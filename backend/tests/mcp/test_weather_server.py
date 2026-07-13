"""Contract test: the weather MCP tool is callable and returns structured data.

Uses FastMCP's in-memory client (no subprocess) and stubs the upstream client
so the test needs no network or API key.
"""

import pytest
from fastmcp import Client

from mcp_servers.weather import server
from mcp_servers.weather.schemas import DailyForecast, ForecastResult


async def test_get_forecast_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_forecast(city: str, days: int = 5) -> ForecastResult:
        return ForecastResult(
            city=city,
            days=[
                DailyForecast(
                    date="2026-07-14",
                    min_temp_c=25.0,
                    max_temp_c=31.5,
                    condition="light rain",
                )
            ],
        )

    monkeypatch.setattr(server._client, "forecast", fake_forecast)

    async with Client(server.mcp) as client:
        tools = {t.name for t in await client.list_tools()}
        assert "get_forecast" in tools

        result = await client.call_tool("get_forecast", {"city": "Kochi", "days": 3})

    data = result.structured_content
    assert data["city"] == "Kochi"
    assert data["days"][0]["condition"] == "light rain"
