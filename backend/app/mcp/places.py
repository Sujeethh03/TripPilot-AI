"""Helper for calling the places MCP tools from agent code.

Agents reach place data only through the MCP pool (never the upstream API).
This wraps the tool call and parses its result into the tool's declared
contract, defensively — a failed tool call yields None, not a crash.
"""

from __future__ import annotations

from app.mcp.client_pool import call_tool
from mcp_servers.places.schemas import PlacesResult

_SERVER = "places"


async def _invoke(tool_name: str, args: dict[str, object]) -> PlacesResult | None:
    text = await call_tool(_SERVER, tool_name, dict(args))
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
