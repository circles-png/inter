from hashlib import sha256
from http.client import NOT_FOUND, UNAUTHORIZED
from random import randint
from typing import Any, Sequence
from datetime import datetime

from quart import abort, request
from quart_sqlalchemy import AsyncSession
from sqlalchemy import Connection, delete, func, select
from sqlalchemy.orm import Mapper, mapped_column, Mapped
from sqlalchemy.event import listens_for
from sqlalchemy.dialects.sqlite import insert

from inter.models.stream import Stream
from inter.utils import generate_secure_random_string
from inter.common import db


class User(db.Model):
    """
    Model representing users on Inter.
    """

    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    stream_token: Mapped[str] = mapped_column(nullable=False)
    password_hash: Mapped[bytes] = mapped_column()
    salt: Mapped[str] = mapped_column(nullable=False)
    colour: Mapped[int] = mapped_column(nullable=False)
    avatar: Mapped[bytes | None] = mapped_column()
    display_name: Mapped[str] = mapped_column(nullable=False)
    stream_title: Mapped[str] = mapped_column(nullable=False, default="")
    stream_game: Mapped[str] = mapped_column(nullable=False, default="")

    @staticmethod
    async def from_session(sql_session: AsyncSession[Any]) -> "User":
        """
        Get the user corresponding to the session token in the request cookies.
        """
        from inter.models.db.session import Session

        token = request.cookies.get("session_token")
        if not token:
            return abort(UNAUTHORIZED)
        session = await Session.validate_token(token, sql_session)
        if not session:
            return abort(UNAUTHORIZED)
        user = await User.find_by_id(sql_session, session.user)
        if not user:
            return abort(NOT_FOUND)
        return user

    @staticmethod
    async def from_session_optional(sql_session: AsyncSession[Any]) -> "User | None":
        """
        Same as `from_session`, but returns `None` instead of aborting.
        """
        from inter.models.db.session import Session

        token = request.cookies.get("session_token")
        if not token:
            return None
        session = await Session.validate_token(token, sql_session)
        if not session:
            return None
        user = await User.find_by_id(sql_session, session.user)
        if not user:
            return None
        return user

    async def follow(self, user: "User", session: AsyncSession[Any]) -> None:
        """
        Follow the given user.
        """
        from inter.models.db.follow import Follow

        session.add(Follow(follower=self.id, followee=user.id))
        await session.flush()

    async def unfollow(self, user: "User", session: AsyncSession[Any]) -> None:
        """
        Unfollow the given user.
        """
        from inter.models.db.follow import Follow

        follow = (
            await session.scalars(
                select(Follow).where(
                    Follow.follower == self.id, Follow.followee == user.id
                )
            )
        ).one_or_none()
        if not follow:
            return
        await session.delete(follow)
        await session.flush()

    async def following_count(self, session: AsyncSession[Any]) -> int:
        """
        Get the number of users this user is following.
        """
        from inter.models.db.follow import Follow

        return await session.scalar(
            select(func.count(), Follow).where(Follow.follower == self.id)
        )

    async def followers_count(self, session: AsyncSession[Any]) -> int:
        """
        Get the number of users following this user.
        """
        from inter.models.db.follow import Follow

        return await session.scalar(
            select(func.count(), Follow).where(Follow.followee == self.id)
        )

    async def following(self, session: AsyncSession[Any]) -> Sequence["User"]:
        """
        Get the list of users this user is following.
        """
        from inter.models.db.follow import Follow

        return (
            await session.scalars(
                select(User)
                .join(Follow, Follow.followee == User.id)
                .where(Follow.follower == self.id)
            )
        ).all()

    async def followers(self, session: AsyncSession[Any]) -> Sequence["User"]:
        """
        Get the list of users following this user.
        """
        from inter.models.db.follow import Follow

        return (
            await session.scalars(
                select(User)
                .join(Follow, Follow.follower == User.id)
                .where(Follow.followee == self.id)
            )
        ).all()

    async def set_notify(
        self,
        user: "User",
        session: AsyncSession[Any],
        endpoint: str | None = None,
        p256dh: bytes | None = None,
        auth: bytes | None = None,
    ):
        """
        Set the notification settings for the given user.
        """
        from inter.models.db.follow import Follow

        endpoint, p256dh, auth = (
            (endpoint, p256dh, auth)
            if all([endpoint, p256dh, auth])
            else (None, None, None)
        )
        follow = await session.get(Follow, {"follower": self.id, "followee": user.id})
        if not follow:
            return
        follow.endpoint = endpoint
        follow.p256dh = p256dh
        follow.auth = auth
        await session.flush()

    async def get_notify(
        self, user: "User", session: AsyncSession[Any]
    ) -> tuple[str, bytes, bytes] | None:
        """
        Get the notification settings for the given user.
        """
        from inter.models.db.follow import Follow

        follow = await session.get(Follow, {"follower": self.id, "followee": user.id})
        if not follow:
            return None
        if follow.endpoint is None or follow.p256dh is None or follow.auth is None:
            return None
        return (follow.endpoint, follow.p256dh, follow.auth)

    async def get_notified(self, session: AsyncSession[Any]) -> Sequence["User"]:
        """
        Get the list of users that should be notified when this user goes live.
        """
        from inter.models.db.follow import Follow

        return (
            await session.scalars(
                select(User)
                .join(Follow, Follow.follower == User.id)
                .where(
                    Follow.followee == self.id,
                    Follow.endpoint != None,
                    Follow.p256dh != None,
                    Follow.auth != None,
                )
            )
        ).all()

    @staticmethod
    async def find_by_token(session: AsyncSession[Any], token: str) -> "User | None":
        """
        Find a user by their stream token.
        """
        return (
            await session.scalars(select(User).where(User.stream_token == token))
        ).one_or_none()

    @staticmethod
    async def find_by_id(session: AsyncSession[Any], user_id: int) -> "User | None":
        """
        Find a user by their ID.
        """
        return (
            await session.scalars(select(User).where(User.id == user_id))
        ).one_or_none()

    @staticmethod
    async def find_by_username(
        session: AsyncSession[Any], username: str
    ) -> "User | None":
        """
        Find a user by their username.
        """
        return (
            await session.scalars(select(User).where(User.username == username))
        ).one_or_none()

    @staticmethod
    async def choice(session: AsyncSession[Any]) -> "User | None":
        """
        Get a random user.
        """
        return (
            await session.scalars(select(User).order_by(func.random()).limit(1))
        ).one_or_none()

    @staticmethod
    async def available(session: AsyncSession[Any], username: str) -> bool:
        """
        Check if a username is available.
        """
        return await User.find_by_username(session, username) is None

    @staticmethod
    async def add(
        session: AsyncSession[Any], username: str, display_name: str, password: str
    ) -> "User":
        """
        Add a new user with the given username, display name, and password.
        """
        from inter.common import COLOUR_COUNT

        salt = generate_secure_random_string()
        user = User(
            username=username,
            display_name=display_name,
            stream_token=generate_secure_random_string(),
            password_hash=sha256((password + salt).encode()).digest(),
            salt=salt,
            colour=randint(0, COLOUR_COUNT - 1),
        )
        session.add(user)
        await session.flush()
        return user

    async def unmoderate(self, target: "User", session: AsyncSession[Any]) -> None:
        """
        Remove any moderation relationship between this user and the target user.
        """
        from inter.models.db.moderation import Moderation

        await session.execute(
            delete(Moderation).where(
                Moderation.subject == self.id, Moderation.target == target.id
            )
        )
        await session.flush()

    async def moderate(
        self, target: "User", duration: int | None, session: AsyncSession[Any]
    ) -> None:
        """
        Moderate the target user for the given duration (in seconds). If duration is `None`, ban the user indefinitely.
        """
        from inter.models.db.moderation import Moderation

        statement = insert(Moderation).values(
            subject=self.id,
            target=target.id,
            duration=duration,
            start=int(datetime.now().timestamp()),
        )
        await session.execute(
            statement.on_conflict_do_update(
                set_=dict(
                    duration=statement.excluded.duration, start=statement.excluded.start
                )
            )
        )


@listens_for(User, "after_insert")
def create_stream(_mapper: Mapper[Any], _connection: Connection, target: User) -> None:
    """
    After adding a new user, create a stream for them in the `streams` dictionary.
    """
    from inter.blueprints.api.v1.stream import streams

    streams[target.id] = Stream()


@listens_for(User, "after_delete")
def delete_stream(_mapper: Mapper[Any], _connection: Connection, target: User) -> None:
    """
    After deleting a user, remove their stream from the `streams` dictionary.
    """
    from inter.blueprints.api.v1.stream import streams

    del streams[target.id]
