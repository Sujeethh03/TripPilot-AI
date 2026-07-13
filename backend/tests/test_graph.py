"""Graph runs end-to-end with all LLM/tool boundaries mocked (no key/network)."""

import pytest
from langgraph.checkpoint.memory import MemorySaver

from app.agents.graph import build_graph
from app.agents.state import Route
from app.schemas.itinerary import Itinerary

pytestmark = pytest.mark.usefixtures("mock_agent_llms")


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
    assert isinstance(result["itinerary"], Itinerary)
    assert result["validation"].is_valid is True


async def test_second_turn_routes_to_refine() -> None:
    graph = build_graph(MemorySaver())
    cfg = _config("t2")

    await graph.ainvoke({"messages": [{"role": "user", "content": "plan kerala"}]}, cfg)
    result = await graph.ainvoke(
        {"messages": [{"role": "user", "content": "skip day 3"}]}, cfg
    )

    assert result["route"] == Route.REFINE.value
    assert result["refinement_count"] == 1
