"""MCP server registry.

Maps each MCP server name to its connection config for the client pool. For
MVP every server runs in-process as a stdio subprocess (PROJECT_PLAN §12);
switching one to HTTP transport later is a change here only, not in agent code.

The stdio transport starts each server with a sanitized environment, so any
secret a server needs must be passed to it explicitly here — and only the ones
it needs (least privilege, §5.7 #3).
"""

from __future__ import annotations

import os
import sys
from typing import Any

from app.config import get_settings

# Non-secret vars a subprocess needs to run correctly (interpreter discovery,
# locale, TLS trust store). No API keys here.
_SAFE_ENV_KEYS = (
    "PATH",
    "HOME",
    "LANG",
    "LC_ALL",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "VIRTUAL_ENV",
)


def _base_env() -> dict[str, str]:
    return {key: os.environ[key] for key in _SAFE_ENV_KEYS if key in os.environ}


def server_registry() -> dict[str, dict[str, Any]]:
    """Return the MCP servers the client pool should connect to.

    Add a new server by listing its `python -m mcp_servers.<name>` entrypoint
    and any secret it requires in `env`.
    """
    settings = get_settings()
    python = sys.executable
    return {
        "weather": {
            "command": python,
            "args": ["-m", "mcp_servers.weather"],
            "transport": "stdio",
            "env": {**_base_env(), "OPENWEATHER_KEY": settings.openweather_key},
        },
    }
