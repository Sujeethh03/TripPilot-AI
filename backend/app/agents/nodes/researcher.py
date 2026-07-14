"""Researcher — gathers real data via MCP tools (§9).

NO LLM. Orchestrates MCP tool calls and aggregates the results into a
ResearchBundle for the Synthesizer to ground its plan on. Fetches weather and
real candidate places (one search per day theme) in parallel. Directions/buses
are added as those flows firm up. Every call is defensive: a failed tool yields
nothing rather than breaking the turn.
"""

from __future__ import annotations

import asyncio
from typing import Any

from app.agents.state import ConversationState
from app.mcp.directions import get_directions
from app.mcp.places import search_hotels, search_places
from app.mcp.weather import fetch_forecast
from app.schemas.planning import DaySkeleton, ResearchBundle
from app.schemas.trip import TripRequest

# Google Directions supports these; the form offers drive / transit.
_ALLOWED_MODES = {"driving", "transit", "walking", "bicycling"}
_MAX_HOTELS = 4

# Cap searches per turn to keep latency + API cost bounded (§9 cost controls).
_MAX_PLACE_QUERIES = 5
_RESULTS_PER_QUERY = 4


def _place_queries(destination: str, skeletons: list[DaySkeleton]) -> list[str]:
    """Build a small, de-duplicated set of text queries from the day themes."""
    raw: list[str] = []
    for skeleton in skeletons:
        area = skeleton.target_areas[0] if skeleton.target_areas else destination
        raw.append(f"{skeleton.theme} in {area}")
    if not raw:
        raw.append(f"top attractions in {destination}")

    seen: set[str] = set()
    unique: list[str] = []
    for query in raw:
        if query not in seen:
            seen.add(query)
            unique.append(query)
    return unique[:_MAX_PLACE_QUERIES]


async def _gather_places(destination: str, skeletons: list[DaySkeleton]) -> list[dict[str, Any]]:
    queries = _place_queries(destination, skeletons)
    tasks = [search_places(q, max_results=_RESULTS_PER_QUERY) for q in queries]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for result in results:
        if not result or isinstance(result, BaseException):
            continue
        for place in result.places:
            key = place.place_id or place.name
            if not key or key in seen:
                continue
            seen.add(key)
            candidates.append(
                {
                    "name": place.name,
                    "address": place.address,
                    "rating": place.rating,
                    "lat": place.lat,
                    "lng": place.lng,
                }
            )
    return candidates


async def _gather_hotels(destination: str) -> list[dict[str, Any]]:
    result = await search_hotels(destination, max_results=_MAX_HOTELS)
    if not result:
        return []
    return [
        {"name": place.name, "area": place.address, "rating": place.rating}
        for place in result.places
    ]


async def _travel_leg(trip: TripRequest) -> dict[str, Any] | None:
    """Route from the traveller's starting point to the destination, if given."""
    if not trip.origin or not trip.destination:
        return None
    mode = trip.transport_mode if trip.transport_mode in _ALLOWED_MODES else "driving"
    result = await get_directions(trip.origin, trip.destination, mode=mode)
    if result is None or not result.ok:
        return None
    return {
        "origin": result.origin,
        "destination": result.destination,
        "mode": result.mode,
        "distance_km": result.distance_km,
        "duration_min": result.duration_min,
    }


def _weather_map(forecast: Any) -> dict[str, Any]:
    if forecast is None:
        return {}
    return {
        day.date: {
            "min_temp_c": day.min_temp_c,
            "max_temp_c": day.max_temp_c,
            "condition": day.condition,
        }
        for day in forecast.days
    }


async def researcher(state: ConversationState) -> dict[str, Any]:
    trip: TripRequest | None = state.get("trip_request")
    if trip is None or not trip.destination:
        return {"research": ResearchBundle()}

    skeletons = state.get("day_skeletons") or []
    forecast, candidate_places, hotels, travel_leg = await asyncio.gather(
        fetch_forecast(trip.destination, days=5),
        _gather_places(trip.destination, skeletons),
        _gather_hotels(trip.destination),
        _travel_leg(trip),
    )

    return {
        "research": ResearchBundle(
            weather_by_day=_weather_map(forecast),
            candidate_places=candidate_places,
            hotels=hotels,
            travel_leg=travel_leg,
        )
    }
