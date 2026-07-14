"""Unit test for the chat WebSocket turn-persistence path.

Verifies that a completed turn writes the user + assistant messages (with the
streamed agent events) and saves the itinerary onto the trip row. Exercised
directly against the test DB, bypassing the WebSocket transport.
"""

from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

import app.api.v1.chat as chat
from app.models import Conversation, Message, Trip, User
from app.repositories.conversation_repository import ConversationRepository
from tests.conftest import valid_itinerary


@pytest.mark.asyncio
async def test_persist_turn_writes_messages_and_itinerary(
    db_sessionmaker: async_sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(chat, "get_sessionmaker", lambda: db_sessionmaker)

    # Seed a user + trip + conversation (thread_id == trip id).
    async with db_sessionmaker() as session:
        user = User(email="ws@trippilot.ai", hashed_password="x")
        session.add(user)
        await session.flush()
        trip = Trip(user_id=user.id, destination="Kerala")
        session.add(trip)
        await session.flush()
        await ConversationRepository(session).create(trip_id=trip.id, thread_id=trip.id)
        await session.commit()
        trip_id = trip.id

    itinerary = valid_itinerary()
    events = [
        {"type": "route_decision", "route": "plan"},
        {"type": "validation_report", "is_valid": True, "issues": []},
    ]
    await chat._persist_turn(
        str(trip_id),
        "5 days kerala 20k",
        assistant_texts=["Here is your plan!"],
        events=events,
        itinerary=itinerary,
    )

    async with db_sessionmaker() as session:
        messages = list(
            (
                await session.execute(
                    select(Message)
                    .join(Conversation, Message.conversation_id == Conversation.id)
                    .where(Conversation.trip_id == trip_id)
                    .order_by(Message.created_at.asc())
                )
            )
            .scalars()
            .all()
        )
        assert [m.role for m in messages] == ["user", "assistant"]
        assert messages[0].content == "5 days kerala 20k"
        assert messages[1].content == "Here is your plan!"
        assert messages[1].agent_events == {"events": events}

        saved = await session.get(Trip, trip_id)
        assert saved is not None
        assert saved.itinerary is not None
        assert saved.itinerary["destination"] == "Kerala"


@pytest.mark.asyncio
async def test_persist_turn_skips_empty_assistant(
    db_sessionmaker: async_sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No assistant text -> only the user row is written (no blank bubble)."""
    monkeypatch.setattr(chat, "get_sessionmaker", lambda: db_sessionmaker)

    async with db_sessionmaker() as session:
        user = User(email="empty@trippilot.ai", hashed_password="x")
        session.add(user)
        await session.flush()
        trip = Trip(user_id=user.id, destination="Goa")
        session.add(trip)
        await session.flush()
        await ConversationRepository(session).create(trip_id=trip.id, thread_id=trip.id)
        await session.commit()
        trip_id = trip.id

    await chat._persist_turn(
        str(trip_id), "hi", assistant_texts=[], events=[], itinerary=None
    )

    async with db_sessionmaker() as session:
        roles = [
            m.role
            for m in (
                await session.execute(
                    select(Message)
                    .join(Conversation, Message.conversation_id == Conversation.id)
                    .where(Conversation.trip_id == trip_id)
                )
            )
            .scalars()
            .all()
        ]
        assert roles == ["user"]


def test_plan_summary_uses_itinerary_facts() -> None:
    summary = chat._plan_summary(valid_itinerary())
    assert "Kerala" in summary and "day" in summary


@pytest.mark.asyncio
async def test_persist_turn_noops_for_unknown_thread(
    db_sessionmaker: async_sessionmaker, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(chat, "get_sessionmaker", lambda: db_sessionmaker)

    # A valid UUID with no conversation should not raise or write anything.
    await chat._persist_turn(
        str(uuid4()), "hello", assistant_texts=[], events=[], itinerary=None
    )

    async with db_sessionmaker() as session:
        count = len((await session.execute(select(Message))).scalars().all())
        assert count == 0
