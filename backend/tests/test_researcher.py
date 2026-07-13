"""Tests for the Researcher node and weather helper parsing."""

import importlib

import pytest

from app.agents.nodes.researcher import researcher
from app.mcp.weather import _extract_text
from app.schemas.trip import TripRequest
from mcp_servers.weather.schemas import DailyForecast, ForecastResult

_researcher_mod = importlib.import_module("app.agents.nodes.researcher")


def test_extract_text_from_content_blocks() -> None:
    blocks = [{"type": "text", "text": '{"city":"Kochi","days":[]}'}]
    assert _extract_text(blocks) == '{"city":"Kochi","days":[]}'


def test_extract_text_from_string() -> None:
    assert _extract_text("hello") == "hello"


def test_extract_text_none_on_unexpected() -> None:
    assert _extract_text({"nope": 1}) is None


async def test_researcher_populates_weather(monkeypatch: pytest.MonkeyPatch) -> None:
    forecast = ForecastResult(
        city="Kochi",
        days=[DailyForecast(date="2026-07-14", min_temp_c=25.0, max_temp_c=31.0, condition="rain")],
    )

    async def _fetch(city: str, days: int = 5) -> ForecastResult:
        return forecast

    monkeypatch.setattr(_researcher_mod, "fetch_forecast", _fetch)

    update = await researcher({"trip_request": TripRequest(destination="Kochi")})
    weather = update["research"].weather_by_day
    assert weather["2026-07-14"]["condition"] == "rain"


async def test_researcher_no_destination_is_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _boom(city: str, days: int = 5) -> ForecastResult:
        raise AssertionError("should not be called")

    monkeypatch.setattr(_researcher_mod, "fetch_forecast", _boom)

    update = await researcher({"trip_request": TripRequest()})
    assert update["research"].weather_by_day == {}
