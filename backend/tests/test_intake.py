"""Tests for the Intake node — LLM boundary is mocked (no network/key)."""

import importlib

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.agents.nodes.intake import _to_openai_messages, intake
from app.schemas.trip import IntakeExtraction, TripRequest

# The `intake` function is re-exported on the nodes package, shadowing the
# `intake` submodule attribute — so fetch the real module to monkeypatch it.
_intake_mod = importlib.import_module("app.agents.nodes.intake")


def _fake_extract(result: IntakeExtraction):
    async def _inner(messages: list) -> IntakeExtraction:
        return result

    return _inner


async def test_intake_maps_extraction_to_trip_request(monkeypatch: pytest.MonkeyPatch) -> None:
    extraction = IntakeExtraction(
        destination="Kerala",
        duration_days=5,
        budget_inr=20000,
        party_size=2,
        preferences=["waterfalls", "street food"],
    )
    monkeypatch.setattr(_intake_mod, "_extract", _fake_extract(extraction))

    update = await intake(
        {"messages": [HumanMessage(content="5 days in kerala, 20k, couple, waterfalls")]}
    )

    trip = update["trip_request"]
    assert isinstance(trip, TripRequest)
    assert trip.destination == "Kerala"
    assert trip.duration_days == 5
    assert trip.budget_inr == 20000
    assert trip.party_size == 2
    assert trip.preferences == ["waterfalls", "street food"]


async def test_intake_skips_when_already_resolved(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    async def _boom(messages: list) -> IntakeExtraction:
        nonlocal called
        called = True
        return IntakeExtraction()

    monkeypatch.setattr(_intake_mod, "_extract", _boom)

    update = await intake({"trip_request": TripRequest(destination="Goa")})

    assert update == {}
    assert called is False


def test_to_openai_messages_maps_roles() -> None:
    messages = [
        HumanMessage(content="hi"),
        AIMessage(content="hello, where to?"),
        HumanMessage(content=""),  # empty content dropped
    ]
    result = _to_openai_messages(messages)
    assert result == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello, where to?"},
    ]
