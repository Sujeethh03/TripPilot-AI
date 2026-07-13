"""Validator — deterministic feasibility checks (§9, §5.12).

NO LLM. Delegates to the rule chain in app.agents.validation, which is the
source of truth for facts; the LLM is only a suggestion engine. Rules needing
grounded research data (opening hours, drive times) are added as the
places/directions MCP servers land.
"""

from __future__ import annotations

from typing import Any

from app.agents.state import ConversationState
from app.agents.validation import validate
from app.schemas.planning import ValidationIssue, ValidationReport


def validator(state: ConversationState) -> dict[str, Any]:
    itinerary = state.get("itinerary")
    if itinerary is None:
        report = ValidationReport(
            is_valid=False,
            issues=[
                ValidationIssue(
                    code="no_itinerary",
                    message="No itinerary available to validate",
                    severity="error",
                )
            ],
        )
        return {"validation": report}

    return {"validation": validate(itinerary, state.get("trip_request"))}
