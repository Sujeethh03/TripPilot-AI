"""Checkpointer factory.

LangGraph checkpoints ARE our conversation memory (PROJECT_PLAN §5.9, §10).
For local dev we use an in-memory saver; a Postgres-backed saver replaces it
once the database is stood up — nothing else in the graph needs to change.
"""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver


def get_checkpointer() -> BaseCheckpointSaver[Any]:
    """Return the checkpointer for the current environment.

    TODO: swap to langgraph-checkpoint-postgres (PostgresSaver) once the DB is
    available; keep this the single place that decision is made.
    """
    return MemorySaver()
