"""Helper for calling the directions MCP tool from agent code.

Agents reach routing only through the MCP pool (never the upstream API). This
wraps the tool call and parses its result into the tool's declared contract,
defensively — a failed tool call yields None, not a crash.
"""

from __future__ import annotations

from app.mcp.client_pool import call_tool
from mcp_servers.directions.schemas import DirectionsResult

_SERVER = "directions"
_TOOL = "get_directions"


async def get_directions(
    origin: str, destination: str, mode: str = "driving"
) -> DirectionsResult | None:
    """Get travel distance/time via the directions MCP tool, or None on failure."""
    text = await call_tool(
        _SERVER, _TOOL, {"origin": origin, "destination": destination, "mode": mode}
    )
    if text is None:
        return None
    try:
        return DirectionsResult.model_validate_json(text)
    except ValueError:
        return None
