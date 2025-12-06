from hashlib import sha256
from http.client import GONE, UNAUTHORIZED
from os import environ
from random import choice
import sqlite3
from typing import Callable

from quart import abort, request

from inter.models.session import Session
from inter.models.stream import Stream
from inter.utils import generate_secure_random_string


class User:
    def __init__(
        self,
        user_id: int,
        username: str,
        display_name: str,
        stream_token: str,
    ) -> None:
        self.id = user_id
        self._username = username
        self._display_name = display_name
        self.stream_token = stream_token
        self.stream: Stream | None = None
        self.colour: int = 0

    @staticmethod
    def from_session() -> "User":
        from inter.common import users

        token = request.cookies.get("session_token")
        if not token:
            return abort(UNAUTHORIZED)
        session = Session.validate_token(token)
        if not session:
            return abort(UNAUTHORIZED)
        user = users.find_by_id(session.user)
        if not user:
            return abort(GONE)
        return user

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, username: str) -> None:
        from inter.common import users

        with sqlite3.connect(environ["DATABASE_PATH"]) as db:
            db.cursor().execute(
                "update users set username = ? where id = ?",
                (username, self.id),
            )

        users.reload()

    @property
    def display_name(self) -> str:
        return self._display_name

    @display_name.setter
    def display_name(self, display_name: str) -> None:
        from inter.common import users

        with sqlite3.connect(environ["DATABASE_PATH"]) as db:
            db.cursor().execute(
                "update users set display_name = ? where id = ?",
                (display_name, self.id),
            )

        users.reload()


class Users:
    def __init__(self) -> None:
        self.reload()

    def find_by_token(self, token: str) -> User | None:
        return self.find(lambda user: user.stream_token == token)

    def find_by_id(self, user_id: int) -> User | None:
        return self.find(lambda user: user.id == user_id)

    def find_by_username(self, username: str) -> User | None:
        return self.find(lambda user: user.username == username)

    def find(self, condition: Callable[[User], bool]) -> User | None:
        return next((user for user in self.users if condition(user)), None)

    def choice(self) -> User:
        return choice(self.users)

    def available(self, username: str) -> bool:
        return self.find_by_username(username) is None

    def reload(self) -> None:
        with sqlite3.connect(environ["DATABASE_PATH"]) as db:
            cursor = db.cursor()
            cursor.execute("select id, username, stream_token, display_name from users")
            self.users = [
                User(user_id, username, display_name, stream_token)
                for user_id, username, stream_token, display_name in cursor.fetchall()
            ]

    def add(self, username: str, display_name: str, password: str) -> int:
        salt = generate_secure_random_string()
        with sqlite3.connect(environ["DATABASE_PATH"]) as db:
            cursor = db.cursor()
            cursor.execute(
                "insert into users (username, display_name, stream_token, password_hash, salt, colour) values (?, ?, ?, ?, ?, ?) returning id",
                (
                    username,
                    display_name,
                    generate_secure_random_string(),
                    sha256((password + salt).encode()).digest(),
                    salt,
                    1,
                ),
            )
            (user_id,) = cursor.fetchone()
        self.reload()
        return user_id

    def avatar(self, user: User) -> bytes | None:
        with sqlite3.connect(environ["DATABASE_PATH"]) as db:
            cursor = db.cursor()
            cursor.execute(
                "select avatar from users where id = ?",
                (user.id,),
            )
            (avatar,) = cursor.fetchone()
        return avatar
