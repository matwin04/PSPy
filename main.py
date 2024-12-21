from flask import *
import requests
app = Flask(__name__)
def fetchPlayers():
    url = "https://wiimmfi.de/stats/game/mariokartwii/text"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.text
        players = []
        for line in data.startswith