"""Public tool contract for the weather MCP server.

These types ARE the interface (PROJECT_PLAN §5.1 #12): the underlying provider
is swappable as long as it returns these shapes.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class DailyForecast(BaseModel):
    """Aggregated forecast for a single calendar day."""

    date: str  # ISO date, YYYY-MM-DD
    min_temp_c: float
    max_temp_c: float
    condition: str  # human-readable, e.g. "light rain"


class ForecastResult(BaseModel):
    """Daily forecast for a city over the requested horizon."""

    city: str
    days: list[DailyForecast] = Field(default_factory=list)
