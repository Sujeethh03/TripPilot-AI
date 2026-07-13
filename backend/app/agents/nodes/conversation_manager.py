"""Conversation Manager — the router (PROJECT_PLAN §9).

Real contract: reads the user message + full state and decides the route
(chit_chat | clarify | plan | refine) via GPT-4o-mini structured output;
answers chit-chat inline.

Stub: deterministic heuristic — refine if an itinerary already exists,
otherwise plan. No LLM. Lets the graph run and be tested end-to-end.
"""

from __future__ import annotations

from typing import Any

from app.agents.state import ConversationState, Route


def conversation_manager(state: ConversationState) -> dict[str, Any]:
    # TODO: replace heuristic with GPT-4o-mini structured-output classifier.
    route = Route.REFINE if state.get("itinerary") else Route.PLAN
    return {"route": route.value}
