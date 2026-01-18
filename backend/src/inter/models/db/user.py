from hashlib import sha256
from http.client import NOT_FOUND, UNAUTHORIZED
from random import randint
from typing import Any, Sequence

from quart import abort, request
from quart_sqlalchemy import AsyncSession
from sqlalchemy import Connection, func, select
from sqlalchemy.orm import Mapper, mapped_column, Mapped
from sqlalchemy.event import listens_for

from inter.models.stream import Stream
from inter.utils import generate_secure_random_string
from inter.common import db


class User(db.Model):
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

    async def follow(self, user: "User", session: AsyncSession[Any]) -> None:
        from inter.models.db.follow import Follow

        session.add(Follow(follower=self.id, followee=user.id))
        await session.flush()

    async def unfollow(self, user: "User", session: AsyncSession[Any]) -> None:
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
        from inter.models.db.follow import Follow

        return await session.scalar(
            select(func.count(), Follow).where(Follow.follower == self.id)
        )

    async def followers_count(self, session: AsyncSession[Any]) -> int:
        from inter.models.db.follow import Follow

        return await session.scalar(
            select(func.count(), Follow).where(Follow.followee == self.id)
        )

    async def following(self, session: AsyncSession[Any]) -> Sequence["User"]:
        from inter.models.db.follow import Follow

        return (
            await session.scalars(
                select(User)
                .join(Follow, Follow.followee == User.id)
                .where(Follow.follower == self.id)
            )
        ).all()

    async def followers(self, session: AsyncSession[Any]) -> Sequence["User"]:
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
        from inter.models.db.follow import Follow

        follow = await session.get(Follow, {"follower": self.id, "followee": user.id})
        if not follow:
            return None
        if follow.endpoint is None or follow.p256dh is None or follow.auth is None:
            return None
        return (follow.endpoint, follow.p256dh, follow.auth)

    async def get_notified(self, session: AsyncSession[Any]) -> Sequence["User"]:
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
        return (
            await session.scalars(select(User).where(User.stream_token == token))
        ).one_or_none()

    @staticmethod
    async def find_by_id(session: AsyncSession[Any], user_id: int) -> "User | None":
        return (
            await session.scalars(select(User).where(User.id == user_id))
        ).one_or_none()

    @staticmethod
    async def find_by_username(
        session: AsyncSession[Any], username: str
    ) -> "User | None":
        return (
            await session.scalars(select(User).where(User.username == username))
        ).one_or_none()

    @staticmethod
    async def choice(session: AsyncSession[Any]) -> "User | None":
        return (
            await session.scalars(select(User).order_by(func.random()).limit(1))
        ).one_or_none()

    @staticmethod
    async def available(session: AsyncSession[Any], username: str) -> bool:
        return await User.find_by_username(session, username) is None

    @staticmethod
    async def add(
        session: AsyncSession[Any], username: str, display_name: str, password: str
    ) -> "User":
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

    async def roles(self, session: AsyncSession[Any]) -> Sequence[str]:
        from inter.models.db.role import Role, UsersRoles

        return (
            await session.scalars(
                select(Role.name)
                .join(UsersRoles, UsersRoles.role == Role.id)
                .where(UsersRoles.user == self.id)
            )
        ).all()


@listens_for(User, "after_insert")
def create_stream(_mapper: Mapper[Any], _connection: Connection, target: User) -> None:
    from inter.blueprints.api.v1.stream import streams

    streams[target.id] = Stream()


@listens_for(User, "after_delete")
def delete_stream(_mapper: Mapper[Any], _connection: Connection, target: User) -> None:
    from inter.blueprints.api.v1.stream import streams

    del streams[target.id]
