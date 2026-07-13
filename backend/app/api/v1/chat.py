"""Chat WebSocket — the core interaction (PROJECT_PLAN §11).

    WS /ws/trips/{trip_id}/chat
    -> { "type": "user_message", "content": "..." }
    <- streamed events: route_decision, agent_update, partial_itinerary,
       validation_report, assistant_message, complete, error

The trip id is used as the LangGraph thread id, so each trip's conversation
resumes from its checkpoint.
"""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from langchain_core.runnables import RunnableConfig

from app.agents.streaming import complete_event, node_events

router = APIRouter()


async def _run_turn(ws: WebSocket, content: str, config: RunnableConfig) -> None:
    graph = ws.app.state.graph
    try:
        async for chunk in graph.astream(
            {"messages": [{"role": "user", "content": content}]},
            config=config,
            stream_mode="updates",
        ):
            for node, update in chunk.items():
                for event in node_events(node, update):
                    await ws.send_json(event)

        snapshot = await graph.aget_state(config)
        await ws.send_json(complete_event(snapshot.values.get("itinerary")))
    except Exception as exc:  # surface failures to the client, keep socket open
        await ws.send_json({"type": "error", "message": str(exc)})


@router.websocket("/ws/trips/{trip_id}/chat")
async def chat_ws(ws: WebSocket, trip_id: str) -> None:
    await ws.accept()
    config: RunnableConfig = {"configurable": {"thread_id": trip_id}}
    try:
        while True:
            data = await ws.receive_json()
            if data.get("type") != "user_message":
                await ws.send_json({"type": "error", "message": "expected type=user_message"})
                continue
            await _run_turn(ws, data.get("content", ""), config)
    except WebSocketDisconnect:
        return
