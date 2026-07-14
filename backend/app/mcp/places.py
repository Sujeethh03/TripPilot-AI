"""Helper for calling the places MCP tool from agent code.

Agents reach place data only through the MCP pool (never the upstream API).
This wraps the tool call and parses its result into the tool's declared
contract, defensively — a failed tool call yields None, not a crash.
"""

from __future__ import annotations

from app.mcp.client_pool import get_tools
from app.mcp.weather import _extract_text  # shared MCP result unwrapping
from mcp_servers.places.schemas import PlacesResult


async def _invoke(tool_name: str, args: dict[str, object]) -> PlacesResult | None:
    tools = {tool.name: tool for tool in await get_tools()}
    tool = tools.get(tool_name)
    if tool is None:
        return None
    try:
        raw = await tool.ainvoke(args)
    except Exception:
        return None

    text = _extract_text(raw)
    if text is None:
        return None
    try:
        return PlacesResult.model_validate_json(text)
    except ValueError:
        return None


async def search_places(query: str, max_results: int = 5) -> PlacesResult | None:
    """Search places via the places MCP tool, or None on failure."""
    return await _invoke("search_places", {"query": query, "max_results": max_results})


async def search_hotels(location: str, max_results: int = 4) -> PlacesResult | None:
    """Find hotels near a location via the places MCP tool, or None on failure."""
    return await _invoke("search_hotels", {"location": location, "max_results": max_results})
