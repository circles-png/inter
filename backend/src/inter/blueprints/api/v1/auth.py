"""
Authentication endpoints for the Inter API, including signing up, logging in, and updating user
information.
"""

from hashlib import sha256
from http.client import BAD_REQUEST, CONFLICT, CREATED, OK, UNAUTHORIZED
from os import environ
import re
import quart
from quart import request
from quart.datastructures import FileStorage
from inter.models.db.session import Session
from inter.models.db.user import User
from inter.common import COLOUR_COUNT, get_session
from inter.utils import generate_secure_random_string

auth = quart.Blueprint("auth", __name__, url_prefix="/auth/")


@auth.route("/available/<string:username>", methods=["GET"])
async def available(username: str):
    """
    Check if a user with the given username exists.
    """
    async with get_session() as session, session.begin():
        return quart.Response(
            status=OK if await User.available(session, username) else CONFLICT
        )


@auth.route("/signup", methods=["POST"])
async def signup():
    """
    Create a new user with the given username and password.
    """
    data = await request.get_json()
    username: str = data.get("username")
    password: str = data.get("password")
    reenter: str = data.get("reenter")
    if not username or not password or not reenter:
        return quart.Response("Enter a username and password.", status=BAD_REQUEST)
    if re.match("^[a-z0-9_]*$", username) is None:
        return quart.Response(
            "Choose a username with only lowercase letters, numbers, and underscores.",
            status=BAD_REQUEST,
        )
    if len(username) > 32:
        return quart.Response(
            "Choose a username with at most 32 characters.",
            status=BAD_REQUEST,
        )
    if len(password) < 8:
        return quart.Response(
            "Choose a password with at least 8 characters.", status=BAD_REQUEST
        )
    if password != reenter:
        return quart.Response("Ensure passwords match.", status=BAD_REQUEST)
    async with get_session() as sql_session, sql_session.begin():
        if not await User.available(sql_session, username):
            return quart.Response(f"'{username}' is not available.", status=CONFLICT)
        user = await User.add(sql_session, username, "", password)
        _, token = await Session.create(user.id, sql_session)
    response = quart.Response(status=CREATED)
    response.set_cookie(
        "session_token",
        token,
        max_age=86400,
        secure=bool(environ.get("PROD")),
        samesite="Lax",
    )
    return response


@auth.route("/user", methods=["GET"])
async def user():
    """
    Get the currently authenticated user's information.
    """
    async with get_session() as sql_session, sql_session.begin():
        user = await User.from_session(sql_session)
        return quart.jsonify(
            {
                "username": user.username,
                "displayName": user.display_name,
                "colour": user.colour,
                "streamToken": user.stream_token,
            }
        )


@auth.route("/login", methods=["POST"])
async def login():
    """
    Authenticate a user with the given username and password.
    """
    async with get_session() as sql_session, sql_session.begin():
        data = await request.get_json()
        username = data.get("username")
        password = data.get("password")
        if not username or not password:
            return quart.Response("Enter a username and password.", status=BAD_REQUEST)
        user = await User.find_by_username(sql_session, username)
        if not user:
            return quart.Response("Invalid username or password.", status=UNAUTHORIZED)

        if user.password_hash != sha256((password + user.salt).encode()).digest():
            return quart.Response("Invalid username or password.", status=UNAUTHORIZED)
        _, token = await Session.create(user.id, sql_session)
        response = quart.Response(status=OK)
        response.set_cookie(
            "session_token",
            token,
            max_age=86400,
            secure=bool(environ.get("PROD")),
            samesite="Lax",
        )
        return response


@auth.route("/update", methods=["POST"])
async def update():
    """
    Update the currently authenticated user's username, display name, and colour.
    """
    async with get_session() as sql_session, sql_session.begin():
        user = await User.from_session(sql_session)
        data = await request.get_json()
        username: str | None = data.get("username")
        if username and username != user.username:
            if not await User.available(sql_session, username):
                return quart.Response(
                    f"'{username}' is not available.", status=CONFLICT
                )
            if re.match("^[a-z0-9_]*$", username) is None:
                return quart.Response(
                    "Choose a username with only lowercase letters, numbers, and underscores.",
                    status=BAD_REQUEST,
                )
            if len(username) > 32:
                return quart.Response(
                    "Choose a username with at most 32 characters.",
                    status=BAD_REQUEST,
                )
            user.username = username

        display_name: str | None = data.get("displayName")
        if display_name is not None and display_name != user.display_name:
            if len(display_name.encode()) > 32:
                return quart.Response(
                    "Choose a shorter display name.",
                    status=BAD_REQUEST,
                )
            user.display_name = display_name

        colour = data.get("colour")
        if colour is not None and colour != user.colour:
            if not isinstance(colour, int) or not (0 <= colour < COLOUR_COUNT):
                return quart.Response("Choose a valid colour.", status=BAD_REQUEST)
            user.colour = colour

        return quart.Response(status=OK)


@auth.route("/update/stream-token", methods=["POST"])
async def update_stream_token():
    """
    Regenerate the currently authenticated user's stream token, which is used to authenticate the user for streaming endpoints.
    """
    async with get_session() as sql_session, sql_session.begin():
        user = await User.from_session(sql_session)
        user.stream_token = generate_secure_random_string()
        return quart.Response(status=OK)


@auth.route("/update/avatar", methods=["POST"])
async def update_avatar():
    """
    Update the currently authenticated user's avatar.
    """
    async with get_session() as sql_session, sql_session.begin():
        user = await User.from_session(sql_session)
        form: MultiDict[str, FileStorage] = await request.files  # type: ignore
        avatar = form.get("avatar")  # type: ignore
        if avatar is None:
            user.avatar = None
            return quart.Response(status=OK)
        if not isinstance(avatar, FileStorage):
            return quart.Response("Upload a profile picture.", status=BAD_REQUEST)
        avatar = avatar.stream.read()
        user.avatar = avatar
        return quart.Response(status=OK)


@auth.route("/update/password", methods=["POST"])
async def update_password():
    """
    Update the currently authenticated user's password.
    """
    async with get_session() as sql_session, sql_session.begin():
        user = await User.from_session(sql_session)
        data = await request.get_json()

        current = data.get("currentPassword")
        new = data.get("newPassword")
        reenter = data.get("reenterPassword")

        if not current or not new or not reenter:
            return quart.Response("Fill in all password fields.", status=BAD_REQUEST)
        if new != reenter:
            return quart.Response("Ensure new passwords match.", status=BAD_REQUEST)
        if len(new) < 8:
            return quart.Response(
                "Choose a new password with at least 8 characters.", status=BAD_REQUEST
            )
        if sha256((current + user.salt).encode()).digest() != user.password_hash:
            return quart.Response(
                "Ensure current password is correct.", status=UNAUTHORIZED
            )

        salt = generate_secure_random_string()
        user.salt = salt
        user.password_hash = sha256((new + salt).encode()).digest()

        return quart.Response(status=OK)
