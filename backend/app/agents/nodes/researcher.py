"""Researcher — gathers real data via MCP tools (§9).

Real contract: NO LLM. Parallel MCP calls to places / weather / directions /
buses, aggressively cached in Redis, aggregated into a ResearchBundle.

Stub: returns an empty ResearchBundle.
"""

from __future__ import annotations

from typing import Any

from app.agents.state import ConversationState
from app.schemas.planning import ResearchBundle


def researcher(state: ConversationState) -> dict[str, Any]:
    # TODO: fan out to the MCP client pool (places/weather/directions/buses).
    return {"research": ResearchBundle()}
