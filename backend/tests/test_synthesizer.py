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
