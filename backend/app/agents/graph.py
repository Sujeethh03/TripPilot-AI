"""LangGraph conversational graph definition (PROJECT_PLAN §4, §9).

Flow:
    START -> conversation_manager
        chit_chat | clarify -> END
        plan               -> intake -> planner -> researcher
                              -> synthesizer -> validator
        refine             -> refiner
    validator -> (refiner if invalid and under the loop cap, else END)
    refiner   -> validator

The planning pipeline is linear with a bounded validation/refine loop
(max MAX_REFINEMENTS iterations, then ship).
"""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agents.checkpointer import get_checkpointer
from app.agents.nodes import (
    conversation_manager,
    intake,
    planner,
    refiner,
    researcher,
    synthesizer,
    validator,
)
from app.agents.state import MAX_REFINEMENTS, ConversationState, Route


def _route_after_manager(state: ConversationState) -> str:
    """Dispatch on the Conversation Manager's routing decision."""
    route = state.get("route")
    if route == Route.PLAN.value:
        return "plan"
    if route == Route.REFINE.value:
        return "refine"
    return "end"  # chit_chat / clarify both exit this turn


def _route_after_validator(state: ConversationState) -> str:
    """Loop back to the Refiner only if invalid and under the iteration cap."""
    report = state.get("validation")
    count = state.get("refinement_count", 0)
    if report is not None and not report.is_valid and count < MAX_REFINEMENTS:
        return "refine"
    return "end"


def build_graph(
    checkpointer: BaseCheckpointSaver[Any] | None = None,
) -> CompiledStateGraph[ConversationState, Any, Any, Any]:
    """Assemble and compile the conversational graph."""
    builder = StateGraph(ConversationState)

    builder.add_node("conversation_manager", conversation_manager)
    builder.add_node("intake", intake)
    builder.add_node("planner", planner)
    builder.add_node("researcher", researcher)
    builder.add_node("synthesizer", synthesizer)
    builder.add_node("validator", validator)
    builder.add_node("refiner", refiner)

    builder.add_edge(START, "conversation_manager")
    builder.add_conditional_edges(
        "conversation_manager",
        _route_after_manager,
        {"plan": "intake", "refine": "refiner", "end": END},
    )

    # Planning pipeline.
    builder.add_edge("intake", "planner")
    builder.add_edge("planner", "researcher")
    builder.add_edge("researcher", "synthesizer")
    builder.add_edge("synthesizer", "validator")

    # Bounded validation/refine loop.
    builder.add_conditional_edges(
        "validator",
        _route_after_validator,
        {"refine": "refiner", "end": END},
    )
    builder.add_edge("refiner", "validator")

    return builder.compile(checkpointer=checkpointer or get_checkpointer())
