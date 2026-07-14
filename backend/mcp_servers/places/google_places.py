"""Google Places API (New) adapter for the places MCP server.

Uses the Text Search endpoint. Parsing is defensive (PROJECT_PLAN §5.1 #11):
upstream JSON is assumed to be possibly malformed. A field mask keeps the
response (and cost) minimal — we request only what the contract exposes.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

from mcp_servers.places.schemas import Place, PlacesResult

_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
_FIELD_MASK = (
    "places.displayName,places.formattedAddress,places.location,places.rating,places.id"
)


class PlacesError(RuntimeError):
    """Raised when the upstream places provider fails or is misconfigured."""


class GooglePlacesClient:
    """Thin async client over the Google Places Text Search API.

    An httpx client may be injected for testing; otherwise one is created per
    call. The API key defaults to the GOOGLE_MAPS_KEY environment variable.
    """

    def __init__(
        self, api_key: str | None = None, http_client: httpx.AsyncClient | None = None
    ) -> None:
        self._api_key = api_key if api_key is not None else os.getenv("GOOGLE_MAPS_KEY", "")
        self._http = http_client

    async def search(self, query: str, max_results: int = 5) -> PlacesResult:
        return await self._text_search(query, max_results)

    async def search_hotels(self, location: str, max_results: int = 4) -> PlacesResult:
        """Find lodging near a location. Uses the Places `lodging` type so results
        are actual hotels rather than generic matches for the word 'hotel'."""
        return await self._text_search(
            f"hotels in {location}", max_results, included_type="lodging"
        )

    async def _text_search(
        self, query: str, max_results: int, included_type: str | None = None
    ) -> PlacesResult:
        if not self._api_key:
            raise PlacesError("GOOGLE_MAPS_KEY is not set")

        headers = {
            "X-Goog-Api-Key": self._api_key,
            "X-Goog-FieldMask": _FIELD_MASK,
            "Content-Type": "application/json",
        }
        body: dict[str, Any] = {
            "textQuery": query,
            "maxResultCount": max(1, min(max_results, 20)),
        }
        if included_type is not None:
            body["includedType"] = included_type
        try:
            if self._http is not None:
                resp = await self._http.post(_SEARCH_URL, headers=headers, json=body)
            else:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(_SEARCH_URL, headers=headers, json=body)
            resp.raise_for_status()
            payload: Any = resp.json()
        except httpx.HTTPError as exc:
            raise PlacesError(f"places request failed: {exc}") from exc

        return PlacesResult(query=query, places=_parse_places(payload, max_results))


def _parse_places(payload: Any, limit: int) -> list[Place]:
    raw = payload.get("places") if isinstance(payload, dict) else None
    if not isinstance(raw, list):
        return []
    places: list[Place] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        location = item.get("location")
        if not isinstance(location, dict):
            location = {}
        places.append(
            Place(
                name=_display_name(item),
                address=_str(item.get("formattedAddress")),
                lat=_float(location.get("latitude")),
                lng=_float(location.get("longitude")),
                rating=_float(item.get("rating")),
                place_id=_str(item.get("id")),
            )
        )
        if len(places) >= limit:
            break
    return places


def _display_name(item: dict[str, Any]) -> str:
    name = item.get("displayName")
    if isinstance(name, dict):
        text = name.get("text")
        if isinstance(text, str):
            return text
    return ""


def _str(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _float(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None
