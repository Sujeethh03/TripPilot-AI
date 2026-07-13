# Weather MCP server — runs standalone over stdio (or HTTP post-MVP).
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Minimal runtime deps for this server only.
RUN uv pip install --system --no-cache "fastmcp>=2.0" "httpx>=0.27" "pydantic>=2.7"

COPY mcp_servers ./mcp_servers

CMD ["python", "-m", "mcp_servers.weather"]
