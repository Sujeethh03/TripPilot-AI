"""Contract test: the directions MCP tool is callable and returns structured data."""

import pytest
from fastmcp import Client

from mcp_servers.directions import server
from mcp_servers.directions.schemas import DirectionsResult


async def test_get_directions_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_directions(origin: str, destination: str, mode: str) -> DirectionsResult:
        return DirectionsResult(
            origin=origin,
            destination=destination,
            mode=mode,
            ok=True,
            distance_km=130.0,
            duration_min=210.0,
        )

    monkeypatch.setattr(server._client, "directions", fake_directions)

    async with Client(server.mcp) as client:
        tools = {t.name for t in await client.list_tools()}
        assert "get_directions" in tools

        result = await client.call_tool(
            "get_directions", {"origin": "Kochi", "destination": "Munnar", "mode": "driving"}
        )

    data = result.structured_content
    assert data["ok"] is True
    assert data["duration_min"] == 210.0
