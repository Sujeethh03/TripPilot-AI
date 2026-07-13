"""ConversationState — the typed state threaded through the LangGraph graph.

Design (PROJECT_PLAN §9): structured state, not raw messages. Each node reads
and writes typed fields; the message log is a separate, append-only channel.
State is treated as immutable — nodes return partial updates, never mutate.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

from app.schemas.itinerary import Itinerary
from app.schemas.planning import DaySkeleton, ResearchBundle, ValidationReport
from app.schemas.trip import TripRequest

# Bounded refinement loop (§9: "max 2 refinement iterations, then ship").
MAX_REFINEMENTS = 2


class Route(StrEnum):
    """Where the Conversation Manager sends a turn."""

    CHIT_CHAT = "chit_chat"
    CLARIFY = "clarify"
    PLAN = "plan"
    REFINE = "refine"


class ConversationState(TypedDict, total=False):
    """Full state for one conversation thread, persisted per checkpoint.

    `total=False`: every field is optional, populated as the graph progresses.
    """

    # Append-only message log (reducer merges updates by id).
    messages: Annotated[list[AnyMessage], add_messages]

    # Routing decision for the current turn.
    route: str

    # Structured planning artifacts, filled in order by the pipeline.
    trip_request: TripRequest | None
    day_skeletons: list[DaySkeleton] | None
    research: ResearchBundle | None
    itinerary: Itinerary | None
    validation: ValidationReport | None

    # How many times the Refiner has run this turn (bounds the loop).
    refinement_count: int
