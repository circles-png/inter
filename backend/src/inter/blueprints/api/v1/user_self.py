from http.client import OK
from typing import Any
import quart

from inter.models.user import User


user_self = quart.Blueprint("self", __name__, url_prefix="/self")


@user_self.route("/followers", methods=["GET"])
async def self_followers():
    user = User.from_session()
    return quart.jsonify(
        [
            {"username": user.username, "displayName": user.display_name}
            for user in user.followers()
        ]
    )


@user_self.route("/following", methods=["GET"])
async def self_following():
    user = User.from_session()
    return quart.jsonify(
        [
            {"username": user.username, "displayName": user.display_name}
            for user in user.following()
        ]
    )


@user_self.route("/stream/update", methods=["POST"])
async def update_stream():
    user = User.from_session()
    data: dict[str, Any] = await quart.request.get_json()
    title = data.get("title")
    if title:
        user.stream_title = title
    game = data.get("game")
    if game:
        user.stream_game = game
    return quart.Response(status=OK)
