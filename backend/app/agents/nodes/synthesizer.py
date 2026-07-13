"""Synthesizer — assembles the Itinerary (§9).

Real contract: GPT-4o with strict json_schema structured output, combining
TripRequest + DaySkeleton[] + ResearchBundle into the canonical Itinerary.

Stub: builds an empty Itinerary keyed to the requested destination.
"""

from __future__ import annotations

from typing import Any

from app.agents.state import ConversationState
from app.schemas.itinerary import Itinerary


def synthesizer(state: ConversationState) -> dict[str, Any]:
    # TODO: GPT-4o structured output over research + skeletons.
    trip = state.get("trip_request")
    destination = (trip.destination if trip else None) or "TBD"
    return {"itinerary": Itinerary(destination=destination)}
