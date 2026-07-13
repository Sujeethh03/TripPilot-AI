"""Graph runs end-to-end. Intake's LLM boundary is mocked; other nodes are
still stubs (no network, no key)."""

import importlib

import pytest
from langgraph.checkpoint.memory import MemorySaver

from app.agents.graph import build_graph
from app.agents.nodes.conversation_manager import RouteDecision
from app.agents.state import Route
from app.schemas.itinerary import Block, Day, Itinerary
from app.schemas.planning import DaySkeleton
from app.schemas.trip import IntakeExtraction, TripRequest

# The re-exported node functions shadow their submodules; fetch the modules.
_cm_mod = importlib.import_module("app.agents.nodes.conversation_manager")
_intake_mod = importlib.import_module("app.agents.nodes.intake")
_planner_mod = importlib.import_module("app.agents.nodes.planner")
_synth_mod = importlib.import_module("app.agents.nodes.synthesizer")
_refiner_mod = importlib.import_module("app.agents.nodes.refiner")


def _valid_itinerary() -> Itinerary:
    return Itinerary(
        destination="Kerala",
        days=[
            Day(
                day=1,
                blocks=[
                    Block(time="09:00", activity="Fort Kochi walk", location="Fort Kochi"),
                    Block(time="13:00", activity="Lunch", location="cafe", cost_inr=400),
                ],
            )
        ],
        total_cost_inr=400,
    )


@pytest.fixture(autouse=True)
def _mock_llm_nodes(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub every LLM boundary so the graph runs with no key/network."""

    async def _route(messages: list, *, has_itinerary: bool) -> RouteDecision:
        return RouteDecision(route=Route.REFINE if has_itinerary else Route.PLAN)

    async def _extract(messages: list) -> IntakeExtraction:
        return IntakeExtraction(destination="Kerala", duration_days=1, budget_inr=20000)

    async def _plan(trip: TripRequest) -> list[DaySkeleton]:
        return [DaySkeleton(day=1, theme="Fort Kochi", meal_slots=["lunch"])]

    async def _synthesize(trip, skeletons, research) -> Itinerary:
        return _valid_itinerary()

    async def _refine(itinerary, validation, messages) -> Itinerary:
        return _valid_itinerary()

    monkeypatch.setattr(_cm_mod, "_route", _route)
    monkeypatch.setattr(_intake_mod, "_extract", _extract)
    monkeypatch.setattr(_planner_mod, "_plan", _plan)
    monkeypatch.setattr(_synth_mod, "_synthesize", _synthesize)
    monkeypatch.setattr(_refiner_mod, "_refine", _refine)


def _config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


async def test_plan_flow_produces_itinerary() -> None:
    graph = build_graph(MemorySaver())
    result = await graph.ainvoke(
        {"messages": [{"role": "user", "content": "5 days kerala, 20k"}]},
        _config("t1"),
    )

    assert result["route"] == Route.PLAN.value
    assert result["trip_request"].destination == "Kerala"
    itinerary = result["itinerary"]
    assert isinstance(itinerary, Itinerary)
    assert result["validation"].is_valid is True


async def test_second_turn_routes_to_refine() -> None:
    graph = build_graph(MemorySaver())
    cfg = _config("t2")

    await graph.ainvoke({"messages": [{"role": "user", "content": "plan kerala"}]}, cfg)
    # Same thread -> checkpoint carries the itinerary -> router picks refine.
    result = await graph.ainvoke(
        {"messages": [{"role": "user", "content": "skip day 3"}]}, cfg
    )

    assert result["route"] == Route.REFINE.value
    assert result["refinement_count"] == 1
