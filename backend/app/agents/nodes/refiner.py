"""Refiner — revises an itinerary from validation issues or user feedback (§9).

Real contract: GPT-4o produces a revised Itinerary and streams the diff to the
frontend. Entered either from the validation loop (fix feasibility issues) or
directly from the router on a user "refine" turn.

Stub: increments the refinement counter and passes the itinerary through
unchanged, so the bounded loop terminates cleanly.
"""

from __future__ import annotations

from typing import Any

from app.agents.state import ConversationState


def refiner(state: ConversationState) -> dict[str, Any]:
    # TODO: GPT-4o revision; stream the diff over WebSocket.
    return {"refinement_count": state.get("refinement_count", 0) + 1}
