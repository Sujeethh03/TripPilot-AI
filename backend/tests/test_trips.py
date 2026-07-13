"""Integration tests for the trips REST endpoints."""

from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models import Conversation, Message, Trip
from app.repositories.conversation_repository import ConversationRepository, MessageRepository
from tests.conftest import register_and_auth


async def test_create_and_get_trip(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    r = await client.post(
        "/api/v1/trips",
        json={"title": "Kerala trip", "destination": "Kerala", "budget_inr": 20000},
        headers=auth_headers,
    )
    assert r.status_code == 201
    trip = r.json()
    assert trip["destination"] == "Kerala"
    assert trip["status"] == "draft"

    r = await client.get(f"/api/v1/trips/{trip['id']}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["id"] == trip["id"]


async def test_list_trips(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    await client.post("/api/v1/trips", json={"destination": "Goa"}, headers=auth_headers)
    await client.post("/api/v1/trips", json={"destination": "Munnar"}, headers=auth_headers)
    r = await client.get("/api/v1/trips", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) == 2


async def test_update_and_delete_trip(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    trip_id = (
        await client.post("/api/v1/trips", json={"destination": "Ooty"}, headers=auth_headers)
    ).json()["id"]

    r = await client.patch(
        f"/api/v1/trips/{trip_id}", json={"title": "Ooty weekend"}, headers=auth_headers
    )
    assert r.status_code == 200 and r.json()["title"] == "Ooty weekend"

    delete = await client.delete(f"/api/v1/trips/{trip_id}", headers=auth_headers)
    assert delete.status_code == 204
    gone = await client.get(f"/api/v1/trips/{trip_id}", headers=auth_headers)
    assert gone.status_code == 404


async def test_messages_and_ownership(client: AsyncClient, auth_headers: dict[str, str]) -> None:
    trip_id = (
        await client.post("/api/v1/trips", json={"destination": "Hampi"}, headers=auth_headers)
    ).json()["id"]

    r = await client.get(f"/api/v1/trips/{trip_id}/messages", headers=auth_headers)
    assert r.status_code == 200 and r.json() == []

    # A different user cannot see this trip (404, not 403 — don't leak existence).
    other = await register_and_auth(client, "intruder@trippilot.ai")
    assert (await client.get(f"/api/v1/trips/{trip_id}", headers=other)).status_code == 404
    msgs = await client.get(f"/api/v1/trips/{trip_id}/messages", headers=other)
    assert msgs.status_code == 404


async def test_delete_purges_all_trip_data(
    client: AsyncClient, auth_headers: dict[str, str], db_sessionmaker: async_sessionmaker
) -> None:
    trip_id = (
        await client.post("/api/v1/trips", json={"destination": "Coorg"}, headers=auth_headers)
    ).json()["id"]

    # Seed a message onto the trip's conversation.
    async with db_sessionmaker() as session:
        conv = await ConversationRepository(session).get_by_trip(trip_id)
        assert conv is not None
        await MessageRepository(session).add(
            conversation_id=conv.id, role="user", content="hi", agent_events=None
        )
        await session.commit()

    r = await client.delete(f"/api/v1/trips/{trip_id}", headers=auth_headers)
    assert r.status_code == 204

    # Trip, its conversation, and its messages are all gone (hard delete + cascade).
    async with db_sessionmaker() as session:
        assert await session.get(Trip, trip_id) is None
        convs = await session.scalar(
            select(func.count()).select_from(Conversation).where(Conversation.trip_id == trip_id)
        )
        msgs = await session.scalar(
            select(func.count())
            .select_from(Message)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(Conversation.trip_id == trip_id)
        )
        assert convs == 0
        assert msgs == 0


async def test_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/trips")).status_code == 401
    assert (await client.post("/api/v1/trips", json={})).status_code == 401
