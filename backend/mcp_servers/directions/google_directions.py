"""Google Directions API adapter for the directions MCP server.

Uses the legacy Directions API (simple GET, same Maps key as places). Parsing
is defensive (PROJECT_PLAN §5.1 #11): upstream JSON is assumed to be possibly
malformed, and a no-route response yields ok=False rather than raising.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from mcp_servers.directions.schemas import DirectionsResult

_DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"
_MODES = {"driving", "walking", "transit", "bicycling"}


class DirectionsError(RuntimeError):
    """Raised when the upstream directions provider fails or is misconfigured."""


class GoogleDirectionsClient:
    """Thin async client over the Google Directions API.

    An httpx client may be injected for testing; otherwise one is created per
    call. The API key defaults to the GOOGLE_MAPS_KEY environment variable.
    """

    def __init__(
        self, api_key: str | None = None, http_client: httpx.AsyncClient | None = None
    ) -> None:
        self._api_key = api_key if api_key is not None else os.getenv("GOOGLE_MAPS_KEY", "")
        self._http = http_client

    async def directions(
        self, origin: str, destination: str, mode: str = "driving"
    ) -> DirectionsResult:
        if not self._api_key:
            raise DirectionsError("GOOGLE_MAPS_KEY is not set")
        mode = mode if mode in _MODES else "driving"

        params = {
            "origin": origin,
            "destination": destination,
            "mode": mode,
            "key": self._api_key,
        }
        try:
            if self._http is not None:
                resp = await self._http.get(_DIRECTIONS_URL, params=params)
            else:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(_DIRECTIONS_URL, params=params)
            resp.raise_for_status()
            payload: Any = resp.json()
        except httpx.HTTPError as exc:
            raise DirectionsError(f"directions request failed: {exc}") from exc

        distance_m, duration_s = _first_route_totals(payload)
        if distance_m is None or duration_s is None:
            return DirectionsResult(origin=origin, destination=destination, mode=mode, ok=False)
        return DirectionsResult(
            origin=origin,
            destination=destination,
            mode=mode,
            ok=True,
            distance_km=round(distance_m / 1000, 1),
            duration_min=round(duration_s / 60, 1),
        )


def _first_route_totals(payload: Any) -> tuple[float | None, float | None]:
    """Sum distance/duration across the first route's legs, defensively."""
    if not isinstance(payload, dict):
        return None, None
    routes = payload.get("routes")
    if not isinstance(routes, list) or not routes or not isinstance(routes[0], dict):
        return None, None
    legs = routes[0].get("legs")
    if not isinstance(legs, list) or not legs:
        return None, None

    distance = 0.0
    duration = 0.0
    for leg in legs:
        if not isinstance(leg, dict):
            continue
        distance += _value(leg.get("distance"))
        duration += _value(leg.get("duration"))
    return distance, duration


def _value(field: Any) -> float:
    if isinstance(field, dict) and isinstance(field.get("value"), (int, float)):
        return float(field["value"])
    return 0.0
