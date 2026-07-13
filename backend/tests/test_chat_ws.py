"""Integration test for the chat WebSocket (LLM boundaries mocked)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

pytestmark = pytest.mark.usefixtures("mock_agent_llms")


def _drain(ws) -> list[dict]:
    events = []
    while True:
        event = ws.receive_json()
        events.append(event)
        if event["type"] in ("complete", "error"):
            return events


def test_plan_turn_streams_events() -> None:
    with TestClient(app) as client, client.websocket_connect("/ws/trips/ws-1/chat") as ws:
        ws.send_json({"type": "user_message", "content": "5 days kerala 20k"})
        events = _drain(ws)

    types = [e["type"] for e in events]
    assert "route_decision" in types
    assert "validation_report" in types
    assert types[-1] == "complete"

    complete = events[-1]
    assert complete["itinerary"]["destination"] == "Kerala"


def test_bad_message_type_errors_without_closing() -> None:
    with TestClient(app) as client, client.websocket_connect("/ws/trips/ws-2/chat") as ws:
        ws.send_json({"type": "nonsense"})
        err = ws.receive_json()
        assert err["type"] == "error"

        # Socket still usable for a valid turn afterwards.
        ws.send_json({"type": "user_message", "content": "plan kerala"})
        events = _drain(ws)
        assert events[-1]["type"] == "complete"
