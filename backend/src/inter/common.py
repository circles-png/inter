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
from sqlalchemy.dialects.sqlite import insert

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
    import inter.models.db.moderation as _
    from inter.models.db.role import Roles

    async with app.app_context():
        await db.create_all()
    async with get_session() as session, session.begin():
        with open("assets/moderator.png", "rb") as f:
            moderator_icon = f.read()
        with open("assets/vip.png", "rb") as f:
            vip_icon = f.read()
        await session.execute(
            insert(Roles)
            .values(
                [
                    {
                        "id": 0,
                        "name": "Moderator",
                        "icon": moderator_icon,
                        "moderator": True,
                    },
                    {"id": 1, "name": "VIP", "icon": vip_icon, "vip": True},
                ]
            )
            .on_conflict_do_nothing()
        )
        for id in (await session.scalars(select(User.id))).all():
            streams[id] = Stream()


asyncio.run(create_initial_streams())

COLOUR_COUNT = 17
