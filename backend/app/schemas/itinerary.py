"""The canonical Itinerary schema — Single Source of Truth (PROJECT_PLAN §5.1).

Every consumer (WebSocket events, DB persistence, PDF export) imports these
types. Do not redefine the itinerary shape anywhere else.

Composite structure (§5.4): Itinerary -> Day[] -> Block[].
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Block(BaseModel):
    """A single scheduled activity within a day."""

    time: str  # "HH:MM" local, 24h
    activity: str
    location: str
    cost_inr: int = Field(default=0, ge=0)
    notes: str = ""


class Day(BaseModel):
    """One day of the trip."""

    day: int = Field(ge=1)
    blocks: list[Block] = Field(default_factory=list)


class Itinerary(BaseModel):
    """A full, validated day-by-day plan."""

    destination: str
    days: list[Day] = Field(default_factory=list)
    total_cost_inr: int = Field(default=0, ge=0)
