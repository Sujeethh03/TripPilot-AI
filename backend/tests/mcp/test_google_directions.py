"""Unit tests for the Google Directions adapter — parsing logic."""

import httpx
import pytest

from mcp_servers.directions.google_directions import DirectionsError, GoogleDirectionsClient

_CANNED = {
    "status": "OK",
    "routes": [
        {
            "legs": [
                {"distance": {"value": 130000}, "duration": {"value": 12600}},
            ]
        }
    ],
}


def _client_with(
    json_body: dict, status: int = 200
) -> tuple[GoogleDirectionsClient, httpx.AsyncClient]:
    transport = httpx.MockTransport(lambda req: httpx.Response(status, json=json_body))
    http = httpx.AsyncClient(transport=transport)
    return GoogleDirectionsClient(api_key="test-key", http_client=http), http


async def test_directions_parses_totals() -> None:
    client, http = _client_with(_CANNED)
    async with http:
        result = await client.directions("Kochi", "Munnar", "driving")
    assert result.ok is True
    assert result.distance_km == 130.0
    assert result.duration_min == 210.0
    assert result.mode == "driving"


async def test_directions_no_route_is_not_ok() -> None:
    client, http = _client_with({"status": "ZERO_RESULTS", "routes": []})
    async with http:
        result = await client.directions("A", "B")
    assert result.ok is False
    assert result.distance_km is None


async def test_invalid_mode_falls_back_to_driving() -> None:
    client, http = _client_with(_CANNED)
    async with http:
        result = await client.directions("Kochi", "Munnar", "teleport")
    assert result.mode == "driving"


async def test_missing_api_key_raises() -> None:
    client = GoogleDirectionsClient(api_key="")
    with pytest.raises(DirectionsError):
        await client.directions("A", "B")
