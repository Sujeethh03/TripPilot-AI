"""Translate LangGraph node updates into WebSocket stream events (§11).

Kept separate from the transport (FastAPI WebSocket) so the mapping is pure and
unit-testable. Each function returns plain JSON-serialisable dicts.
"""

from __future__ import annotations

from typing import Any

from app.schemas.itinerary import Itinerary
from app.schemas.planning import ValidationReport


def _dump_itinerary(itinerary: Any) -> dict[str, Any] | None:
    return itinerary.model_dump(mode="json") if isinstance(itinerary, Itinerary) else None


def _assistant_text(messages: Any) -> str | None:
    """Return the latest assistant message text from a node's message update."""
    for message in reversed(messages or []):
        if isinstance(message, dict):
            role, content = message.get("role"), message.get("content")
        else:
            role, content = getattr(message, "type", None), getattr(message, "content", None)
        if content and role in ("assistant", "ai"):
            return content if isinstance(content, str) else None
    return None


def node_events(node: str, update: dict[str, Any]) -> list[dict[str, Any]]:
    """Map one node's state update to zero or more client events."""
    if node == "conversation_manager":
        events: list[dict[str, Any]] = []
        if "route" in update:
            events.append({"type": "route_decision", "route": update["route"]})
        text = _assistant_text(update.get("messages"))
        if text:
            events.append({"type": "assistant_message", "content": text})
        return events

    if node == "intake":
        return [{"type": "agent_update", "agent": "intake", "detail": "understood the request"}]

    if node == "planner":
        count = len(update.get("day_skeletons") or [])
        return [{"type": "agent_update", "agent": "planner", "detail": f"drafted {count} day(s)"}]

    if node == "researcher":
        return [{"type": "agent_update", "agent": "researcher", "detail": "gathered live data"}]

    if node == "synthesizer":
        return [
            {
                "type": "partial_itinerary",
                "agent": "synthesizer",
                "data": _dump_itinerary(update.get("itinerary")),
            }
        ]

    if node == "validator":
        report = update.get("validation")
        if isinstance(report, ValidationReport):
            return [
                {
                    "type": "validation_report",
                    "is_valid": report.is_valid,
                    "issues": [issue.model_dump() for issue in report.issues],
                }
            ]
        return []

    if node == "refiner":
        itinerary = update.get("itinerary")
        if itinerary is not None:
            return [
                {
                    "type": "partial_itinerary",
                    "agent": "refiner",
                    "data": _dump_itinerary(itinerary),
                }
            ]
        return []

    return []


def complete_event(itinerary: Any) -> dict[str, Any]:
    return {"type": "complete", "itinerary": _dump_itinerary(itinerary)}
