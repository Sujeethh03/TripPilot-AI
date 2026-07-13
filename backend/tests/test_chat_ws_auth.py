"""Tests for the chat WebSocket auth/ownership gate (`_authorize`)."""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker

import app.api.v1.chat as chat
from app.core.security import create_access_token
from app.models import Trip, User


async def _seed_user_and_trip(sm: async_sessionmaker) -> tuple[User, Trip]:
    async with sm() as session:
        user = User(email="owner-ws@trippilot.ai", hashed_password="x")
        session.add(user)
        await session.flush()
        trip = Trip(user_id=user.id, destination="Kerala")
        session.add(trip)
        await session.flush()
        await session.commit()
        return user, trip


@pytest.fixture
def _use_test_db(db_sessionmaker: async_sessionmaker, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(chat, "get_sessionmaker", lambda: db_sessionmaker)


async def test_authorize_accepts_owner(
    db_sessionmaker: async_sessionmaker, _use_test_db: None
) -> None:
    user, trip = await _seed_user_and_trip(db_sessionmaker)
    token = create_access_token(str(user.id))
    result = await chat._authorize(str(trip.id), token)
    assert result is not None and result.id == trip.id


async def test_authorize_rejects_missing_token(
    db_sessionmaker: async_sessionmaker, _use_test_db: None
) -> None:
    _, trip = await _seed_user_and_trip(db_sessionmaker)
    assert await chat._authorize(str(trip.id), None) is None
    assert await chat._authorize(str(trip.id), "") is None


async def test_authorize_rejects_bad_token(
    db_sessionmaker: async_sessionmaker, _use_test_db: None
) -> None:
    _, trip = await _seed_user_and_trip(db_sessionmaker)
    assert await chat._authorize(str(trip.id), "not-a-jwt") is None


async def test_authorize_rejects_non_uuid_trip(
    db_sessionmaker: async_sessionmaker, _use_test_db: None
) -> None:
    user, _ = await _seed_user_and_trip(db_sessionmaker)
    token = create_access_token(str(user.id))
    assert await chat._authorize("ws-1", token) is None


async def test_authorize_rejects_non_owner(
    db_sessionmaker: async_sessionmaker, _use_test_db: None
) -> None:
    _, trip = await _seed_user_and_trip(db_sessionmaker)
    # A valid token for a different (non-existent-as-owner) user.
    other_token = create_access_token(str(uuid4()))
    assert await chat._authorize(str(trip.id), other_token) is None
