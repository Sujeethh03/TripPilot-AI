"""MCP client pool.

Single entry point through which agents reach every MCP tool
(PROJECT_PLAN §3, §9). Wraps `langchain-mcp-adapters` so MCP tools appear as
LangChain tools bindable to the OpenAI model.
"""

from __future__ import annotations

from typing import Any, cast

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from app.mcp.config import server_registry

_client: MultiServerMCPClient | None = None


def get_client() -> MultiServerMCPClient:
    """Return the process-wide MCP client (singleton)."""
    global _client
    if _client is None:
        # cast: registry values match the adapter's connection TypedDicts.
        _client = MultiServerMCPClient(cast(Any, server_registry()))
    return _client


async def get_tools() -> list[BaseTool]:
    """Discover all tools across the registered MCP servers."""
    return await get_client().get_tools()
