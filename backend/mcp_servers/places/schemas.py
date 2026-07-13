"""Public tool contract for the places MCP server.

These types ARE the interface (PROJECT_PLAN §5.1 #12): the underlying provider
(Google Places today) is swappable as long as it returns these shapes. The
Validator uses `open_now`/coordinates; the Planner uses names + ratings.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Place(BaseModel):
    """A single point of interest."""

    name: str
    address: str = ""
    lat: float | None = None
    lng: float | None = None
    rating: float | None = None  # 0-5
    place_id: str = ""


class PlacesResult(BaseModel):
    """Places matching a text query."""

    query: str
    places: list[Place] = Field(default_factory=list)
