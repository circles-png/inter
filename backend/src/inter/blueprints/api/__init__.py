from http.client import NOT_FOUND
from os import environ
import httpx
import quart

from inter.blueprints.api.v1.auth import auth
from inter.blueprints.api.v1.stream import stream
from inter.blueprints.api.v1.user import user
from inter.blueprints.api.v1.user_self import user_self
from inter.models.db.user import User
from inter.common import get_session

api = quart.Blueprint("api", __name__, url_prefix="/api/v1/")


@api.route("/random", methods=["GET"])
async def random():
    async with get_session() as session, session.begin():
        user = await User.choice(session)
    if not user:
        return quart.Response(status=NOT_FOUND)
    return user.username


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
