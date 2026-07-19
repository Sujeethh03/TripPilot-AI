# TripPilot backend — FastAPI app (agent orchestrator).
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# uv for fast, reproducible installs.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Source is copied before the install because the build backend packages
# `app` and `mcp_servers` — they must exist for the wheel to build. The MCP
# servers are spawned as `python -m mcp_servers.<name>` subprocesses at
# runtime (app/mcp/config.py), so they have to ship in the image.
COPY pyproject.toml ./
COPY app ./app
COPY mcp_servers ./mcp_servers
COPY alembic.ini ./

RUN uv pip install --system --no-cache .

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
