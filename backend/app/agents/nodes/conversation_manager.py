"""Conversation Manager — the router (PROJECT_PLAN §9).

Classifies each turn (chit_chat | clarify | plan | refine) with GPT-4o-mini and
answers chit-chat / clarifications inline. Resets the per-turn refinement
counter. The LLM call is isolated in `_route` for testing.
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AnyMessage
from pydantic import BaseModel

from app.agents.nodes.intake import _to_openai_messages
from app.agents.prompts.conversation_manager import CONVERSATION_MANAGER_SYSTEM_PROMPT
from app.agents.state import ConversationState, Route
from app.config import get_settings
from app.core.llm import parse_structured


class RouteDecision(BaseModel):
    """LLM output for the router: the chosen route and an optional inline reply."""

    route: Route
    message: str | None = None


async def _route(messages: list[AnyMessage], *, has_itinerary: bool) -> RouteDecision:
    state_text = "already exists" if has_itinerary else "does not exist yet"
    system = CONVERSATION_MANAGER_SYSTEM_PROMPT.format(itinerary_state=state_text)
    oai_messages = [
        {"role": "system", "content": system},
        *_to_openai_messages(messages),
    ]
    result = await parse_structured(get_settings().model_router, oai_messages, RouteDecision)
    return result or RouteDecision(
        route=Route.CLARIFY, message="Could you tell me more about your trip?"
    )


async def conversation_manager(state: ConversationState) -> dict[str, Any]:
    decision = await _route(
        state.get("messages", []),
        has_itinerary=state.get("itinerary") is not None,
    )
    # Reset the refinement counter at the start of every turn (bounds the loop
    # per turn, not per conversation).
    update: dict[str, Any] = {"route": decision.route.value, "refinement_count": 0}
    if decision.message:
        update["messages"] = [{"role": "assistant", "content": decision.message}]
    return update
