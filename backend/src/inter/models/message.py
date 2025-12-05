from typing import Literal, TypedDict

from inter.models.user import User


class TextFragment(TypedDict):
    type: Literal["text"]
    text: str


class EmoteFragment(TypedDict):
    type: Literal["emote"]
    url: str
    name: str


class Message(TypedDict):
    time: str
    message: list["Fragment"]
    user: "User"


type Fragment = TextFragment | EmoteFragment
