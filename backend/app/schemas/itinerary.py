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


class Weather(BaseModel):
    """A day's forecast, filled deterministically from the weather MCP — never
    by the LLM (§ "never trust the LLM for facts")."""

    min_temp_c: float | None = None
    max_temp_c: float | None = None
    condition: str = ""


class Day(BaseModel):
    """One day of the trip."""

    day: int = Field(ge=1)
    blocks: list[Block] = Field(default_factory=list)
    weather: Weather | None = None


class TravelLeg(BaseModel):
    """How the traveller gets from their starting point to the destination.
    Distance/duration come from the directions MCP (a fact, not the LLM)."""

    origin: str
    destination: str
    mode: str = "driving"  # driving | transit
    distance_km: float | None = None
    duration_min: float | None = None


class HotelOption(BaseModel):
    """A place to stay, from the places MCP (lodging). No live price/availability."""

    name: str
    area: str = ""  # short address / locality
    rating: float | None = None


class Itinerary(BaseModel):
    """A full, validated day-by-day plan."""

    destination: str
    origin: str | None = None
    travel: TravelLeg | None = None
    hotels: list[HotelOption] = Field(default_factory=list)
    days: list[Day] = Field(default_factory=list)
    total_cost_inr: int = Field(default=0, ge=0)
