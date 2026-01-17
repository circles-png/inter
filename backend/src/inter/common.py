import asyncio
from os import environ
from typing import Any, Callable
import quart
from quart_sqlalchemy.framework import QuartSQLAlchemy
from quart_sqlalchemy import (
    AsyncBindConfig,
    AsyncSession,
    EngineConfig,
    SQLAlchemyConfig,
)
from sqlalchemy import select


app = quart.Quart(__name__, static_folder="../../../frontend/build")
db = QuartSQLAlchemy(
    config=SQLAlchemyConfig(
        binds={
            "default": AsyncBindConfig(
                engine=EngineConfig(
                    url=f"sqlite+aiosqlite:///{environ["DATABASE_PATH"]}",
                )
            )
        }
    ),
    app=app,
)
get_session: Callable[[], AsyncSession[Any]] = lambda: db.bind.Session()  # type: ignore


async def create_initial_streams() -> None:
    from inter.blueprints.api.v1.stream import streams
    from inter.models.db.user import User
    from inter.models.stream import Stream
    import inter.models.db.follow as _
    import inter.models.db.session as _
    await db.create_all()
    async with get_session() as session, session.begin():
        for id in (await session.scalars(select(User.id))).all():
            streams[id] = Stream()


asyncio.run(create_initial_streams())

COLOUR_COUNT = 17
