"""Chat WebSocket — the core interaction (PROJECT_PLAN §11).

    WS /ws/trips/{trip_id}/chat
    -> { "type": "user_message", "content": "..." }
    <- streamed events: route_decision, agent_update, partial_itinerary,
       validation_report, assistant_message, complete, error

Authentication: the JWT is passed as a `?token=` query param on the connect URL
(WebSocket clients can't set Authorization headers). The socket is only accepted
if the token is valid AND the caller owns the trip; otherwise it is closed with
code 4401 before accept (no distinction between "bad token" and "not your trip",
mirroring the REST 404 no-leak policy).

The trip id is used as the LangGraph thread id, so each trip's conversation
resumes from its checkpoint. After each turn we persist the user + assistant
messages (with the streamed agent events) and save the latest itinerary onto
the trip row, so the REST layer (GET /trips/{id} and /messages) reflects the
live conversation.
"""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from langchain_core.runnables import RunnableConfig

from app.agents.streaming import _dump_itinerary, complete_event, node_events
from app.core.security import decode_access_token
from app.db.session import get_sessionmaker
from app.models import Trip
from app.repositories.conversation_repository import ConversationRepository, MessageRepository
from app.repositories.trip_repository import TripRepository
from app.repositories.user_repository import UserRepository
from app.schemas.itinerary import Itinerary

router = APIRouter()

# Close code for a rejected connection (4000-4999 is the app-defined range).
WS_UNAUTHORIZED = 4401


async def _authorize(trip_id: str, token: str | None) -> Trip | None:
    """Return the trip iff the token is valid and the caller owns it, else None.

    Opens its own short-lived session so the connection doesn't hold a DB
    session open for its whole lifetime (per-turn persistence gets its own).
    """
    if not token:
        return None
    subject = decode_access_token(token)
    if subject is None:
        return None
    try:
        user_id = UUID(subject)
        trip_uuid = UUID(trip_id)
    except ValueError:
        return None

    async with get_sessionmaker()() as session:
        if await UserRepository(session).get_by_id(user_id) is None:
            return None
        return await TripRepository(session).get_for_user(trip_uuid, user_id)


async def _persist_turn(
    trip_id: str,
    user_content: str,
    assistant_texts: list[str],
    events: list[dict[str, Any]],
    itinerary: Any,
) -> None:
    """Write the turn's messages and itinerary. No-ops for non-persistent
    threads (e.g. ad-hoc thread ids that don't map to a stored trip)."""
    try:
        trip_uuid = UUID(trip_id)
    except ValueError:
        return

    async with get_sessionmaker()() as session:
        conversation = await ConversationRepository(session).get_by_trip(trip_uuid)
        if conversation is None:
            return

        messages = MessageRepository(session)
        await messages.add(
            conversation_id=conversation.id,
            role="user",
            content=user_content,
            agent_events=None,
        )
        # Skip empty assistant rows (would render as a blank bubble on reload).
        if assistant_texts:
            await messages.add(
                conversation_id=conversation.id,
                role="assistant",
                content="\n\n".join(assistant_texts),
                agent_events={"events": events},
            )

        if itinerary is not None:
            trip = await session.get(Trip, trip_uuid)
            if trip is not None:
                trip.itinerary = _dump_itinerary(itinerary)

        await session.commit()


def _trip_context(trip: Trip) -> str | None:
    """A one-line summary of the details the traveller entered in the booking
    form, injected into the conversation so the agents don't re-ask for them."""
    parts: list[str] = []
    if trip.destination:
        parts.append(f"Destination: {trip.destination}")
    if trip.origin:
        mode = trip.transport_mode or "driving"
        parts.append(f"Travelling from: {trip.origin} (by {mode})")
    if trip.start_date and trip.end_date:
        days = (trip.end_date - trip.start_date).days + 1
        parts.append(f"Dates: {trip.start_date} to {trip.end_date} ({days} days)")
    elif trip.start_date:
        parts.append(f"Start date: {trip.start_date}")
    if trip.budget_inr:
        parts.append(f"Budget: ₹{trip.budget_inr}")
    if not parts:
        return None
    return (
        "The traveller already provided these trip details in the booking form; "
        "treat them as their stated request and do not ask for them again unless "
        "they change. " + "; ".join(parts) + "."
    )


def _plan_summary(itinerary: Itinerary) -> str:
    """A short, friendly acknowledgment for a planning turn (facts come straight
    from the itinerary — days/cost — so nothing is invented)."""
    days = len(itinerary.days)
    dest = itinerary.destination or "your trip"
    cost = f" for around ₹{itinerary.total_cost_inr:,}" if itinerary.total_cost_inr else ""
    return (
        f"I've put together a {days}-day {dest} itinerary{cost}. "
        "It's on the right — tell me what you'd like to change."
    )


async def _run_turn(
    ws: WebSocket,
    content: str,
    config: RunnableConfig,
    trip_id: str,
    trip_context: str | None,
) -> None:
    graph = ws.app.state.graph
    assistant_texts: list[str] = []
    events_log: list[dict[str, Any]] = []

    # On the first turn of a fresh thread, seed the form details as context so
    # Intake merges them with whatever the user types (rather than re-asking).
    inputs: list[dict[str, str]] = []
    snapshot = await graph.aget_state(config)
    if trip_context and not snapshot.values.get("messages"):
        inputs.append({"role": "system", "content": trip_context})
    inputs.append({"role": "user", "content": content})

    try:
        async for chunk in graph.astream(
            {"messages": inputs},
            config=config,
            stream_mode="updates",
        ):
            for node, update in chunk.items():
                for event in node_events(node, update):
                    events_log.append(event)
                    if event["type"] == "assistant_message":
                        assistant_texts.append(event["content"])
                    await ws.send_json(event)

        snapshot = await graph.aget_state(config)
        itinerary = snapshot.values.get("itinerary")

        # Planning routes stream the itinerary but no chat text, which reads as
        # "the AI didn't reply". If the turn produced/updated an itinerary and
        # said nothing, add a short acknowledgment so the chat always responds.
        if isinstance(itinerary, Itinerary) and not assistant_texts:
            summary = _plan_summary(itinerary)
            event = {"type": "assistant_message", "content": summary}
            events_log.append(event)
            assistant_texts.append(summary)
            await ws.send_json(event)

        await ws.send_json(complete_event(itinerary))
    except Exception as exc:  # surface failures to the client, keep socket open
        await ws.send_json({"type": "error", "message": str(exc)})
        return

    await _persist_turn(trip_id, content, assistant_texts, events_log, itinerary)


@router.websocket("/ws/trips/{trip_id}/chat")
async def chat_ws(
    ws: WebSocket, trip_id: str, token: Annotated[str | None, Query()] = None
) -> None:
    trip = await _authorize(trip_id, token)
    if trip is None:
        await ws.close(code=WS_UNAUTHORIZED)
        return
    # Snapshot the form details now, while the trip's attributes are loaded.
    trip_context = _trip_context(trip)
    await ws.accept()
    config: RunnableConfig = {"configurable": {"thread_id": trip_id}}
    try:
        while True:
            data = await ws.receive_json()
            if data.get("type") != "user_message":
                await ws.send_json({"type": "error", "message": "expected type=user_message"})
                continue
            await _run_turn(ws, data.get("content", ""), config, trip_id, trip_context)
    except WebSocketDisconnect:
        return
