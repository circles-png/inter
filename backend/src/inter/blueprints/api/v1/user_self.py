"""
Endpoints for managing and querying the currently authenticated user, including their followers and
following, and updating their stream information.
"""

from datetime import datetime
from http.client import OK
from typing import Any
import quart
from sqlalchemy import select, update

from inter.models.db.moderation import Moderation
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


@user_self.route("/stream/moderation", methods=["GET"])
async def get_moderation():
    """
    Get the currently authenticated user's stream moderation information.
    This includes the list of bans and timeouts, and the content filtering settings.
    """
    async with get_session() as session, session.begin():
        user = await User.from_session(session)

        return quart.jsonify(
            {
                "moderation": [
                    {
                        "duration": moderation.duration,
                        "start": moderation.start,
                        "target": target.username,
                    }
                    async for (moderation, target) in (
                        (moderation, await session.get(User, moderation.target))
                        for moderation in (
                            await session.execute(
                                select(Moderation)
                                .where(Moderation.subject == user.id)
                                .where(
                                    Moderation.start + Moderation.duration
                                    > datetime.now().timestamp()
                                )
                                .order_by(Moderation.start.desc())
                            )
                        )
                        .scalars()
                        .all()
                    )
                    if target
                ],
                "words": user.stream_moderation_words,
            }
        )


@user_self.route("/stream/moderation/words", methods=["POST"])
async def update_moderation_words():
    """
    Update the currently authenticated user's stream moderation words.
    """
    async with get_session() as session, session.begin():
        user = await User.from_session(session)
        words = await quart.request.get_data(as_text=True)
        await session.execute(
            update(User).where(User.id == user.id).values(stream_moderation_words=words)
        )
        return quart.Response(status=OK)
