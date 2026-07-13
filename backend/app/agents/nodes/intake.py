"""Intake — resolves the user's request into a structured TripRequest (§9).

Real contract: extract destination/dates/budget/party/preferences via
GPT-4o-mini structured output; call interrupt() to ask for any missing
required field.

Stub: emits a placeholder TripRequest so downstream nodes have something to
consume. No LLM, no clarification.
"""

from __future__ import annotations

from typing import Any

from app.agents.state import ConversationState
from app.schemas.trip import TripRequest


def intake(state: ConversationState) -> dict[str, Any]:
    # TODO: extract from state["messages"] with structured output; interrupt()
    # when a required field is missing/ambiguous.
    existing = state.get("trip_request")
    if existing is not None:
        return {}
    return {"trip_request": TripRequest(destination="TBD")}
