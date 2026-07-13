"""Entrypoint: `python -m mcp_servers.directions` runs the server over stdio."""

from mcp_servers.directions.server import mcp

if __name__ == "__main__":
    mcp.run(transport="stdio")
