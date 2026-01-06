from os import environ
import quart
import httpx

from inter.models.user import Users

app = quart.Quart(__name__, static_folder="../../../frontend/build")
users = Users()

try:
    emotes = {
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
                    "query": """
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
                    """,
                    "variables": {"set": environ["EMOTE_SET"]},
                },
            ).json()["data"]["emoteSets"]["emoteSet"]["emotes"]["items"],
            *httpx.post(
                f"https://7tv.io/v4/gql",
                json={
                    "query": """
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
                },
            ).json()["data"]["emoteSets"]["global"]["emotes"]["items"],
        ]
    }

except httpx.ConnectError:
    emotes = {}

COLOUR_COUNT = 17
