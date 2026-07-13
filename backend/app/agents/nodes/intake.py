"""Intake — resolves the conversation into a structured TripRequest (§9).

Uses GPT-4o-mini structured output to extract only what the traveller stated.
Date/duration resolution and clarifying `interrupt()` calls for missing
required fields are added when the chat/WebSocket turn machinery lands.

The LLM call is isolated in `_extract` so tests can mock the boundary.
"""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AnyMessage

from app.agents.prompts.intake import INTAKE_SYSTEM_PROMPT
from app.agents.state import ConversationState
from app.config import get_settings
from app.core.llm import parse_structured
from app.schemas.trip import IntakeExtraction, TripRequest

_ROLE_BY_TYPE = {"human": "user", "ai": "assistant", "system": "system"}


def _to_openai_messages(messages: list[AnyMessage]) -> list[dict[str, str]]:
    """Convert LangChain messages to OpenAI chat format, keeping only text."""
    converted: list[dict[str, str]] = []
    for message in messages:
        role = _ROLE_BY_TYPE.get(message.type, "user")
        content = message.content
        if isinstance(content, str) and content:
            converted.append({"role": role, "content": content})
    return converted


async def _extract(messages: list[AnyMessage]) -> IntakeExtraction:
    """Call the LLM to extract trip fields from the conversation so far."""
    oai_messages = [
        {"role": "system", "content": INTAKE_SYSTEM_PROMPT},
        *_to_openai_messages(messages),
    ]
    result = await parse_structured(
        get_settings().model_router, oai_messages, IntakeExtraction
    )
    return result or IntakeExtraction()


async def intake(state: ConversationState) -> dict[str, Any]:
    # Already resolved on an earlier turn — nothing to do.
    if state.get("trip_request") is not None:
        return {}

    extraction = await _extract(state.get("messages", []))
    trip = TripRequest(
        destination=extraction.destination,
        duration_days=extraction.duration_days,
        budget_inr=extraction.budget_inr,
        party_size=extraction.party_size,
        preferences=extraction.preferences,
    )
    return {"trip_request": trip}
