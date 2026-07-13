"""MCP server registry.

Maps each MCP server name to its connection config for the client pool. For
MVP every server runs in-process as a stdio subprocess (PROJECT_PLAN §12);
switching one to HTTP transport later is a change here only, not in agent code.
"""

from __future__ import annotations

import sys
from typing import Any


def server_registry() -> dict[str, dict[str, Any]]:
    """Return the MCP servers the client pool should connect to.

    Add a new server by listing its `python -m mcp_servers.<name>` entrypoint.
    """
    python = sys.executable
    return {
        "weather": {
            "command": python,
            "args": ["-m", "mcp_servers.weather"],
            "transport": "stdio",
        },
    }
