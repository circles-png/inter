from hashlib import sha256
from http.client import BAD_REQUEST, CONFLICT, CREATED, OK, UNAUTHORIZED
from os import environ
import re
import sqlite3
import quart
from quart import request
from quart.datastructures import FileStorage
from inter.models.session import Session
from inter.models.user import User
from inter.common import COLOUR_COUNT, users
from inter.utils import generate_secure_random_string

auth = quart.Blueprint("auth", __name__, url_prefix="/auth/")


@auth.route("/available/<string:username>", methods=["GET"])
async def available(username: str):
    if users.available(username):
        return quart.Response(status=OK)
    else:
        return quart.Response(status=CONFLICT)


@auth.route("/signup", methods=["POST"])
async def signup():
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
    if not users.available(username):
        return quart.Response(f"'{username}' is not available.", status=CONFLICT)
    user_id = users.add(username, "", password)
    session = Session(user_id)
    response = quart.Response(status=CREATED)
    response.set_cookie(
        "session_token", session.token, max_age=86400, secure=True, samesite="Lax"
    )
    return response


@auth.route("/user", methods=["GET"])
async def user():
    user = User.from_session()
    return quart.jsonify(
        {
            "username": user.username,
            "displayName": user.display_name,
            "colour": user.colour,
            "streamToken": user.stream_token,
            "roles": user.roles,
        }
    )


@auth.route("/login", methods=["POST"])
async def login():
    data = await request.get_json()
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return quart.Response("Enter a username and password.", status=BAD_REQUEST)
    user = users.find_by_username(username)
    if not user:
        return quart.Response("Invalid username or password.", status=UNAUTHORIZED)
    with sqlite3.connect(environ["DATABASE_PATH"]) as db:
        cursor = db.cursor()
        cursor.execute(
            "select password_hash, salt from users where id = ?",
            (user.id,),
        )
        password_hash, salt = cursor.fetchone()
    if password_hash != sha256((password + salt).encode()).digest():
        return quart.Response("Invalid username or password.", status=UNAUTHORIZED)
    session = Session(user.id)
    response = quart.Response(status=OK)
    response.set_cookie(
        "session_token", session.token, max_age=86400, secure=True, samesite="Lax"
    )
    return response


@auth.route("/update", methods=["POST"])
async def update():
    user = User.from_session()
    data = await request.get_json()
    username: str | None = data.get("username")
    if username and username != user.username:
        if not users.available(username):
            return quart.Response(f"'{username}' is not available.", status=CONFLICT)
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
            return quart.Response(
                "Choose a valid colour.", status=BAD_REQUEST
            )
        user.colour = colour

    return quart.Response(status=OK)

@auth.route("/update/stream-token", methods=["POST"])
async def update_stream_token():
    user = User.from_session()
    user.stream_token = generate_secure_random_string()
    return quart.Response(status=OK)

@auth.route("/update/avatar", methods=["POST"])
async def update_avatar():
    user = User.from_session()  # type: ignore
    form: MultiDict[str, FileStorage] = await request.files  # type: ignore
    avatar = form.get("avatar")  # type: ignore
    if avatar is None:
        user.set_avatar(None)
        return quart.Response(status=OK)
    if not isinstance(avatar, FileStorage):
        return quart.Response("Upload a profile picture.", status=BAD_REQUEST)
    avatar = avatar.stream.read()
    user.set_avatar(avatar)
    return quart.Response(status=OK)


@auth.route("/update/password", methods=["POST"])
async def update_password():
    user = User.from_session()
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
