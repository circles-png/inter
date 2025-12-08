from hashlib import sha256
from http.client import BAD_REQUEST, CONFLICT, CREATED, OK, UNAUTHORIZED
from os import environ
import sqlite3
import quart
from quart import request
from inter.models.session import Session
from inter.models.user import User
from inter.common import users
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
            "avatarUrl": f"{request.host_url}api/v1/avatar/{user.username}",
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
    username = data.get("username")
    if username and username != user.username:
        if not users.available(username):
            return quart.Response(f"'{username}' is not available.", status=CONFLICT)
        user.username = username

    display_name = data.get("displayName")
    if display_name is not None and display_name != user.display_name:
        user.display_name = display_name

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
        return quart.Response("Ensure current password is correct.", status=UNAUTHORIZED)

    user.salt = generate_secure_random_string()
    user.password_hash = sha256((new + user.salt).encode()).digest()

    return quart.Response(status=OK)
