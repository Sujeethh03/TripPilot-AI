"""Unit tests for the OpenWeatherMap adapter — parsing/aggregation logic."""

import httpx
import pytest

from mcp_servers.weather.openweather import OpenWeatherClient, WeatherError


def _entry(dt_txt: str, temp: float, desc: str) -> dict:
    return {"dt_txt": dt_txt, "main": {"temp": temp}, "weather": [{"description": desc}]}


_CANNED = {
    "city": {"name": "Kochi"},
    "list": [
        _entry("2026-07-14 09:00:00", 27.0, "haze"),
        _entry("2026-07-14 12:00:00", 31.5, "light rain"),
        _entry("2026-07-14 18:00:00", 25.0, "clouds"),
        _entry("2026-07-15 12:00:00", 30.0, "clear"),
    ],
}


def _client_with(json_body: dict, status: int = 200) -> tuple[OpenWeatherClient, httpx.AsyncClient]:
    transport = httpx.MockTransport(lambda req: httpx.Response(status, json=json_body))
    http = httpx.AsyncClient(transport=transport)
    return OpenWeatherClient(api_key="test-key", http_client=http), http


async def test_forecast_aggregates_by_day() -> None:
    client, http = _client_with(_CANNED)
    async with http:
        result = await client.forecast("Kochi", days=5)

    assert result.city == "Kochi"
    assert len(result.days) == 2

    day1 = result.days[0]
    assert day1.date == "2026-07-14"
    assert day1.min_temp_c == 25.0
    assert day1.max_temp_c == 31.5
    assert day1.condition == "light rain"  # entry closest to noon


async def test_days_limit_is_respected() -> None:
    client, http = _client_with(_CANNED)
    async with http:
        result = await client.forecast("Kochi", days=1)
    assert len(result.days) == 1


async def test_missing_api_key_raises() -> None:
    client = OpenWeatherClient(api_key="")
    with pytest.raises(WeatherError):
        await client.forecast("Kochi")


async def test_malformed_payload_yields_no_days() -> None:
    client, http = _client_with({"unexpected": "shape"})
    async with http:
        result = await client.forecast("Kochi")
    assert result.days == []
