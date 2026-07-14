"""Tests for the Synthesizer node — LLM boundary mocked."""

import importlib

import pytest

from app.agents.nodes.synthesizer import synthesizer
from app.schemas.itinerary import Block, Day, Itinerary
from app.schemas.planning import DaySkeleton, ResearchBundle
from app.schemas.trip import TripRequest

_synth_mod = importlib.import_module("app.agents.nodes.synthesizer")


async def test_synthesizer_produces_itinerary(monkeypatch: pytest.MonkeyPatch) -> None:
    itinerary = Itinerary(
        destination="Kerala",
        days=[
            Day(
                day=1,
                blocks=[Block(time="13:00", activity="Lunch", location="cafe", cost_inr=400)],
            )
        ],
        total_cost_inr=400,
    )

    async def _synthesize(
        trip: TripRequest, skeletons: list[DaySkeleton], research: ResearchBundle | None
    ) -> Itinerary:
        return itinerary

    monkeypatch.setattr(_synth_mod, "_synthesize", _synthesize)

    update = await synthesizer(
        {
            "trip_request": TripRequest(destination="Kerala"),
            "day_skeletons": [DaySkeleton(day=1, theme="Fort Kochi")],
        }
    )
    assert update["itinerary"] == itinerary


async def test_synthesizer_no_trip_request_is_noop() -> None:
    assert await synthesizer({}) == {}


async def test_synthesizer_attaches_weather_from_research(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # LLM returns two days; the second carries a hallucinated weather that must
    # be cleared (no forecast for it). Day 1 gets the real forecast.
    from app.schemas.itinerary import Weather

    itinerary = Itinerary(
        destination="Munnar",
        days=[
            Day(day=1, blocks=[Block(time="09:00", activity="Tea", location="estate")]),
            Day(
                day=2,
                blocks=[Block(time="09:00", activity="Falls", location="Attukad")],
                weather=Weather(condition="made up"),
            ),
        ],
    )

    async def _synthesize(
        trip: TripRequest, skeletons: list[DaySkeleton], research: ResearchBundle | None
    ) -> Itinerary:
        return itinerary

    monkeypatch.setattr(_synth_mod, "_synthesize", _synthesize)

    update = await synthesizer(
        {
            "trip_request": TripRequest(destination="Munnar"),
            "day_skeletons": [DaySkeleton(day=1, theme="tea")],
            "research": ResearchBundle(
                weather_by_day={
                    "2026-07-14": {"min_temp_c": 18.0, "max_temp_c": 27.0, "condition": "rain"}
                }
            ),
        }
    )

    days = update["itinerary"].days
    assert days[0].weather == Weather(min_temp_c=18.0, max_temp_c=27.0, condition="rain")
    assert days[1].weather is None  # beyond the forecast window → LLM value cleared


async def test_synthesizer_attaches_travel_and_hotels(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    itinerary = Itinerary(
        destination="Goa",
        days=[Day(day=1, blocks=[Block(time="09:00", activity="Beach", location="Baga")])],
    )

    async def _synthesize(
        trip: TripRequest, skeletons: list[DaySkeleton], research: ResearchBundle | None
    ) -> Itinerary:
        return itinerary

    monkeypatch.setattr(_synth_mod, "_synthesize", _synthesize)

    update = await synthesizer(
        {
            "trip_request": TripRequest(destination="Goa", origin="Hyderabad"),
            "day_skeletons": [DaySkeleton(day=1, theme="beach")],
            "research": ResearchBundle(
                travel_leg={
                    "origin": "Hyderabad",
                    "destination": "Goa",
                    "mode": "driving",
                    "distance_km": 590.0,
                    "duration_min": 660.0,
                },
                hotels=[
                    {"name": "Taj Goa", "area": "Sinquerim", "rating": 4.5},
                    {"area": "no name -> dropped"},
                ],
            ),
        }
    )

    result = update["itinerary"]
    assert result.origin == "Hyderabad"
    assert result.travel is not None and result.travel.distance_km == 590.0
    assert [h.name for h in result.hotels] == ["Taj Goa"]  # nameless hotel dropped
