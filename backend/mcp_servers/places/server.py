"""Places MCP server (FastMCP).

Exposes place search as an MCP tool. Run standalone with:
    python -m mcp_servers.places
"""

from __future__ import annotations

from fastmcp import FastMCP

from mcp_servers.places.google_places import GooglePlacesClient
from mcp_servers.places.schemas import PlacesResult

mcp: FastMCP = FastMCP("places")
_client = GooglePlacesClient()


@mcp.tool
async def search_places(query: str, max_results: int = 5) -> PlacesResult:
    """Search for points of interest matching a free-text query.

    Args:
        query: What to look for, e.g. "waterfalls near Munnar" or
            "street food in Fort Kochi".
        max_results: Maximum number of places to return (1-20).
    """
    return await _client.search(query, max_results=max_results)


@mcp.tool
async def search_hotels(location: str, max_results: int = 4) -> PlacesResult:
    """Find hotels / places to stay near a location.

    Args:
        location: Where to stay, e.g. "Munnar" or "Fort Kochi".
        max_results: Maximum number of hotels to return (1-20).
    """
    return await _client.search_hotels(location, max_results=max_results)
