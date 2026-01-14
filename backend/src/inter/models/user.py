from hashlib import sha256
from http.client import NOT_FOUND, UNAUTHORIZED
from os import environ
from random import choice, randint
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
        colour: int,
        salt: str,
        password_hash: bytes,
        stream_title: str,
        stream_game: str,
        roles: list[int],
    ) -> None:
        self._id = user_id
        self._username = username
        self._display_name = display_name
        self._stream_token = stream_token
        self._colour = colour
        self._salt = salt
        self._password_hash = password_hash
        self.roles: list[int] = roles

        self.stream: Stream = Stream()
        self.stream.title = stream_title
        self.stream.game = stream_game

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
            return abort(NOT_FOUND)
        return user

    @property
    def id(self) -> int:
        return self._id

    @id.setter
    def id(self, id: int) -> None:
        from inter.common import users

        with sqlite3.connect(environ["DATABASE_PATH"]) as db:
            db.cursor().execute(
                "update users set id = ? where id = ?",
                (id, self.id),
            )

        users.reload()

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

    @property
    def stream_token(self) -> str:
        return self._stream_token

    @stream_token.setter
    def stream_token(self, stream_token: str) -> None:
        from inter.common import users

        with sqlite3.connect(environ["DATABASE_PATH"]) as db:
            db.cursor().execute(
                "update users set stream_token = ? where id = ?",
                (stream_token, self.id),
            )

        users.reload()

    @property
    def colour(self) -> int:
        return self._colour

    @colour.setter
    def colour(self, colour: int) -> None:
        from inter.common import users

        with sqlite3.connect(environ["DATABASE_PATH"]) as db:
            db.cursor().execute(
                "update users set colour = ? where id = ?",
                (colour, self.id),
            )

        users.reload()

    @property
    def salt(self) -> str:
        return self._salt

    @salt.setter
    def salt(self, salt: str) -> None:
        from inter.common import users

        with sqlite3.connect(environ["DATABASE_PATH"]) as db:
            db.cursor().execute(
                "update users set salt = ? where id = ?",
                (salt, self.id),
            )

        users.reload()

    @property
    def password_hash(self) -> bytes:
        return self._password_hash

    @password_hash.setter
    def password_hash(self, password_hash: bytes) -> None:
        from inter.common import users

        with sqlite3.connect(environ["DATABASE_PATH"]) as db:
            db.cursor().execute(
                "update users set password_hash = ? where id = ?",
                (password_hash, self.id),
            )

        users.reload()

    @property
    def stream_title(self) -> str:
        return self.stream.title

    @stream_title.setter
    def stream_title(self, title: str) -> None:
        from inter.common import users

        with sqlite3.connect(environ["DATABASE_PATH"]) as db:
            db.cursor().execute(
                "update users set stream_title = ? where id = ?",
                (title, self.id),
            )

        users.reload()

    @property
    def stream_game(self) -> str:
        return self.stream.game

    @stream_game.setter
    def stream_game(self, game: str) -> None:
        from inter.common import users

        with sqlite3.connect(environ["DATABASE_PATH"]) as db:
            db.cursor().execute(
                "update users set stream_game = ? where id = ?",
                (game, self.id),
            )

        users.reload()

    def set_avatar(self, avatar_bytes: bytes | None) -> None:
        from inter.common import users

        with sqlite3.connect(environ["DATABASE_PATH"]) as db:
            db.cursor().execute(
                "update users set avatar = ? where id = ?",
                (avatar_bytes, self.id),
            )

        users.reload()

    def follow(self, user: "User") -> None:
        from inter.common import users

        with sqlite3.connect(environ["DATABASE_PATH"]) as db:
            db.cursor().execute(
                "insert into follow (follower, followee) values (?, ?)",
                (self.id, user.id),
            )

        users.reload()

    def unfollow(self, user: "User") -> None:
        from inter.common import users

        with sqlite3.connect(environ["DATABASE_PATH"]) as db:
            db.cursor().execute(
                "delete from follow where follower = ? and followee = ?",
                (self.id, user.id),
            )

        users.reload()

    def following_count(self) -> int:
        with sqlite3.connect(environ["DATABASE_PATH"]) as db:
            cursor = db.cursor()
            cursor.execute(
                "select count(*) from follow where follower = ?",
                (self.id,),
            )
            (count,) = cursor.fetchone()

        return count

    def followers_count(self) -> int:
        with sqlite3.connect(environ["DATABASE_PATH"]) as db:
            cursor = db.cursor()
            cursor.execute(
                "select count(*) from follow where followee = ?",
                (self.id,),
            )
            (count,) = cursor.fetchone()

        return count

    def following(self) -> list["User"]:
        from inter.common import users

        with sqlite3.connect(environ["DATABASE_PATH"]) as db:
            cursor = db.cursor()
            cursor.execute(
                "select followee from follow where follower = ?",
                (self.id,),
            )
            followee_ids = [followee for followee, in cursor.fetchall()]

        return [user for user in users.users if user.id in followee_ids]

    def followers(self) -> list["User"]:
        from inter.common import users

        with sqlite3.connect(environ["DATABASE_PATH"]) as db:
            cursor = db.cursor()
            cursor.execute(
                "select follower from follow where followee = ?",
                (self.id,),
            )
            follower_ids = [follower for follower, in cursor.fetchall()]

        return [user for user in users.users if user.id in follower_ids]

    def reload(
        self,
        username: str,
        display_name: str,
        stream_token: str,
        colour: int,
        salt: str,
        password_hash: bytes,
        stream_title: str,
        stream_game: str,
        roles: list[int],
    ) -> None:
        self._username = username
        self._display_name = display_name
        self._stream_token = stream_token
        self._colour = colour
        self._salt = salt
        self._password_hash = password_hash
        self.stream.title = stream_title
        self.stream.game = stream_game
        self.roles = roles

    def set_notify(
        self,
        user: "User",
        endpoint: str | None = None,
        p256dh: bytes | None = None,
        auth: bytes | None = None,
    ):
        from inter.common import users

        if all([endpoint, p256dh, auth]):
            with sqlite3.connect(environ["DATABASE_PATH"]) as db:
                db.cursor().execute(
                    "update follow set endpoint = ?, p256dh = ?, auth = ? where follower = ? and followee = ?",
                    (endpoint, p256dh, auth, self.id, user.id),
                )
        else:
            with sqlite3.connect(environ["DATABASE_PATH"]) as db:
                db.cursor().execute(
                    "update follow set endpoint = null, p256dh = null, auth = null where follower = ? and followee = ?",
                    (self.id, user.id),
                )

        users.reload()

    def get_notify(self, user: "User") -> tuple[str, bytes, bytes] | None:
        with sqlite3.connect(environ["DATABASE_PATH"]) as db:
            cursor = db.cursor()
            cursor.execute(
                "select endpoint, p256dh, auth from follow where follower = ? and followee = ?",
                (self.id, user.id),
            )
            result = cursor.fetchone()
        return result if result and all(result) else None

    def get_notified(self) -> list["User"]:
        from inter.common import users

        with sqlite3.connect(environ["DATABASE_PATH"]) as db:
            cursor = db.cursor()
            cursor.execute(
                """
                    select
                        group_concat(users.id, ' ')
                    from
                        follow
                        left join users on follower = users.id
                    where
                            followee = ?
                        and endpoint is not null
                        and p256dh is not null
                        and auth is not null
                """,
                (self.id,),
            )
            result = cursor.fetchone()
            return (
                [
                    user
                    for user in (
                        users.find_by_id(int(user_id)) for user_id in result[0].split()
                    )
                    if user
                ]
                if result and result[0]
                else []
            )


class Users:
    def __init__(self) -> None:
        self.users = []
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
            cursor.execute(
                """
                    select
                        users.id, username, display_name, stream_token, colour, salt, password_hash, stream_title, stream_game,
                        group_concat(roles.id, ' ')
                    from
                        users
                        left join users_roles on users.id = users_roles.user
                        left join roles on users_roles.role = roles.id
                    group by
                        users.id
                    order by
                        users.id
                """
            )
            if self.users:
                users: list[int] = []
                for (
                    id,
                    username,
                    display_name,
                    stream_token,
                    colour,
                    salt,
                    password_hash,
                    stream_title,
                    stream_game,
                    roles,
                ) in cursor.fetchall():
                    roles = [int(role) for role in roles.split(" ")] if roles else []
                    user = self.find_by_id(id)
                    users.append(id)
                    if not user:
                        self.users.append(
                            User(
                                id,
                                username,
                                display_name,
                                stream_token,
                                colour,
                                salt,
                                password_hash,
                                stream_title,
                                stream_game,
                                roles,
                            )
                        )
                        continue
                    user.reload(
                        username,
                        display_name,
                        stream_token,
                        colour,
                        salt,
                        password_hash,
                        stream_title,
                        stream_game,
                        roles,
                    )
                for user in self.users[:]:
                    if user.id not in users:
                        self.users.remove(user)

            else:
                self.users = [
                    User(
                        id,
                        username,
                        display_name,
                        stream_token,
                        colour,
                        salt,
                        password_hash,
                        stream_title,
                        stream_game,
                        [int(role) for role in roles.split(" ")] if roles else [],
                    )
                    for (
                        id,
                        username,
                        display_name,
                        stream_token,
                        colour,
                        salt,
                        password_hash,
                        stream_title,
                        stream_game,
                        roles,
                    ) in cursor.fetchall()
                ]

    def add(self, username: str, display_name: str, password: str) -> int:
        from inter.common import COLOUR_COUNT

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
                    randint(0, COLOUR_COUNT - 1),
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
