# Progress

Running log of what's done, in flight, and next. Update this as we work. Newest entries at the top of the log.

## Status

**Phase:** Scaffolding
**Current focus:** Backend scaffold

## Now / Next

- [ ] LangGraph conversational graph skeleton: state schema, checkpointer, empty nodes
- [ ] First MCP server (`weather` — simplest) to validate the MCP pattern
- [ ] Set up basic CI
- [ ] Auth (email + Google OAuth) + Alembic migrations for users/trips/conversations
- [ ] Stand up Postgres + Redis in Docker Compose

## Done

- [x] Repo created, remote set to `Sujeethh03/TripPilot-AI`, project plan committed
- [x] Scaffold FastAPI backend: app factory, pydantic-settings config, `/api/v1/health`, CORS, Dockerfile, smoke test

## Log

### 2026-07-13
- Set up project: git repo, `CLAUDE.md`, `PROGRESS.md`, copied in `PROJECT_PLAN.md`.
- Scaffolded backend under `backend/`: `pyproject.toml` (uv, fastapi, ruff/mypy/pytest), `app/main.py` (app factory + CORS + versioned router), `app/config.py` (pydantic-settings), `app/api/v1/health.py`, `.env.example`, `Dockerfile`, health smoke test, `backend/README.md`.
