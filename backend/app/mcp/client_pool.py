"""MCP client pool.

Single entry point through which agents reach every MCP tool
(PROJECT_PLAN §3, §9). Wraps `langchain-mcp-adapters` so MCP tools appear as
LangChain tools bindable to the OpenAI model.

Memory note: each MCP server runs as its own Python subprocess (~50 MB), and
the adapter spawns one per call. Two things keep that bounded:

1. Calls are *scoped to one server* — asking the client for every tool spawns
   all four servers just to reach one of them.
2. Concurrent calls are capped, because the Researcher fans out several tool
   calls at once and each one costs a subprocess.

Without both, a single planning turn peaked well past a 512 MB container.
"""

from __future__ import annotations

import asyncio
from typing import Any, cast

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from app.mcp.config import server_registry

_client: MultiServerMCPClient | None = None

# Ceiling on MCP subprocesses alive at once. 2 × ~50 MB leaves room for the
# app (~250 MB) inside a 512 MB instance. Raise this if the host has more RAM.
_MAX_CONCURRENT_CALLS = 2
_slot = asyncio.Semaphore(_MAX_CONCURRENT_CALLS)


def get_client() -> MultiServerMCPClient:
    """Return the process-wide MCP client (singleton)."""
    global _client
    if _client is None:
        # cast: registry values match the adapter's connection TypedDicts.
        _client = MultiServerMCPClient(cast(Any, server_registry()))
    return _client


async def get_tools(server_name: str | None = None) -> list[BaseTool]:
    """Discover tools — for one server, or across all when name is None."""
    return await get_client().get_tools(server_name=server_name)


def _extract_text(raw: Any) -> str | None:
    """Pull the JSON text out of an MCP tool result (string or content blocks)."""
    if isinstance(raw, str):
        return raw
    if isinstance(raw, list):
        for block in raw:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text")
                if isinstance(text, str):
                    return text
    return None


async def call_tool(server_name: str, tool_name: str, args: dict[str, Any]) -> str | None:
    """Invoke one tool on one server and return its raw JSON text, or None.

    Defensive by design: a missing tool or a failed call yields None so a
    degraded tool never breaks the turn. Holds a concurrency slot for the whole
    discover-and-invoke window, since that is when the subprocess is alive.
    """
    async with _slot:
        tools = {tool.name: tool for tool in await get_tools(server_name)}
        tool = tools.get(tool_name)
        if tool is None:
            return None
        try:
            raw = await tool.ainvoke(args)
        except Exception:
            return None
    return _extract_text(raw)
