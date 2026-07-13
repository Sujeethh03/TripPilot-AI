"""Planner — turns a TripRequest into day skeletons (§9).

Real contract: GPT-4o with RAG (pgvector destination knowledge) produces
DaySkeleton[] — themes, target areas, meal slots — before real places exist.

Stub: emits a single empty-themed day skeleton.
"""

from __future__ import annotations

from typing import Any

from app.agents.state import ConversationState
from app.schemas.planning import DaySkeleton


def planner(state: ConversationState) -> dict[str, Any]:
    # TODO: GPT-4o + RAG over destination knowledge base.
    return {"day_skeletons": [DaySkeleton(day=1, theme="TBD")]}
