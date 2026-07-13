"""Directions MCP server (FastMCP).

Exposes point-to-point routing as an MCP tool. Run standalone with:
    python -m mcp_servers.directions
"""

from __future__ import annotations

from fastmcp import FastMCP

from mcp_servers.directions.google_directions import GoogleDirectionsClient
from mcp_servers.directions.schemas import DirectionsResult

mcp: FastMCP = FastMCP("directions")
_client = GoogleDirectionsClient()


@mcp.tool
async def get_directions(
    origin: str, destination: str, mode: str = "driving"
) -> DirectionsResult:
    """Get travel distance and time between two places.

    Args:
        origin: Start location, e.g. "Kochi, Kerala".
        destination: End location, e.g. "Munnar, Kerala".
        mode: driving | walking | transit | bicycling (default driving).
    """
    return await _client.directions(origin, destination, mode)
