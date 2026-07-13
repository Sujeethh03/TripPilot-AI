"""Validator — deterministic feasibility checks (§9, §5.12).

Real contract: NO LLM. Plain Python rules — opening hours, drive-time
realism, budget fit (+10% buffer), meal slots present, pacing not too dense.
The Validator is the source of truth for facts; the LLM is only a suggestion
engine.

Stub: passes everything. The real rule set is built out in the Validator task.
"""

from __future__ import annotations

from typing import Any

from app.agents.state import ConversationState
from app.schemas.planning import ValidationReport


def validator(state: ConversationState) -> dict[str, Any]:
    # TODO: implement deterministic rule checks against itinerary + research.
    return {"validation": ValidationReport(is_valid=True)}
