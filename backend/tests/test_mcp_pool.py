"""Integration test: the client pool spawns the weather server and lists tools.

Validates the end-to-end MCP wiring (stdio subprocess + langchain adapters)
without any network call — tool discovery doesn't hit OpenWeatherMap.
"""

from app.mcp.client_pool import get_tools


async def test_pool_discovers_weather_tool() -> None:
    tools = await get_tools()
    names = {t.name for t in tools}
    assert "get_forecast" in names
