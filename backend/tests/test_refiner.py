"""Tests for the Refiner node — LLM boundary mocked."""

import importlib

import pytest

from app.agents.nodes.refiner import refiner
from app.schemas.itinerary import Block, Day, Itinerary
from app.schemas.planning import ValidationReport

_refiner_mod = importlib.import_module("app.agents.nodes.refiner")


async def test_refiner_revises_and_increments(monkeypatch: pytest.MonkeyPatch) -> None:
    revised = Itinerary(
        destination="Kerala",
        days=[Day(day=1, blocks=[Block(time="10:00", activity="Beach", location="Kovalam")])],
    )

    async def _refine(itinerary, validation, messages) -> Itinerary:
        return revised

    monkeypatch.setattr(_refiner_mod, "_refine", _refine)

    update = await refiner(
        {
            "itinerary": Itinerary(destination="Kerala"),
            "validation": ValidationReport(is_valid=False),
            "refinement_count": 0,
            "messages": [],
        }
    )
    assert update["itinerary"] == revised
    assert update["refinement_count"] == 1


async def test_refiner_without_itinerary_just_counts() -> None:
    update = await refiner({"refinement_count": 1})
    assert update == {"refinement_count": 2}
    assert "itinerary" not in update
