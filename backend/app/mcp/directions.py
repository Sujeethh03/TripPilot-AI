"""Helper for calling the directions MCP tool from agent code.

Agents reach routing only through the MCP pool (never the upstream API). This
wraps the tool call and parses its result into the tool's declared contract,
defensively — a failed tool call yields None, not a crash.
"""

from __future__ import annotations

from app.mcp.client_pool import get_tools
from app.mcp.weather import _extract_text  # shared MCP result unwrapping
from mcp_servers.directions.schemas import DirectionsResult

_TOOL = "get_directions"


async def get_directions(
    origin: str, destination: str, mode: str = "driving"
) -> DirectionsResult | None:
    """Get travel distance/time via the directions MCP tool, or None on failure."""
    tools = {tool.name: tool for tool in await get_tools()}
    tool = tools.get(_TOOL)
    if tool is None:
        return None
    try:
        raw = await tool.ainvoke(
            {"origin": origin, "destination": destination, "mode": mode}
        )
    except Exception:
        return None

    text = _extract_text(raw)
    if text is None:
        return None
    try:
        return DirectionsResult.model_validate_json(text)
    except ValueError:
        return None
