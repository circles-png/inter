from hashlib import sha256
from os import environ
from random import choice
import sqlite3
from typing import Callable

from inter.models.stream import Stream
from inter.utils import generate_secure_random_string


class User:
    def __init__(
        self,
        user_id: int,
        username: str,
        display_name: str | None,
        stream_token: str | None,
    ) -> None:
        self.id = user_id
        self.username = username
        self.display_name = display_name
        self.stream_token = stream_token
        self.stream: Stream | None = None
        self.colour: int = 0


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

    def add(self, username: str, display_name: str | None, password: str) -> int:
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
