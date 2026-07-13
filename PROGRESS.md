# Progress

Running log of what's done, in flight, and next. Update this as we work. Newest entries at the top of the log.

## Status

**Phase:** Scaffolding
**Current focus:** LangGraph skeleton done → next is first MCP server

## Now / Next

- [ ] Wire the MCP client pool into the Researcher node (call `get_forecast` for real)
- [ ] More MCP servers: `places`, `directions`, `buses` (Rome2Rio), `currency`
- [ ] Set up basic CI
- [ ] Auth (email + Google OAuth) + Alembic migrations for users/trips/conversations
- [ ] Stand up Postgres + Redis in Docker Compose

## Done

- [x] Repo created, remote set to `Sujeethh03/TripPilot-AI`, project plan committed
- [x] Scaffold FastAPI backend: app factory, pydantic-settings config, `/api/v1/health`, CORS, Dockerfile, smoke test
- [x] LangGraph conversational graph skeleton: SSOT schemas, `ConversationState`, checkpointer factory, 7 stub nodes, routing + bounded refine loop, end-to-end tests. mypy strict + ruff clean.
- [x] `weather` MCP server (FastMCP) + MCP client pool: OpenWeatherMap adapter (daily aggregation, defensive parsing), `get_forecast` tool, stdio entrypoint, Dockerfile. Client pool via langchain-mcp-adapters with a server registry. Tests: unit (parsing), in-memory tool contract, integration (pool spawns server & discovers tool). All green.

## Log

### 2026-07-13
- Set up project: git repo, `CLAUDE.md`, `PROGRESS.md`, copied in `PROJECT_PLAN.md`.
- Scaffolded backend under `backend/`: `pyproject.toml` (uv, fastapi, ruff/mypy/pytest), `app/main.py` (app factory + CORS + versioned router), `app/config.py` (pydantic-settings), `app/api/v1/health.py`, `.env.example`, `Dockerfile`, health smoke test, `backend/README.md`.
- Built LangGraph skeleton. Schemas (SSOT): `schemas/itinerary.py` (Itinerary/Day/Block), `schemas/trip.py` (TripRequest), `schemas/planning.py` (DaySkeleton, ResearchBundle, ValidationReport). Agents: `agents/state.py` (`ConversationState` TypedDict + `Route` StrEnum + `MAX_REFINEMENTS=2`), `agents/checkpointer.py` (MemorySaver now, Postgres later), `agents/nodes/*` (7 stub nodes, no LLM/MCP yet), `agents/graph.py` (router + linear pipeline + bounded validate/refine loop). Tests in `tests/test_graph.py`. Added `langgraph>=0.2` dep.
- Built `weather` MCP server + client pool. `mcp_servers/weather/` (schemas, `openweather.py` adapter, `server.py`, `__main__.py`, Dockerfile). `app/mcp/` (`config.py` registry, `client_pool.py` singleton over langchain-mcp-adapters). Tests under `tests/mcp/` + `tests/test_mcp_pool.py`. Added `fastmcp>=2.0`, `langchain-mcp-adapters>=0.1`, `httpx>=0.27` deps. `OPENWEATHER_KEY` in `.env.example`.
