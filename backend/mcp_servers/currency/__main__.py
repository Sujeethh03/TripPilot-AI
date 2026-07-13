"""Entrypoint: `python -m mcp_servers.currency` runs the server over stdio."""

from mcp_servers.currency.server import mcp

if __name__ == "__main__":
    mcp.run(transport="stdio")
