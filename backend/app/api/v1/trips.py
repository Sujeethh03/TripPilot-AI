"""Trip endpoints (PROJECT_PLAN §11).

Resource-oriented, ownership-enforced. A trip is created together with its
conversation; the conversation's thread id equals the trip id, which is the
LangGraph thread the chat WebSocket drives.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import Response

from app.api.deps import CurrentUser, SessionDep
from app.models import Trip
from app.repositories.conversation_repository import ConversationRepository, MessageRepository
from app.repositories.trip_repository import TripRepository
from app.schemas.itinerary import Itinerary
from app.schemas.trip_api import MessageResponse, TripCreate, TripResponse, TripUpdate
from app.services.pdf import render_itinerary_pdf

router = APIRouter(prefix="/trips", tags=["trips"])

Limit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0)]


async def _get_owned_trip(trip_id: UUID, user: CurrentUser, session: SessionDep) -> Trip:
    trip = await TripRepository(session).get_for_user(trip_id, user.id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return trip


@router.post("", response_model=TripResponse, status_code=status.HTTP_201_CREATED)
async def create_trip(body: TripCreate, user: CurrentUser, session: SessionDep) -> TripResponse:
    trip = await TripRepository(session).create(
        user_id=user.id,
        title=body.title,
        destination=body.destination,
        origin=body.origin,
        transport_mode=body.transport_mode,
        start_date=body.start_date,
        end_date=body.end_date,
        budget_inr=body.budget_inr,
    )
    # The conversation's thread id == trip id (the WebSocket drives that thread).
    await ConversationRepository(session).create(trip_id=trip.id, thread_id=trip.id)
    await session.commit()
    await session.refresh(trip)
    return TripResponse.model_validate(trip)


@router.get("", response_model=list[TripResponse])
async def list_trips(
    user: CurrentUser, session: SessionDep, limit: Limit = 20, offset: Offset = 0
) -> list[TripResponse]:
    trips = await TripRepository(session).list_for_user(user.id, limit=limit, offset=offset)
    return [TripResponse.model_validate(t) for t in trips]


@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(trip_id: UUID, user: CurrentUser, session: SessionDep) -> TripResponse:
    trip = await _get_owned_trip(trip_id, user, session)
    return TripResponse.model_validate(trip)


@router.patch("/{trip_id}", response_model=TripResponse)
async def update_trip(
    trip_id: UUID, body: TripUpdate, user: CurrentUser, session: SessionDep
) -> TripResponse:
    trip = await _get_owned_trip(trip_id, user, session)
    if body.title is not None:
        trip.title = body.title
    if body.status is not None:
        trip.status = body.status
    await session.commit()
    await session.refresh(trip)
    return TripResponse.model_validate(trip)


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trip(
    trip_id: UUID, user: CurrentUser, session: SessionDep, request: Request
) -> None:
    """Permanently delete a trip and all of its data: the trip row, its
    conversation + messages (via ON DELETE CASCADE), and the LangGraph
    conversation checkpoint (keyed by thread_id == trip id)."""
    trip = await _get_owned_trip(trip_id, user, session)

    # Purge the graph checkpoint first (best-effort; its own store/connection).
    graph = getattr(request.app.state, "graph", None)
    checkpointer = getattr(graph, "checkpointer", None) if graph is not None else None
    if checkpointer is not None and hasattr(checkpointer, "adelete_thread"):
        try:
            await checkpointer.adelete_thread(str(trip_id))
        except Exception:  # never let checkpoint cleanup block the DB delete
            pass

    await TripRepository(session).hard_delete(trip)
    await session.commit()


@router.get("/{trip_id}/messages", response_model=list[MessageResponse])
async def list_messages(
    trip_id: UUID,
    user: CurrentUser,
    session: SessionDep,
    limit: Limit = 50,
    offset: Offset = 0,
) -> list[MessageResponse]:
    await _get_owned_trip(trip_id, user, session)  # ownership check
    messages = await MessageRepository(session).list_by_trip(trip_id, limit=limit, offset=offset)
    return [MessageResponse.model_validate(m) for m in messages]


@router.get("/{trip_id}/pdf")
async def export_trip_pdf(trip_id: UUID, user: CurrentUser, session: SessionDep) -> Response:
    trip = await _get_owned_trip(trip_id, user, session)
    if trip.itinerary is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Trip has no itinerary to export yet",
        )
    itinerary = Itinerary.model_validate(trip.itinerary)
    pdf = render_itinerary_pdf(itinerary, title=trip.title)
    filename = f"trip-{trip_id}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
