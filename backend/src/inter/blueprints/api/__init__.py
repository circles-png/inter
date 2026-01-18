from http.client import NOT_FOUND
from os import environ
import httpx
import quart
from sqlalchemy import select

from inter.blueprints.api.v1.auth import auth
from inter.blueprints.api.v1.stream import stream
from inter.blueprints.api.v1.user import user
from inter.blueprints.api.v1.user_self import user_self
from inter.models.db.follow import Follow
from inter.models.db.user import User
from inter.common import get_session
from quart import request

api = quart.Blueprint("api", __name__, url_prefix="/api/v1/")


@api.route("/random", methods=["GET"])
async def random():
    async with get_session() as session, session.begin():
        user = await User.choice(session)
    if not user:
        return quart.Response(status=NOT_FOUND)
    return user.username


@api.route("/search/<string:query>", methods=["GET"])
async def search_users(query: str):
    async with get_session() as session, session.begin():
        user = (
            await User.from_session(session)
            if request.cookies.get("session_token")
            else None
        )
        following = (
            [
                *(
                    await session.scalars(
                        select(User)
                        .join(Follow, Follow.followee == User.id)
                        .where(
                            (
                                User.display_name.ilike(f"%{query}%")
                                | User.username.ilike(f"%{query}%")
                            ),
                            (Follow.follower == user.id),
                        )
                        .limit(10)
                    )
                ).all()
            ]
            if user
            else []
        )
        results = await session.scalars(
            select(User)
            .where(
                (
                    User.display_name.ilike(f"%{query}%")
                    | User.username.ilike(f"%{query}%")
                ),
                User.id.not_in([followed.id for followed in following]),
            )
            .limit(10)
        )
        return quart.jsonify(
            [
                group
                for group in [
                    {
                        "name": "Following",
                        "results": [u.username for u in following],
                    },
                    {
                        "name": "Results",
                        "results": [u.username for u in results],
                    },
                ]
                if group["results"]
            ]
        )


CUSTOM_EMOTE_SET_QUERY = """
    query Emotes($set: Id!){
        emoteSets {
            emoteSet(id: $set) {
                emotes {
                    items {
                        name: alias
                        emote {
                            flags {
                                zeroWidth: defaultZeroWidth
                            }
                            images {
                                url
                            }
                        }
                    }
                }
            }
        }
    }
"""
GLOBAL_EMOTE_SET_QUERY = """
    {
        emoteSets {
            global {
                emotes {
                    items {
                        name: alias
                        emote {
                            flags {
                                zeroWidth: defaultZeroWidth
                            }
                            images {
                                url
                            }
                        }
                    }
                }
            }
        }
    }
"""


@api.route("/emotes", methods=["GET"])
async def _():
    return quart.jsonify(
        {
            emote["name"]: (
                next(
                    image["url"]
                    for image in emote["emote"]["images"]
                    if image["url"].endswith("2x.webp")
                ),
                emote["emote"]["flags"]["zeroWidth"],
            )
            for emote in [
                *httpx.post(
                    f"https://7tv.io/v4/gql",
                    json={
                        "query": CUSTOM_EMOTE_SET_QUERY,
                        "variables": {"set": environ["EMOTE_SET"]},
                    },
                ).json()["data"]["emoteSets"]["emoteSet"]["emotes"]["items"],
                *httpx.post(
                    f"https://7tv.io/v4/gql",
                    json={
                        "query": GLOBAL_EMOTE_SET_QUERY,
                    },
                ).json()["data"]["emoteSets"]["global"]["emotes"]["items"],
            ]
        }
    )


api.register_blueprint(stream)
api.register_blueprint(auth)
api.register_blueprint(user)
api.register_blueprint(user_self)
