"""Tests for the Planner node — LLM boundary mocked."""

import importlib

import pytest

from app.agents.nodes.planner import planner
from app.schemas.planning import DaySkeleton
from app.schemas.trip import TripRequest

# The re-exported `planner` function shadows the submodule; fetch the module.
_planner_mod = importlib.import_module("app.agents.nodes.planner")


async def test_planner_produces_skeletons(monkeypatch: pytest.MonkeyPatch) -> None:
    skeletons = [
        DaySkeleton(day=1, theme="Fort Kochi", target_areas=["Fort Kochi"], meal_slots=["lunch"]),
        DaySkeleton(day=2, theme="Munnar", target_areas=["Munnar"], meal_slots=["breakfast"]),
    ]

    async def _plan(trip: TripRequest) -> list[DaySkeleton]:
        return skeletons

    monkeypatch.setattr(_planner_mod, "_plan", _plan)

    update = await planner({"trip_request": TripRequest(destination="Kerala", duration_days=2)})
    assert update["day_skeletons"] == skeletons


async def test_planner_no_trip_request_is_noop() -> None:
    assert await planner({}) == {}
