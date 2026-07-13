# Progress

Running log of what's done, in flight, and next. Update this as we work. Newest entries at the top of the log.

## Status

**Phase:** Scaffolding
**Current focus:** LangGraph skeleton done → next is first MCP server

## Now / Next

- [ ] Persist chat messages per WS turn + save itinerary to the trip row (so GET /trips/{id}/messages and trip.itinerary populate)
- [ ] PDF export endpoint (GET /trips/{id}/pdf)
- [ ] Google OAuth (email/password auth done)
- [ ] More MCP servers: places, directions, buses, currency
- [ ] Frontend (Next.js)
- [ ] Auth (email + Google OAuth); associate trips with users
- [ ] CI: add Postgres service + a DB integration test (DB tests currently verified locally only)
- [ ] More MCP servers: places, directions, buses, currency
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
- [x] Researcher wired to real MCP data: `app/mcp/weather.py::fetch_forecast` calls the weather tool through the pool and parses the result defensively; Researcher populates `ResearchBundle.weather_by_day` for the Synthesizer. All 7 nodes now real AND (for weather) grounded. LIVE verified: Munnar plan pulls real forecast into the bundle. 40 tests green, ruff + mypy strict clean.
- [x] Chat WebSocket + streaming (`/ws/trips/{id}/chat`): graph singleton (`get_graph`), streaming translation layer (`app/agents/streaming.py`: node updates → route_decision/agent_update/partial_itinerary/validation_report/assistant_message/complete/error), WS endpoint streaming via `graph.astream(stream_mode=updates)`, thread_id = trip id. Shared test fixture in `conftest.py`. Tests: streaming unit + WS integration (TestClient). LIVE verified: real streamed run showed the validator/refiner self-correction loop (day_count_mismatch → fixed). 47 tests green, ruff + mypy strict clean.
- [x] Trips REST API (`app/api/v1/trips.py`): `POST /trips` (creates trip + conversation, thread_id=trip.id), `GET /trips` (paginated), `GET /trips/{id}`, `PATCH /trips/{id}`, `DELETE /trips/{id}` (soft delete), `GET /trips/{id}/messages`. `TripRepository` + `ConversationRepository`/`MessageRepository`. Ownership enforced in the repo query (404, no existence leak). `TripCreate/Update/Response` + `MessageResponse` (from_attributes). `auth_headers`/`register_and_auth` test helpers. 6 integration tests (CRUD, ownership, auth-required). Fixed soft-delete tz bug (naive UTC to match columns). 61 tests green, ruff + mypy strict clean.
- [x] Email/password auth: `app/core/security.py` (bcrypt hashing + PyJWT HS256 tokens), `UserRepository` (Repository pattern), `get_current_user` dep (HTTP Bearer), endpoints `POST /api/v1/auth/register` (201, 409 on dup), `POST /api/v1/auth/login` (JWT), `GET /api/v1/me`. Auth schemas with `EmailStr`. Config: jwt_secret/algorithm/expiry. Test infra: Postgres-backed `client`/`db_sessionmaker` fixtures (fresh schema per test on `trippilot_test`), added Postgres service + `TEST_DATABASE_URL` to CI. Tests: security unit + 5 auth integration. 56 tests green, ruff + mypy strict clean. Google OAuth still TODO.
- [x] LangGraph Postgres checkpointer wired via FastAPI lifespan (`app/main.py`): builds the graph once per process with `AsyncPostgresSaver` when `CHECKPOINTER=postgres` + `DATABASE_URL` set, else `MemorySaver` (default, keeps tests hermetic). WS endpoint now reads `app.state.graph`; removed the `get_graph` singleton. Added `checkpointer` setting + `postgres_dsn` property. Added `langgraph-checkpoint-postgres` + `psycopg[binary]`. VERIFIED against local Postgres: ran a plan turn, then rebuilt saver+graph (simulated restart) and recovered full conversation state; checkpoint tables created by `setup()`. 47 tests green, ruff + mypy strict clean.
- [x] Persistence (DB layer): async SQLAlchemy 2.0 setup (`app/db/base.py` with naming convention, `app/db/session.py` engine/sessionmaker/`get_session` dep), models `users/trips/conversations/messages` (§10; UUID PKs, JSONB itinerary+agent_events, CHECK constraints, FK indexes, soft deletes), Alembic (async `env.py`, initial autogen migration). `docker-compose.yml` (pgvector Postgres + Redis + backend). Migrations exclude from ruff/mypy. VERIFIED against LOCAL Postgres (postgresql@17): migration applied, full async CRUD round-trip (user→trip→conversation→message with JSONB) read back. NOTE: Postgres started locally via `brew services start postgresql@17`; role/db `trippilot/trippilot`; `DATABASE_URL` added to `.env`. DB tests not yet in CI. 47 tests green, ruff + mypy strict clean.
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
