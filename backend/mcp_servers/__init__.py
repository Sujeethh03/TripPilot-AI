"""Standalone MCP tool servers (PROJECT_PLAN §8).

Each server wraps one external API and is runnable in isolation via
`python -m mcp_servers.<name>`. Agents never import these directly — they
reach them only through the MCP client pool.
"""
