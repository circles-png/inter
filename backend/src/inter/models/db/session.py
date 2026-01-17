from datetime import datetime
from hashlib import sha256
from math import floor
import secrets
from typing import Any

from quart_sqlalchemy import AsyncSession
from sqlalchemy import ForeignKey
from inter.common import db
from inter.utils import generate_secure_random_string
from sqlalchemy.orm import mapped_column, Mapped


class Session(db.Model):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(primary_key=True, nullable=False)
    secret_hash: Mapped[bytes] = mapped_column(nullable=False)
    created_at: Mapped[int] = mapped_column(nullable=False)
    user: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    @staticmethod
    async def create(
        user_id: int, sql_session: AsyncSession[Any]
    ) -> tuple["Session", str]:
        id = generate_secure_random_string()
        secret = generate_secure_random_string()
        token = f"{id}.{secret}"
        new_session = Session(
            id=id,
            secret_hash=sha256(secret.encode()).digest(),
            created_at=floor(datetime.now().timestamp()),
            user=user_id,
        )
        sql_session.add(new_session)
        await sql_session.flush()
        return new_session, token

    @staticmethod
    async def validate_token(
        token: str, sql_session: AsyncSession[Any]
    ) -> "Session | None":
        parts = token.split(".")
        if len(parts) != 2:
            return None
        session_id, secret = parts
        session = await Session.get(session_id, sql_session)
        if not session:
            return None
        secret_hash = sha256(secret.encode()).digest()
        if not secrets.compare_digest(secret_hash, session.secret_hash):
            return None
        return session

    @staticmethod
    async def get(session_id: str, sql_session: AsyncSession[Any]) -> "Session | None":
        session = await sql_session.get(Session, session_id)
        if not session:
            return None
        created_at = datetime.fromtimestamp(session.created_at)
        SECONDS_IN_A_DAY = 60 * 60 * 24
        if (datetime.now() - created_at).total_seconds() > SECONDS_IN_A_DAY:
            await sql_session.delete(session)
            return None
        return session

    @staticmethod
    async def delete(session_id: str, sql_session: AsyncSession[Any]) -> None:
        await sql_session.delete(await sql_session.get(Session, session_id))
