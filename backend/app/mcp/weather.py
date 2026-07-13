"""Helper for calling the weather MCP tool from agent code.

Agents reach weather only through the MCP pool (never the upstream API). This
wraps the tool call and parses its result into the tool's declared contract,
defensively — a failed tool call (e.g. missing key) yields None, not a crash.
"""

from __future__ import annotations

from typing import Any

from app.mcp.client_pool import get_tools
from mcp_servers.weather.schemas import ForecastResult

_TOOL = "get_forecast"


def _extract_text(raw: Any) -> str | None:
    """Pull the JSON text out of an MCP tool result (string or content blocks)."""
    if isinstance(raw, str):
        return raw
    if isinstance(raw, list):
        for block in raw:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text")
                if isinstance(text, str):
                    return text
    return None


async def fetch_forecast(city: str, days: int = 5) -> ForecastResult | None:
    """Return the forecast for a city via the weather MCP tool, or None."""
    tools = {tool.name: tool for tool in await get_tools()}
    tool = tools.get(_TOOL)
    if tool is None:
        return None
    try:
        raw = await tool.ainvoke({"city": city, "days": days})
    except Exception:
        return None

    text = _extract_text(raw)
    if text is None:
        return None
    try:
        return ForecastResult.model_validate_json(text)
    except ValueError:
        return None  # tool returned an error message, not a forecast
