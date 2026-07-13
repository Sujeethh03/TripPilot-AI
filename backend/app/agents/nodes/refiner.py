"""Refiner — revises an itinerary from validation issues or user feedback (§9).

GPT-4o produces a revised Itinerary. Entered either from the validation loop
(fix feasibility issues) or from the router on a user "refine" turn. Increments
the per-turn refinement counter so the loop stays bounded. The LLM call is
isolated in `_refine` for testing.
"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import AnyMessage

from app.agents.nodes.intake import _to_openai_messages
from app.agents.prompts.refiner import REFINER_SYSTEM_PROMPT
from app.agents.state import ConversationState
from app.config import get_settings
from app.core.llm import parse_structured
from app.schemas.itinerary import Itinerary
from app.schemas.planning import ValidationReport


async def _refine(
    itinerary: Itinerary,
    validation: ValidationReport | None,
    messages: list[AnyMessage],
) -> Itinerary:
    payload = {
        "current_itinerary": itinerary.model_dump(mode="json"),
        "validation_issues": [
            i.model_dump() for i in (validation.issues if validation else [])
        ],
    }
    oai_messages = [
        {"role": "system", "content": REFINER_SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(payload)},
        *_to_openai_messages(messages),
    ]
    result = await parse_structured(get_settings().model_planner, oai_messages, Itinerary)
    return result or itinerary


async def refiner(state: ConversationState) -> dict[str, Any]:
    count = state.get("refinement_count", 0) + 1
    itinerary = state.get("itinerary")
    if itinerary is None:
        return {"refinement_count": count}
    revised = await _refine(itinerary, state.get("validation"), state.get("messages", []))
    return {"itinerary": revised, "refinement_count": count}
