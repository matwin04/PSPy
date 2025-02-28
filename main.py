import os
import sqlite3
import socket
import subprocess
from bottle import Bottle, run, request, static_file, template, redirect

# Server Config
app = Bottle()
DATABASE = 'PSPyTube.db'
UPLOAD_FOLDER = 'static/videos/'
PSP_RES = "480:272"

# Get IP for PSP connection
hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)


# Initialize Database
def connectDB():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def initDB():
    if not os.path.exists(DATABASE):
        with sqlite3.connect(DATABASE) as conn:
            with open('createdb.sql', 'r') as f:
                conn.executescript(f.read())
        print("Database Initialized")
    else:
        print("Database Already Exists")


# Home Page - List Uploaded Videos
@app.route('/')
def index():
    conn = connectDB()
    videos = conn.execute("SELECT * FROM videos ORDER BY upload_date DESC").fetchall()
    conn.close()
    return template('./pages/index.html', videos=videos, ip=IPAddr)


# Upload and Convert Video
@app.route('/upload', method='POST')
def upload():
    video = request.files.get('video')
    if video:
        filename = video.filename
        save_path = os.path.join(UPLOAD_FOLDER, filename)

        # Save the uploaded video
        video.save(save_path)

        # Convert to PSP format
        psp_filename = f"psp_{filename}"
        output_path = os.path.join(UPLOAD_FOLDER, psp_filename)
        ffmpeg_command = [
            "ffmpeg", "-i", save_path, "-vf", f"scale={PSP_RES}",
            "-c:v", "libx264", "-preset", "slow", "-crf", "23", "-c:a", "aac", output_path
        ]
        subprocess.run(ffmpeg_command)

        # Store in database
        conn = connectDB()
        conn.execute("INSERT INTO videos (filename, original_filename) VALUES (?, ?)", (psp_filename, filename))
        conn.commit()
        conn.close()

        return redirect('/')

    return "Upload Failed"


# Serve Videos for PSP Download
@app.route('/videos/<filename>')
def serve_video(filename):
    return static_file(filename, root=UPLOAD_FOLDER, download=filename)


# Run App
if __name__ == '__main__':
    initDB()
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    run(app, host='0.0.0.0', port=8181, debug=True)