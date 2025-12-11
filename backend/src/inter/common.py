from os import environ
import quart
import requests

from inter.models.user import Users

app = quart.Quart(__name__, static_folder="../../../frontend/build")
users = Users()

try:
    emotes = {
        emote[
            "name"
        ]: f"http:{emote['data']['host']['url']}/{emote['data']['host']['files'][1]['name']}"
        for emote in [
            *requests.get(
                f"https://7tv.io/v3/emote-sets/{environ["EMOTE_SET"]}"
            ).json()["emotes"],
            *requests.get(f"https://7tv.io/v3/emote-sets/global").json()["emotes"],
        ]
    }

except requests.exceptions.ConnectionError:
    emotes = {}
