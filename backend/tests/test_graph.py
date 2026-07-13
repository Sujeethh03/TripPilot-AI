"""Skeleton graph runs end-to-end with stub nodes (no LLM, no MCP)."""

from langgraph.checkpoint.memory import MemorySaver

from app.agents.graph import build_graph
from app.agents.state import Route
from app.schemas.itinerary import Itinerary


def _config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def test_plan_flow_produces_itinerary() -> None:
    graph = build_graph(MemorySaver())
    result = graph.invoke(
        {"messages": [{"role": "user", "content": "5 days kerala, 20k"}]},
        _config("t1"),
    )

    assert result["route"] == Route.PLAN.value
    itinerary = result["itinerary"]
    assert isinstance(itinerary, Itinerary)
    assert result["validation"].is_valid is True


def test_second_turn_routes_to_refine() -> None:
    graph = build_graph(MemorySaver())
    cfg = _config("t2")

    graph.invoke({"messages": [{"role": "user", "content": "plan kerala"}]}, cfg)
    # Same thread -> checkpoint carries the itinerary -> router picks refine.
    result = graph.invoke(
        {"messages": [{"role": "user", "content": "skip day 3"}]}, cfg
    )

    assert result["route"] == Route.REFINE.value
    assert result["refinement_count"] == 1
