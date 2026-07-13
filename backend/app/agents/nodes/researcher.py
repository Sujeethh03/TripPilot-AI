"""Researcher — gathers real data via MCP tools (§9).

NO LLM. Orchestrates MCP tool calls and aggregates the results into a
ResearchBundle for the Synthesizer to ground its plan on. Today it fetches
weather; places / directions / buses are added as those servers land, ideally
called in parallel and cached in Redis.
"""

from __future__ import annotations

from typing import Any

from app.agents.state import ConversationState
from app.mcp.weather import fetch_forecast
from app.schemas.planning import ResearchBundle


async def researcher(state: ConversationState) -> dict[str, Any]:
    trip = state.get("trip_request")
    weather_by_day: dict[str, Any] = {}

    if trip is not None and trip.destination:
        forecast = await fetch_forecast(trip.destination, days=5)
        if forecast is not None:
            weather_by_day = {
                day.date: {
                    "min_temp_c": day.min_temp_c,
                    "max_temp_c": day.max_temp_c,
                    "condition": day.condition,
                }
                for day in forecast.days
            }

    return {"research": ResearchBundle(weather_by_day=weather_by_day)}
