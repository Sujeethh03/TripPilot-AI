"""Helper for calling the weather MCP tool from agent code.

Agents reach weather only through the MCP pool (never the upstream API). This
wraps the tool call and parses its result into the tool's declared contract,
defensively — a failed tool call (e.g. missing key) yields None, not a crash.
"""

from __future__ import annotations

from app.mcp.client_pool import call_tool
from mcp_servers.weather.schemas import ForecastResult

_SERVER = "weather"
_TOOL = "get_forecast"


async def fetch_forecast(city: str, days: int = 5) -> ForecastResult | None:
    """Return the forecast for a city via the weather MCP tool, or None."""
    text = await call_tool(_SERVER, _TOOL, {"city": city, "days": days})
    if text is None:
        return None
    try:
        return ForecastResult.model_validate_json(text)
    except ValueError:
        return None  # tool returned an error message, not a forecast
