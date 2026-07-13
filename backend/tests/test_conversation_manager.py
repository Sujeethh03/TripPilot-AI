"""Tests for the Conversation Manager node — LLM boundary mocked."""

import importlib

import pytest

from app.agents.nodes.conversation_manager import RouteDecision, conversation_manager
from app.agents.state import Route
from app.schemas.itinerary import Itinerary

_cm_mod = importlib.import_module("app.agents.nodes.conversation_manager")


def _mock_route(decision: RouteDecision):
    async def _route(messages: list, *, has_itinerary: bool) -> RouteDecision:
        return decision

    return _route


async def test_chit_chat_appends_message(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        _cm_mod, "_route", _mock_route(RouteDecision(route=Route.CHIT_CHAT, message="Hi there!"))
    )
    update = await conversation_manager({"messages": []})
    assert update["route"] == Route.CHIT_CHAT.value
    assert update["refinement_count"] == 0
    assert update["messages"] == [{"role": "assistant", "content": "Hi there!"}]


async def test_plan_route_has_no_message(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(_cm_mod, "_route", _mock_route(RouteDecision(route=Route.PLAN)))
    update = await conversation_manager({"messages": []})
    assert update["route"] == Route.PLAN.value
    assert "messages" not in update


async def test_refine_only_considered_with_itinerary(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, bool] = {}

    async def _route(messages: list, *, has_itinerary: bool) -> RouteDecision:
        seen["has_itinerary"] = has_itinerary
        return RouteDecision(route=Route.REFINE)

    monkeypatch.setattr(_cm_mod, "_route", _route)
    await conversation_manager({"messages": [], "itinerary": Itinerary(destination="Goa")})
    assert seen["has_itinerary"] is True
