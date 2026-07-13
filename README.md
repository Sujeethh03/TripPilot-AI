# TripPilot AI

A conversational, agentic AI travel planner that turns a chat into a validated, day-by-day itinerary — powered by OpenAI, orchestrated with LangGraph, and grounded in real data through MCP-based tools.

You just talk — "5 days, ₹20k, Kerala, love waterfalls and street food" — and a team of coordinated agents asks clarifying questions, researches real options, builds an hour-by-hour plan, and refines it live.

- **Backend:** FastAPI + LangGraph + FastMCP
- **Frontend:** Next.js 14 + TypeScript + Tailwind
- **LLM:** OpenAI (GPT-4o / GPT-4o-mini)
- **Data:** PostgreSQL + pgvector, Redis

See [`PROJECT_PLAN.md`](./PROJECT_PLAN.md) for the full design, [`FRONTEND_PLAN.md`](./FRONTEND_PLAN.md) for the frontend spec, and [`PROGRESS.md`](./PROGRESS.md) for current status.

---

## Running locally

You run **two processes**: the backend API (port **8000**) and the frontend (port **3000**). The frontend talks to the backend, and the backend needs PostgreSQL.

### Prerequisites

- **Python 3.11+** and [`uv`](https://docs.astral.sh/uv/) (backend)
- **Node 22+** with **pnpm** (enable once via `corepack enable pnpm`)
- **PostgreSQL 16/17** running locally

### 1. Start PostgreSQL and create the database

```bash
brew services start postgresql@17        # or however you run Postgres

# One-time: create the role + database the backend expects
psql -d postgres -c "CREATE ROLE trippilot WITH LOGIN PASSWORD 'trippilot';"
psql -d postgres -c "CREATE DATABASE trippilot OWNER trippilot;"
```

### 2. Backend (terminal 1)

```bash
cd backend
uv venv                       # first time only
uv pip install -e ".[dev]"    # first time only

cp .env.example .env          # first time only — then edit .env:
#   OPENAI_API_KEY=...        (required for real planning)
#   DATABASE_URL=postgresql+asyncpg://trippilot:trippilot@localhost:5432/trippilot
#   OPENWEATHER_KEY=...        (optional — weather MCP)
#   GOOGLE_MAPS_KEY=...        (optional — places MCP)
#   GOOGLE_CLIENT_ID=...       (optional — Google sign-in)

uv run alembic upgrade head   # first time (and after schema changes) — creates tables

uv run uvicorn app.main:app --reload
```

Backend is up when http://localhost:8000/api/v1/health returns OK.
Interactive API docs: http://localhost:8000/docs

### 3. Frontend (terminal 2)

```bash
cd frontend
pnpm install                  # first time only
cp .env.local.example .env.local   # first time only (defaults already point at :8000)

pnpm dev
```

### 4. Open the app

Go to **http://localhost:3000**.

- Click **Get started** → register with an email + password (min 8 chars).
- You'll land on the dashboard (trip list is being built out).
- **Google sign-in** only appears if you set `NEXT_PUBLIC_GOOGLE_CLIENT_ID` (frontend) and `GOOGLE_CLIENT_ID` (backend) to the same value.

> The login/register **pages** render without the backend, but submitting them
> (and the dashboard) needs the backend + Postgres running.

### Quick reference

| What | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |
| Health check | http://localhost:8000/api/v1/health |

---

## Checks

```bash
# Backend
cd backend && uv run pytest && uv run ruff check . && uv run mypy app mcp_servers

# Frontend
cd frontend && pnpm lint && pnpm exec tsc --noEmit && pnpm build
```
