"""Contract test: the places MCP tool is callable and returns structured data.

Uses FastMCP's in-memory client (no subprocess) and stubs the upstream client
so the test needs no network or API key.
"""

import pytest
from fastmcp import Client

from mcp_servers.places import server
from mcp_servers.places.schemas import Place, PlacesResult


async def test_search_places_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_search(query: str, max_results: int = 5) -> PlacesResult:
        return PlacesResult(
            query=query,
            places=[Place(name="Athirappilly Falls", rating=4.6, lat=10.285, lng=76.569)],
        )

    monkeypatch.setattr(server._client, "search", fake_search)

    async with Client(server.mcp) as client:
        tools = {t.name for t in await client.list_tools()}
        assert "search_places" in tools

        result = await client.call_tool(
            "search_places", {"query": "waterfalls near Munnar", "max_results": 3}
        )

    data = result.structured_content
    assert data["query"] == "waterfalls near Munnar"
    assert data["places"][0]["name"] == "Athirappilly Falls"
