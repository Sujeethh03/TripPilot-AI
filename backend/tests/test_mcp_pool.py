"""Integration test: the client pool spawns the MCP servers and lists tools.

Validates the end-to-end MCP wiring (stdio subprocesses + langchain adapters)
without any network call — tool discovery doesn't hit the upstream APIs.
"""

from app.mcp.client_pool import get_tools


async def test_pool_discovers_all_tools() -> None:
    tools = await get_tools()
    names = {t.name for t in tools}
    assert {"get_forecast", "convert_currency", "search_places", "get_directions"} <= names
