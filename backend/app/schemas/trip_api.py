"""Request/response schemas for the trips REST API.

Separate from the internal `TripRequest` agent schema — these map the DB model
to the HTTP boundary (Data Mapper, §5.3 #5).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TripCreate(BaseModel):
    title: str | None = None
    destination: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    budget_inr: int | None = Field(default=None, gt=0)


class TripUpdate(BaseModel):
    title: str | None = None
    status: str | None = None


class TripResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str | None
    destination: str | None
    start_date: date | None
    end_date: date | None
    budget_inr: int | None
    status: str
    itinerary: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    role: str
    content: str
    created_at: datetime
