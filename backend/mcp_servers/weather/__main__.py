"""Entrypoint: `python -m mcp_servers.weather` runs the server over stdio."""

from mcp_servers.weather.server import mcp

if __name__ == "__main__":
    mcp.run(transport="stdio")
