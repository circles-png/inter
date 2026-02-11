"""
Endpoints for managing and querying the currently authenticated user, including their followers and
following, and updating their stream information.
"""

from http.client import OK
from typing import Any
import quart

from inter.models.db.user import User
from inter.common import get_session


user_self = quart.Blueprint("self", __name__, url_prefix="/self")


@user_self.route("/followers", methods=["GET"])
async def self_followers():
    """
    Get the list of followers for the currently authenticated user.
    """
    async with get_session() as session, session.begin():
        user = await User.from_session(session)
        return quart.jsonify(
            [
                {"username": user.username, "displayName": user.display_name}
                for user in await user.followers(session)
            ]
        )


@user_self.route("/following", methods=["GET"])
async def self_following():
    """
    Get the list of users that the currently authenticated user is following.
    """
    async with get_session() as session, session.begin():
        user = await User.from_session(session)
        return quart.jsonify(
            [
                {"username": user.username, "displayName": user.display_name}
                for user in await user.following(session)
            ]
        )


@user_self.route("/stream/update", methods=["POST"])
async def update_stream():
    """
    Update the currently authenticated user's stream information.
    """
    async with get_session() as session, session.begin():
        user = await User.from_session(session)
        data: dict[str, Any] = await quart.request.get_json()
        title = data.get("title")
        if title:
            user.stream_title = title
        game = data.get("game")
        if game:
            user.stream_game = game
        return quart.Response(status=OK)
