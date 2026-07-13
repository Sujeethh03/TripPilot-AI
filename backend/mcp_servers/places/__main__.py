"""Entrypoint: `python -m mcp_servers.places` runs the server over stdio."""

from mcp_servers.places.server import mcp

if __name__ == "__main__":
    mcp.run(transport="stdio")
