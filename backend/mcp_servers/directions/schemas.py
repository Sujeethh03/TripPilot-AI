"""Public tool contract for the directions MCP server.

These types ARE the interface (PROJECT_PLAN §5.1 #12): the routing provider
(Google Directions today) is swappable as long as it returns these shapes. The
Validator can use `duration_min` for drive-time feasibility once itinerary
blocks carry locations to route between.
"""

from __future__ import annotations

from pydantic import BaseModel


class DirectionsResult(BaseModel):
    """A single summarized route between two points."""

    origin: str
    destination: str
    mode: str  # driving | walking | transit | bicycling
    ok: bool  # whether a route was found
    distance_km: float | None = None
    duration_min: float | None = None
