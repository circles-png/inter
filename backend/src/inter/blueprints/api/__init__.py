"""
Base API blueprint for Inter organising general or miscellaneous endpoints, with sub-blueprints for
authentication, user management, and stream management. The API is versioned at /api/v1/ to allow
for a different system update method and to preserve backwards compatibility.
"""

from http.client import NOT_FOUND
from os import environ
import httpx
import quart
from sqlalchemy import select

from inter.blueprints.api.v1.auth import auth
from inter.blueprints.api.v1.stream import stream, streams
from inter.blueprints.api.v1.user import user
from inter.blueprints.api.v1.user_self import user_self
from inter.blueprints.api.v1.roles import roles
from inter.models.db.follow import Follow
from inter.models.db.user import User
from inter.common import get_session

api = quart.Blueprint("api", __name__, url_prefix="/api/v1/")


@api.route("/random", methods=["GET"])
async def random():
    """
    Get a random username.
    """
    async with get_session() as session, session.begin():
        user = await User.choice(session)
    if not user:
        return quart.Response(status=NOT_FOUND)
    return user.username


@api.route("/search/<string:query>", methods=["GET"])
async def search_users(query: str):
    """
    Search for users with the given query in their username or display name. If the user is
    authenticated, return followed users in a separate group.
    """
    async with get_session() as session, session.begin():
        user = await User.from_session_optional(session)
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


@stream.route("/homepage", methods=["GET"])
async def homepage():
    """
    Get a list of currently live streamers to display on the homepage.
    """
    async with get_session() as session, session.begin():
        return quart.jsonify(
            [
                streamer.username
                for streamer in [
                    await session.get(User, streamer)
                    for streamer, stream in streams.items()
                    if stream.connection
                ]
                if streamer
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
    """
    Get a list of emotes to display in the chat, including URLs and zero-width (overlaying) status.
    """
    try:
        async with httpx.AsyncClient() as client:
            return quart.jsonify(
                {
                    emote["name"]: (
                        next(
                            image["url"].replace(
                                "https://cdn.7tv.app/",
                                "https://em.circles-png.workers.dev/cdn.7tv.app/",
                            )
                            for image in emote["emote"]["images"]
                            if image["url"].endswith("2x.webp")
                        ),
                        emote["emote"]["flags"]["zeroWidth"],
                    )
                    for set in [
                        (
                            await client.post(
                                f"https://em.circles-png.workers.dev/7tv.io/v4/gql",
                                json=body,
                            )
                        ).json()["data"]["emoteSets"][key]["emotes"]["items"]
                        for body, key in [
                            (
                                {
                                    "query": CUSTOM_EMOTE_SET_QUERY,
                                    "variables": {"set": environ["EMOTE_SET"]},
                                },
                                "emoteSet",
                            ),
                            (
                                {
                                    "query": GLOBAL_EMOTE_SET_QUERY,
                                },
                                "global",
                            ),
                        ]
                    ]
                    for emote in set
                }
            )
    except httpx.HTTPError:
        return quart.jsonify({})


api.register_blueprint(stream)
api.register_blueprint(auth)
api.register_blueprint(user)
api.register_blueprint(user_self)
api.register_blueprint(roles)
