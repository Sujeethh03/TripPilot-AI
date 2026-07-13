"""Planner — turns a TripRequest into day skeletons (§9).

GPT-4o produces DaySkeleton[] — themes, target areas, meal slots — before any
real places exist. RAG over a destination knowledge base (pgvector) is added
once that store lands. The LLM call is isolated in `_plan` for testing.
"""

from __future__ import annotations

from typing import Any

from app.agents.prompts.planner import PLANNER_SYSTEM_PROMPT
from app.agents.state import ConversationState
from app.config import get_settings
from app.core.llm import parse_structured
from app.schemas.planning import DaySkeleton, DaySkeletonPlan
from app.schemas.trip import TripRequest


async def _plan(trip: TripRequest) -> list[DaySkeleton]:
    messages = [
        {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
        {"role": "user", "content": trip.model_dump_json()},
    ]
    result = await parse_structured(get_settings().model_planner, messages, DaySkeletonPlan)
    return result.days if result else []


async def planner(state: ConversationState) -> dict[str, Any]:
    trip = state.get("trip_request")
    if trip is None:
        return {}
    return {"day_skeletons": await _plan(trip)}
