"""Unit tests for the Google Places adapter — parsing logic."""

import httpx
import pytest

from mcp_servers.places.google_places import GooglePlacesClient, PlacesError

_CANNED = {
    "places": [
        {
            "id": "abc123",
            "displayName": {"text": "Athirappilly Falls", "languageCode": "en"},
            "formattedAddress": "Athirappilly, Kerala",
            "location": {"latitude": 10.285, "longitude": 76.569},
            "rating": 4.6,
        },
        {
            "id": "def456",
            "displayName": {"text": "Vazhachal Falls"},
            "formattedAddress": "Vazhachal, Kerala",
            "location": {"latitude": 10.3, "longitude": 76.6},
        },
    ]
}


def _client_with(
    json_body: dict, status: int = 200
) -> tuple[GooglePlacesClient, httpx.AsyncClient]:
    transport = httpx.MockTransport(lambda req: httpx.Response(status, json=json_body))
    http = httpx.AsyncClient(transport=transport)
    return GooglePlacesClient(api_key="test-key", http_client=http), http


async def test_search_parses_places() -> None:
    client, http = _client_with(_CANNED)
    async with http:
        result = await client.search("waterfalls near Athirappilly", max_results=5)

    assert result.query == "waterfalls near Athirappilly"
    assert len(result.places) == 2
    first = result.places[0]
    assert first.name == "Athirappilly Falls"
    assert first.lat == 10.285
    assert first.rating == 4.6
    assert first.place_id == "abc123"
    # Missing rating tolerated.
    assert result.places[1].rating is None


async def test_max_results_limits_output() -> None:
    client, http = _client_with(_CANNED)
    async with http:
        result = await client.search("kerala", max_results=1)
    assert len(result.places) == 1


async def test_missing_api_key_raises() -> None:
    client = GooglePlacesClient(api_key="")
    with pytest.raises(PlacesError):
        await client.search("anything")


async def test_malformed_payload_yields_no_places() -> None:
    client, http = _client_with({"unexpected": "shape"})
    async with http:
        result = await client.search("kerala")
    assert result.places == []
