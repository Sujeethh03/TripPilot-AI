"""Data access for trips (the aggregate root for a planning session)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Trip


class TripRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, user_id: UUID, **fields: object) -> Trip:
        trip = Trip(user_id=user_id, **fields)
        self._session.add(trip)
        await self._session.flush()
        return trip

    async def get_for_user(self, trip_id: UUID, user_id: UUID) -> Trip | None:
        """Fetch a non-deleted trip owned by the user (ownership enforced here)."""
        result = await self._session.execute(
            select(Trip).where(
                Trip.id == trip_id,
                Trip.user_id == user_id,
                Trip.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: UUID, *, limit: int, offset: int) -> list[Trip]:
        result = await self._session.execute(
            select(Trip)
            .where(Trip.user_id == user_id, Trip.deleted_at.is_(None))
            .order_by(Trip.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def soft_delete(self, trip: Trip) -> None:
        # Naive UTC to match the other TIMESTAMP WITHOUT TIME ZONE columns.
        trip.deleted_at = datetime.now(UTC).replace(tzinfo=None)
        await self._session.flush()

    async def hard_delete(self, trip: Trip) -> None:
        """Permanently remove the trip. Conversations + messages cascade via
        their ON DELETE CASCADE foreign keys. The LangGraph checkpoint (keyed by
        thread_id) is deleted separately by the endpoint."""
        await self._session.delete(trip)
        await self._session.flush()
