# Progress

Running log of what's done, in flight, and next. Update this as we work. Newest entries at the top of the log.

## Status

**Phase:** Scaffolding
**Current focus:** LangGraph skeleton done → next is first MCP server

## Now / Next

- [ ] Wire the MCP client pool into the Researcher node (call `get_forecast` for real) — now unblocked (weather key active)
- [ ] Chat WebSocket + streaming agent events; persist conversations/messages
- [ ] Intake: date/duration resolution + `interrupt()` for missing required fields
- [ ] Auth (email + Google OAuth) + Alembic migrations for users/trips/conversations
- [ ] Stand up Postgres + Redis in Docker Compose; swap MemorySaver → Postgres checkpointer
- [ ] Validator rules needing research data: opening hours (places MCP), drive times (directions MCP)
- [ ] More MCP servers: `places`, `directions`, `buses` (Rome2Rio), `currency`
- [ ] Auth (email + Google OAuth) + Alembic migrations for users/trips/conversations
- [ ] Stand up Postgres + Redis in Docker Compose

## Done

- [x] Repo created, remote set to `Sujeethh03/TripPilot-AI`, project plan committed
- [x] Scaffold FastAPI backend: app factory, pydantic-settings config, `/api/v1/health`, CORS, Dockerfile, smoke test
- [x] LangGraph conversational graph skeleton: SSOT schemas, `ConversationState`, checkpointer factory, 7 stub nodes, routing + bounded refine loop, end-to-end tests. mypy strict + ruff clean.
- [x] `weather` MCP server (FastMCP) + MCP client pool: OpenWeatherMap adapter (daily aggregation, defensive parsing), `get_forecast` tool, stdio entrypoint, Dockerfile. Client pool via langchain-mcp-adapters with a server registry. Tests: unit (parsing), in-memory tool contract, integration (pool spawns server & discovers tool). All green.
- [x] Real Validator: deterministic rule chain in `app/agents/validation.py` (budget +10% buffer, pacing, time ordering, meal-slot presence, empty check) wired into the validator node. 11 exhaustive tests. Opening-hours/drive-time rules deferred (need places/directions MCP data).
- [x] GitHub Actions CI (`.github/workflows/backend-ci.yml`): ruff + mypy strict + pytest on push/PR touching `backend/**`.
- [x] Real Intake node: GPT-4o-mini structured extraction (`IntakeExtraction` → `TripRequest`). OpenAI client singleton (`app/core/openai_client.py`), model IDs in config, versioned prompt (`agents/prompts/intake.py`). LLM boundary isolated in `_extract` for mocking; graph converted to async (`ainvoke`). Added `openai` dep + `duration_days` to TripRequest. 23 tests green.
- [x] Real Planner + Synthesizer nodes (GPT-4o structured outputs). Shared `app/core/llm.py::parse_structured` helper (DRY across all 3 LLM nodes; single seam for future cost/retry/cache). Prompts `agents/prompts/planner.py`/`synthesizer.py`, `DaySkeletonPlan` wrapper schema. LLM boundaries (`_plan`, `_synthesize`) mocked in tests. Now the Intake→Planner→Synthesizer→Validator path is real (Researcher still a stub). 27 tests green.

## Log

### 2026-07-13
- Set up project: git repo, `CLAUDE.md`, `PROGRESS.md`, copied in `PROJECT_PLAN.md`.
- Scaffolded backend under `backend/`: `pyproject.toml` (uv, fastapi, ruff/mypy/pytest), `app/main.py` (app factory + CORS + versioned router), `app/config.py` (pydantic-settings), `app/api/v1/health.py`, `.env.example`, `Dockerfile`, health smoke test, `backend/README.md`.
- Built LangGraph skeleton. Schemas (SSOT): `schemas/itinerary.py` (Itinerary/Day/Block), `schemas/trip.py` (TripRequest), `schemas/planning.py` (DaySkeleton, ResearchBundle, ValidationReport). Agents: `agents/state.py` (`ConversationState` TypedDict + `Route` StrEnum + `MAX_REFINEMENTS=2`), `agents/checkpointer.py` (MemorySaver now, Postgres later), `agents/nodes/*` (7 stub nodes, no LLM/MCP yet), `agents/graph.py` (router + linear pipeline + bounded validate/refine loop). Tests in `tests/test_graph.py`. Added `langgraph>=0.2` dep.
- Built `weather` MCP server + client pool. `mcp_servers/weather/` (schemas, `openweather.py` adapter, `server.py`, `__main__.py`, Dockerfile). `app/mcp/` (`config.py` registry, `client_pool.py` singleton over langchain-mcp-adapters). Tests under `tests/mcp/` + `tests/test_mcp_pool.py`. Added `fastmcp>=2.0`, `langchain-mcp-adapters>=0.1`, `httpx>=0.27` deps. `OPENWEATHER_KEY` in `.env.example`.
- Verified the weather path hits the real OpenWeatherMap API (got a genuine 401 — key not yet active/invalid; code path confirmed correct). Moved the key from tracked `.env.example` into gitignored `.env`.
- Implemented the real Validator (`app/agents/validation.py`) as an ordered rule chain + 11 tests. Added backend CI workflow. Full suite: 20 tests green, ruff + mypy strict clean.
- Implemented the real Intake node with OpenAI structured outputs. New: `app/core/openai_client.py` (singleton), `app/agents/prompts/intake.py`, `IntakeExtraction` schema, `model_router`/`model_planner` config. Graph now runs async. LLM mocked in tests (no key/network needed). Note: `duration_days` added to `TripRequest` (additive). Live verification pending an `OPENAI_API_KEY`. 23 tests green.
- Implemented Planner + Synthesizer. Factored shared parse boilerplate into `app/core/llm.py::parse_structured` and refactored Intake onto it. Prompts + `DaySkeletonPlan` wrapper. Real LLM path is now Intake→Planner→Synthesizer→Validator (Researcher stubbed). Tests mock each LLM boundary via `importlib` module patch (node functions shadow their submodules). 27 tests green, ruff + mypy strict clean.
- LIVE verified end-to-end against real OpenAI (key set): "3 days Kerala 20k couple waterfalls/street food" → correct Intake extraction, 3 sensible day themes from Planner, valid itinerary. Known gap: Synthesizer only filled Day 1 (no rule enforcing day count == duration_days yet).
- LIVE verified weather: OpenWeather key now active. Fixed MCP env passing — stdio transport sanitizes env, so `app/mcp/config.py` now passes `OPENWEATHER_KEY` (from settings) + safe base vars to the weather subprocess (least privilege). Real forecasts confirmed via direct client AND full pool→server→API path (Kochi, Munnar). Added `openweather_key` to Settings.
- Completed the graph: real Conversation Manager (GPT-4o-mini router → chit_chat/clarify/plan/refine, inline replies, resets per-turn refinement counter) and real Refiner (GPT-4o revision from validation issues + user message). Added `check_day_count` Validator rule + tightened Synthesizer prompt (fixes the Day-1-only bug). All 7 nodes now real. 35 tests green, ruff + mypy strict clean.
- LIVE verified the full graph: "3 days Kerala 20k couple waterfalls/street food" → complete 3-day itinerary (₹9300, valid). Refine turn "swap day 3 for a beach day" → correctly routed to refine, kept days 1-2, rebuilt day 3 as Marari Beach. Multi-turn conversational planning works end to end.
