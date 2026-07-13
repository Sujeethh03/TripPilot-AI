"""Weather MCP server (FastMCP).

Exposes forecast data as an MCP tool. Run standalone with:
    python -m mcp_servers.weather
"""

from __future__ import annotations

from fastmcp import FastMCP

from mcp_servers.weather.openweather import OpenWeatherClient
from mcp_servers.weather.schemas import ForecastResult

mcp: FastMCP = FastMCP("weather")
_client = OpenWeatherClient()


@mcp.tool
async def get_forecast(city: str, days: int = 5) -> ForecastResult:
    """Get the daily weather forecast for a city (up to 5 days ahead).

    Args:
        city: City name, e.g. "Kochi" or "Munnar, IN".
        days: Number of days to return (1-5).
    """
    return await _client.forecast(city, days=max(1, min(days, 5)))
