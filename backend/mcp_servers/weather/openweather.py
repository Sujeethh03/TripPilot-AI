"""OpenWeatherMap adapter for the weather MCP server.

Uses the free "5 day / 3 hour forecast" endpoint and aggregates the 3-hourly
entries into per-day summaries. Parsing is defensive (PROJECT_PLAN §5.1 #11):
upstream JSON is assumed to be possibly malformed.
"""

from __future__ import annotations

import os
from collections import defaultdict
from typing import Any

import httpx

from mcp_servers.weather.schemas import DailyForecast, ForecastResult

_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


class WeatherError(RuntimeError):
    """Raised when the upstream weather provider fails or is misconfigured."""


class OpenWeatherClient:
    """Thin async client over the OpenWeatherMap forecast API.

    An httpx client may be injected for testing; otherwise one is created per
    call. The API key defaults to the OPENWEATHER_KEY environment variable.
    """

    def __init__(
        self,
        api_key: str | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key if api_key is not None else os.getenv("OPENWEATHER_KEY", "")
        self._http = http_client

    async def forecast(self, city: str, days: int = 5) -> ForecastResult:
        if not self._api_key:
            raise WeatherError("OPENWEATHER_KEY is not set")

        params = {"q": city, "units": "metric", "appid": self._api_key}
        try:
            if self._http is not None:
                resp = await self._http.get(_FORECAST_URL, params=params)
            else:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(_FORECAST_URL, params=params)
            resp.raise_for_status()
            payload: Any = resp.json()
        except httpx.HTTPError as exc:
            raise WeatherError(f"weather request failed: {exc}") from exc

        resolved_city = _safe_city_name(payload, fallback=city)
        daily = _aggregate_daily(payload)
        return ForecastResult(city=resolved_city, days=daily[:days])


def _safe_city_name(payload: Any, fallback: str) -> str:
    if isinstance(payload, dict):
        city = payload.get("city")
        if isinstance(city, dict):
            name = city.get("name")
            if isinstance(name, str):
                return name
    return fallback


def _aggregate_daily(payload: Any) -> list[DailyForecast]:
    """Collapse 3-hourly entries into one summary per calendar day."""
    entries = payload.get("list") if isinstance(payload, dict) else None
    if not isinstance(entries, list):
        return []

    by_date: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        dt_txt = entry.get("dt_txt")
        if not isinstance(dt_txt, str) or " " not in dt_txt:
            continue
        by_date[dt_txt.split(" ", 1)[0]].append(entry)

    result: list[DailyForecast] = []
    for date in sorted(by_date):
        day_entries = by_date[date]
        temps = [t for e in day_entries if (t := _temp(e)) is not None]
        if not temps:
            continue
        result.append(
            DailyForecast(
                date=date,
                min_temp_c=round(min(temps), 1),
                max_temp_c=round(max(temps), 1),
                condition=_midday_condition(day_entries),
            )
        )
    return result


def _temp(entry: dict[str, Any]) -> float | None:
    main = entry.get("main")
    if isinstance(main, dict) and isinstance(main.get("temp"), (int, float)):
        return float(main["temp"])
    return None


def _midday_condition(day_entries: list[dict[str, Any]]) -> str:
    """Pick the condition from the entry closest to noon, else the first."""

    def hour(entry: dict[str, Any]) -> int:
        dt_txt = entry.get("dt_txt", "")
        if isinstance(dt_txt, str) and " " in dt_txt:
            try:
                return int(dt_txt.split(" ", 1)[1][:2])
            except ValueError:
                return 99
        return 99

    chosen = min(day_entries, key=lambda e: abs(hour(e) - 12))
    weather = chosen.get("weather")
    if isinstance(weather, list) and weather and isinstance(weather[0], dict):
        desc = weather[0].get("description")
        if isinstance(desc, str):
            return desc
    return "unknown"
