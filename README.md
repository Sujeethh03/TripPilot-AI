# TripPilot AI

**A conversational, agentic AI travel planner for trips across India.**

You talk in plain language — *"5 days in Kerala, ₹20k, from Kochi by car, love waterfalls and street food"* — and a team of coordinated AI agents asks clarifying questions, researches **real** options through tool servers, builds an hour-by-hour itinerary, validates it for feasibility, and refines it live as you chat.

Built to demonstrate production-shaped agentic architecture: LangGraph orchestration, MCP tool servers, deterministic validation, streaming, and a typed end-to-end contract.

<!-- HERO IMAGE — add docs/images/hero.png (the split chat + itinerary trip view) and uncomment:
<p align="center">
  <img src="docs/images/hero.png" alt="TripPilot — chat and itinerary side by side" width="900">
</p>
-->

---

## Demo

<!-- DEMO GIF — add docs/images/demo.gif (a plan streaming in) and uncomment:
<p align="center">
  <img src="docs/images/demo.gif" alt="Planning a trip: agents research, build, and validate an itinerary live" width="900">
</p>
-->

<!-- Screenshots — add the files under docs/images/ and uncomment:
| Trip view | Exported PDF |
|---|---|
| <img src="docs/images/itinerary.png" alt="Itinerary with weather, travel banner, hotels, and route map" width="420"> | <img src="docs/images/pdf.png" alt="Exported itinerary PDF" width="420"> |
-->

_Screenshots to add: see [`docs/images/README.md`](docs/images/README.md)._

---

## What it does

- **Plans from a sentence.** Describe a trip and get a concrete day-by-day itinerary — ordered time blocks with activity, location, estimated cost, and practical tips.
- **Grounded in real data, not the model's imagination.** Attractions, restaurants, hotels, weather, and travel times come from live APIs (Google Places, OpenWeather, Google Directions) — never invented by the LLM.
- **Refines conversationally.** *"Make day 2 cheaper", "add a beach", "less driving"* — it revises the existing plan while preserving the real facts.
- **Checks its own work.** A deterministic (non-LLM) validator reviews every plan for feasibility; if it fails, a refiner fixes it and it re-checks — a bounded self-correction loop you watch happen live.
- **Real-time streaming.** The routing decision, each agent's progress, the itinerary appearing block by block, and validation all stream over a WebSocket.
- **Exports.** Download the finished itinerary as a PDF.

### Feature highlights

| Area | What's there |
|---|---|
| Itinerary | Day-by-day blocks, running budget vs. your cap, per-day **weather**, **route map** of daily stops |
| Travel | Optional **starting point + transport mode** (drive / bus-train) → real distance & time for the leg |
| Stay | **"Where to stay"** — real hotel options (name, area, rating) from Google Places lodging |
| Accounts | Email/password auth (JWT) + optional Google Sign-In |
| Trips | Create, list, open, and hard-delete trips (full data purge) |
| Export | Server-side PDF generation |

---

## How it works

Agents are orchestrated as a **LangGraph** state machine. Every turn is routed, and planning turns run a research → synthesize → validate → refine pipeline. **Agents never call external APIs directly** — every tool is a separate **MCP server** reached through a client pool.

```mermaid
flowchart TD
    U([User message]) --> CM{Conversation Manager<br/>router}
    CM -->|chit-chat / clarify| R([Reply])
    CM -->|plan| I[Intake<br/>extract TripRequest]
    CM -->|refine| RF

    I --> P[Planner<br/>day skeletons]
    P --> RS[Researcher<br/>real MCP data]
    RS --> SY[Synthesizer<br/>build itinerary]
    SY --> V{Validator<br/>deterministic}
    V -->|feasible| D([Itinerary])
    V -->|issues, under cap| RF[Refiner]
    RF --> V

    RS -.-> MCP
    subgraph MCP[MCP tool servers]
      W[Weather<br/>OpenWeather]
      PL[Places + Hotels<br/>Google Places]
      DIR[Directions<br/>Google Directions]
      CUR[Currency<br/>Frankfurter]
    end
```

**Design principles that shaped the code:**

- **Facts are never trusted to the LLM.** Weather, hotels, travel times, and real places are fetched via MCP and attached *deterministically* after synthesis. The model writes the *plan*; data provides the *facts*.
- **The validator is plain Python, not an LLM** — feasibility (budget, structure) is checked deterministically, so the plan can't be "confidently wrong."
- **One schema, one source of truth.** The `Itinerary` schema is defined once (Pydantic) and every consumer — streaming, DB, PDF, and the frontend (mirrored in Zod) — imports it, so contract drift surfaces as a type error, not a runtime surprise.
- **Tool isolation via MCP.** Each external API is its own server with least-privilege secrets, swappable behind a stable tool contract.
- **Bounded loops.** The validate⇄refine cycle is capped so it always terminates.

---

## Tech stack

**Backend**
- Python 3.11, **FastAPI** (REST + WebSocket)
- **LangGraph** — agent orchestration & checkpointed conversation state
- **FastMCP** + `langchain-mcp-adapters` — tool servers over stdio, pooled
- **OpenAI** (GPT-4o planner / GPT-4o-mini router) with structured outputs
- **SQLAlchemy 2.0** (async) + **Alembic**, **PostgreSQL 16**
- Pydantic v2, `fpdf2` (PDF), `ruff` + `mypy --strict`

**Frontend**
- **Next.js 14** (App Router) + **TypeScript** (strict)
- **Tailwind** + shadcn/ui (Radix)
- **TanStack Query** (server state) + **Zustand** (live chat state)
- **Zod** contracts, React Hook Form, WebSocket streaming client

**External data (each wrapped as an MCP server)**
- Google Places (attractions + hotels), Google Directions, OpenWeather, Frankfurter (currency)

---

## Project structure

```
backend/
  app/
    agents/         # LangGraph nodes (router, intake, planner, researcher,
                    #   synthesizer, validator, refiner), prompts, streaming
    api/            # FastAPI routes: auth, trips, chat WebSocket
    mcp/            # MCP client pool + agent-side tool helpers
    schemas/        # SSOT Pydantic models (Itinerary, TripRequest, ...)
    models/         # SQLAlchemy models
    services/       # PDF export
    db/             # session + Alembic migrations
  mcp_servers/      # standalone MCP tool servers (weather, places, directions, currency)
  tests/            # pytest suite (unit + integration)
frontend/
  app/              # routes (dashboard, trip view, auth)
  components/       # chat, itinerary, budget, trips, ui
  lib/              # api client, Zod schemas, query hooks, ws
  store/            # Zustand chat store
```

---

## Running locally

Two processes: the **backend API** (port `8000`) and the **frontend** (port `3000`). The backend needs PostgreSQL.

### Prerequisites
- **Python 3.11+** and [`uv`](https://docs.astral.sh/uv/)
- **Node 22+** with **pnpm** (`corepack enable pnpm`)
- **PostgreSQL 16+**

### 1. Database
```bash
psql -d postgres -c "CREATE ROLE trippilot WITH LOGIN PASSWORD 'trippilot';"
psql -d postgres -c "CREATE DATABASE trippilot OWNER trippilot;"
```

### 2. Backend
```bash
cd backend
uv venv && uv pip install -e ".[dev]"     # first time
cp .env.example .env                       # then fill in keys (see below)
uv run alembic upgrade head                # create tables
uv run uvicorn app.main:app --reload
```

`.env` keys:
```
OPENAI_API_KEY=...        # required for planning
DATABASE_URL=postgresql+asyncpg://trippilot:trippilot@localhost:5432/trippilot
OPENWEATHER_KEY=...       # weather MCP
GOOGLE_MAPS_KEY=...       # places + directions MCP (Places API + Directions API)
GOOGLE_CLIENT_ID=...      # optional — Google sign-in
```

### 3. Frontend
```bash
cd frontend
pnpm install
cp .env.local.example .env.local           # defaults point at :8000
pnpm dev
```
Optional in `.env.local`: `NEXT_PUBLIC_GOOGLE_MAPS_KEY` (Maps JS + Geocoding APIs) to show the route map; `NEXT_PUBLIC_GOOGLE_CLIENT_ID` for Google sign-in.

### 4. Open
| What | URL |
|---|---|
| App | http://localhost:3000 |
| API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |

---

## Testing & quality

```bash
# Backend — pytest suite, lint, strict type-check
cd backend && uv run pytest && uv run ruff check . && uv run mypy app mcp_servers

# Frontend — lint, type-check, production build
cd frontend && pnpm lint && pnpm exec tsc --noEmit && pnpm build
```

The backend suite covers the agent nodes (LLM/tool boundaries mocked), the MCP adapters (defensive parsing), the REST + WebSocket layers, persistence, and PDF export.

---

## Honest limitations

- **No live bookings, prices, or availability** — hotels and places are grounded suggestions with ratings, not reservations (that needs paid APIs like Booking/Amadeus).
- **Travel legs are drive or bus/train transit only** (Google Directions) — no flights.
- **Weather is a 5-day forecast** — trips further out get an indicative forecast.
- **India-focused**, budgets in ₹.
- Drive-time *between* daily stops isn't enforced yet (planned once itinerary blocks carry coordinates).
