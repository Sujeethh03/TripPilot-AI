"""Synthesizer — assembles the Itinerary (§9).

GPT-4o combines TripRequest + DaySkeleton[] + ResearchBundle into the canonical
Itinerary via strict structured output. It prefers grounded research data and
avoids inventing facts when research is absent. The LLM call is isolated in
`_synthesize` for testing.
"""

from __future__ import annotations

import json
from typing import Any

from app.agents.prompts.synthesizer import SYNTHESIZER_SYSTEM_PROMPT
from app.agents.state import ConversationState
from app.config import get_settings
from app.core.llm import parse_structured
from app.schemas.itinerary import Itinerary
from app.schemas.planning import DaySkeleton, ResearchBundle
from app.schemas.trip import TripRequest


async def _synthesize(
    trip: TripRequest,
    skeletons: list[DaySkeleton],
    research: ResearchBundle | None,
) -> Itinerary:
    payload = {
        "trip_request": trip.model_dump(mode="json"),
        "day_skeletons": [s.model_dump() for s in skeletons],
        "research": (research or ResearchBundle()).model_dump(mode="json"),
    }
    messages = [
        {"role": "system", "content": SYNTHESIZER_SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(payload)},
    ]
    result = await parse_structured(get_settings().model_planner, messages, Itinerary)
    return result or Itinerary(destination=trip.destination or "TBD")


async def synthesizer(state: ConversationState) -> dict[str, Any]:
    trip = state.get("trip_request")
    if trip is None:
        return {}
    itinerary = await _synthesize(
        trip,
        state.get("day_skeletons") or [],
        state.get("research"),
    )
    return {"itinerary": itinerary}
