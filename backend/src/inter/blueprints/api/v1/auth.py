from hashlib import sha256
from http.client import BAD_REQUEST, CONFLICT, CREATED, GONE, OK, UNAUTHORIZED
from os import environ
import sqlite3
import quart
from quart import request, abort
from inter.common import users
from inter.models.session import Session

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
    if password != reenter:
        return quart.Response("Ensure passwords match.", status=BAD_REQUEST)
    if not users.available(username):
        return quart.Response(f"'{username}' is not available.", status=CONFLICT)
    user_id = users.add(username, None, password)
    session = Session(user_id)
    response = quart.Response(status=CREATED)
    response.set_cookie(
        "session_token", session.token, max_age=86400, secure=True, samesite="Lax"
    )
    return response


@auth.route("/user", methods=["GET"])
async def user():
    token = request.cookies.get("session_token")
    if not token:
        return abort(UNAUTHORIZED)
    session = Session.validate_token(token)
    if not session:
        return abort(UNAUTHORIZED)
    user = users.find_by_id(session.user)
    if not user:
        return abort(GONE)
    return quart.jsonify(
        {
            "username": user.username,
            "displayName": user.display_name,
            "colour": user.colour,
            "avatarUrl": f"{request.host_url}api/v1/avatar/{user.username}",
        }
    )


@auth.route("/login", methods=["POST"])
async def login():
    data = await request.get_json()
    username: str = data.get("username")
    password: str = data.get("password")
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
