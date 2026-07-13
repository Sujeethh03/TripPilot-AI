"""Unit tests for node-update → WebSocket-event translation."""

from app.agents.streaming import complete_event, node_events
from app.schemas.itinerary import Block, Day, Itinerary
from app.schemas.planning import ValidationIssue, ValidationReport


def test_conversation_manager_route_and_message() -> None:
    update = {"route": "chit_chat", "messages": [{"role": "assistant", "content": "Hi!"}]}
    events = node_events("conversation_manager", update)
    assert {"type": "route_decision", "route": "chit_chat"} in events
    assert {"type": "assistant_message", "content": "Hi!"} in events


def test_synthesizer_emits_partial_itinerary() -> None:
    day = Day(day=1, blocks=[Block(time="09:00", activity="x", location="y")])
    itin = Itinerary(destination="Goa", days=[day])
    events = node_events("synthesizer", {"itinerary": itin})
    assert events[0]["type"] == "partial_itinerary"
    assert events[0]["data"]["destination"] == "Goa"


def test_validator_emits_report() -> None:
    report = ValidationReport(is_valid=False, issues=[ValidationIssue(code="x", message="m")])
    events = node_events("validator", {"validation": report})
    assert events[0]["type"] == "validation_report"
    assert events[0]["is_valid"] is False
    assert events[0]["issues"][0]["code"] == "x"


def test_planner_reports_day_count() -> None:
    from app.schemas.planning import DaySkeleton

    events = node_events("planner", {"day_skeletons": [DaySkeleton(day=1, theme="t")]})
    assert events[0] == {"type": "agent_update", "agent": "planner", "detail": "drafted 1 day(s)"}


def test_complete_event_serializes_itinerary() -> None:
    itin = Itinerary(destination="Goa")
    assert complete_event(itin)["itinerary"]["destination"] == "Goa"
    assert complete_event(None)["itinerary"] is None
