import asyncio
import importlib
from hypothesis import given
from hypothesis.strategies import text, one_of, sampled_from, lists
import pytest
from sqlalchemy import select
from sqlalchemy.orm import aliased

import inter.common
importlib.reload(inter.common)
from inter import create_app
app = create_app()

from inter.models.db.role import Roles, UsersRoles
from inter.common import get_session
from inter.models.db.user import User


@pytest.fixture
def anyio_backend():
    return "asyncio"


url_safe = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.~"


async def get_users():
    async with get_session() as session, session.begin():
        return [
            user.__dict__
            for user in (await session.execute(select(User))).scalars().all()
        ]


users = asyncio.run(get_users())


username = one_of(
    sampled_from([user["username"] for user in users]),
    text(url_safe, min_size=1, max_size=200),
)


@pytest.mark.anyio
async def test_random():
    test = app.test_client()
    response = await test.get("/api/v1/random")
    assert response.status_code == 200
    async with get_session() as session, session.begin():
        assert (
            await session.execute(
                select(User).where(User.username == await response.get_data(True))
            )
        ).scalar() is not None


@pytest.mark.anyio
@given(text(url_safe, min_size=1, max_size=200))
async def test_search(query: str):
    test = app.test_client()
    response = await test.get(f"/api/v1/search/{query}")
    assert response.status_code == 200
    results = await response.json
    assert isinstance(results, list)
    assert all(isinstance(result, dict) for result in results)  # type: ignore
    assert all(result["name"] in ["Following", "Results"] for result in results)  # type: ignore
    assert all(isinstance(result["results"], list) for result in results)  # type: ignore
    assert all(isinstance(user, str) for result in results for user in result["results"])  # type: ignore


@pytest.mark.anyio
async def test_emotes():
    test = app.test_client()
    response = await test.get("/api/v1/emotes")
    assert response.status_code == 200
    assert isinstance(await response.json, dict)


@pytest.mark.anyio
@given(text(url_safe, min_size=1, max_size=200))
async def test_auth_available(username: str):
    test = app.test_client()
    response = await test.get(f"/api/v1/auth/available/{username}")
    async with get_session() as session, session.begin():
        available = (
            await session.execute(select(User).where(User.username == username))
        ).scalar() is None
    assert response.status_code == (200 if available else 409)
    assert await response.json is None


@pytest.mark.anyio
@given(username)
async def test_user_avatar(username: str):
    test = app.test_client()
    response = await test.get(f"/api/v1/user/{username}/avatar")
    async with get_session() as session, session.begin():
        user = (
            await session.execute(select(User).where(User.username == username))
        ).scalar()

        if user is None:
            assert response.status_code == 404
        else:
            if user.avatar:
                assert response.status_code == 200
                assert response.headers["Content-Type"] == "image/png"
            else:
                assert response.status_code == 204
                assert await response.json is None


@pytest.mark.anyio
@given(username)
async def test_user_get(username: str):
    test = app.test_client()
    response = await test.get(f"/api/v1/user/{username}/")
    async with get_session() as session, session.begin():
        user = (
            await session.execute(select(User).where(User.username == username))
        ).scalar()

        if user is None:
            assert response.status_code == 404
        else:
            assert response.status_code == 200
            data = await response.json
            assert data["displayName"] == user.display_name
            assert data["following"] == await user.following_count(session)
            assert data["followers"] == await user.followers_count(session)


@pytest.mark.anyio
@given(username)
async def test_user_followers(username: str):
    test = app.test_client()
    response = await test.get(f"/api/v1/user/{username}/followers")
    async with get_session() as session, session.begin():
        user = (
            await session.execute(select(User).where(User.username == username))
        ).scalar()

        if user is None:
            assert response.status_code == 404
        else:
            assert response.status_code == 200
            data = await response.json
            assert data == await user.followers_count(session)


@pytest.mark.anyio
@given(username)
async def test_user_following(username: str):
    test = app.test_client()
    response = await test.get(f"/api/v1/user/{username}/following")
    async with get_session() as session, session.begin():
        user = (
            await session.execute(select(User).where(User.username == username))
        ).scalar()

        if user is None:
            assert response.status_code == 404
        else:
            assert response.status_code == 200
            data = await response.json
            assert data == await user.following_count(session)


@pytest.mark.anyio
@given(lists(username, min_size=2, max_size=2, unique=True))
async def test_roles(users: list[str]):
    username, subject = users
    test = app.test_client()
    response = await test.get(f"/api/v1/user/{username}/roles/{subject}")
    async with get_session() as session, session.begin():
        target_table = aliased(User, name="target")
        subject_table = aliased(User, name="subject")
        roles = (
            (
                await session.execute(
                    select(UsersRoles.role)
                    .join(target_table, target_table.id == UsersRoles.target)
                    .join(subject_table, subject_table.id == UsersRoles.subject)
                    .where(
                        target_table.username == username,
                        subject_table.username == subject,
                    )
                )
            )
            .scalars()
            .all()
        )
        assert response.status_code == (
            200
            if (
                await session.execute(select(User).where(User.username == subject))
            ).scalar()
            and (
                await session.execute(select(User).where(User.username == username))
            ).scalar()
            else 404
        )
        if roles:
            data = await response.json
            assert roles == data


@pytest.mark.anyio
async def test_all_roles():
    test = app.test_client()
    response = await test.get("/api/v1/roles/")
    async with get_session() as session, session.begin():
        roles = (await session.execute(select(Roles.name))).scalars().all()
        assert response.status_code == 200
        data = await response.json
        assert set(roles) == set(role["name"] for role in data)


@pytest.mark.anyio
async def test_role_icon():
    test = app.test_client()
    async with get_session() as session, session.begin():
        roles = (await session.execute(select(Roles.id))).scalars().all()
        for role in roles:
            response = await test.get(f"/api/v1/roles/{role}/icon")
            assert response.status_code == 200
            assert response.headers["Content-Type"] == "image/png"
