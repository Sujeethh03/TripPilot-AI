# TripPilot AI

**A conversational, agentic AI travel planner for trips across India.**

You talk in plain language — *"5 days in Kerala, ₹20k, from Kochi by car, love waterfalls and street food"* — and a team of coordinated AI agents asks clarifying questions, researches **real** options through tool servers, builds an hour-by-hour itinerary, validates it for feasibility, and refines it live as you chat.

Built to demonstrate production-shaped agentic architecture: LangGraph orchestration, MCP tool servers, deterministic validation, streaming, and a typed end-to-end contract.

**[Live app](#deployment)** · **[Live API health check](https://trippilot-api.onrender.com/api/v1/health)** · **[How it works](#how-it-works)** · **[Deployment](#deployment)**

<p align="center">
  <img src="docs/images/hero.png" alt="TripPilot — chat on the left, live itinerary with route map, travel leg, budget, and hotels on the right" width="900">
</p>

---

## Screenshots

Chat and refine on the left; a live, validated itinerary — route map, travel leg, budget, weather, and hotels — on the right.

| Agents working live | Day-by-day itinerary |
|---|---|
| <img src="docs/images/agents.png" alt="Live agent activity: intake, planner, researcher, and a validator feasibility warning" width="440"> | <img src="docs/images/itinerary.png" alt="Where to stay plus hour-by-hour day blocks with costs" width="440"> |
| **Ask questions & refine in chat** | **Your trips dashboard** |
| <img src="docs/images/conversation.png" alt="Conversational Q&A about the trip with per-day weather on the itinerary" width="440"> | <img src="docs/images/dashboard.png" alt="Dashboard listing saved trips" width="440"> |

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

## Deployment

**Live API:** [`trippilot-api.onrender.com/api/v1/health`](https://trippilot-api.onrender.com/api/v1/health) · **App:** _<!-- VERCEL_URL -->coming soon_

> **Heads up on first load:** the backend runs on a free instance that sleeps after 15 minutes idle, so the first request can take ~50 seconds to wake it. After that it's responsive. A full plan takes 30–90s regardless — it's several GPT-4o calls plus live Places/Weather/Directions lookups.

### How it's deployed

```mermaid
flowchart LR
    U([Browser]) -->|HTTPS| V["Next.js<br/>Vercel"]
    V -->|REST + WSS| R

    subgraph R["FastAPI container — Render"]
      API[uvicorn<br/>REST + WebSocket]
      LG[LangGraph<br/>orchestrator]
      M1[weather]
      M2[places]
      M3[directions]
      M4[currency]
      API --- LG
      LG -.stdio.-> M1
      LG -.stdio.-> M2
      LG -.stdio.-> M3
      LG -.stdio.-> M4
    end

    R --> PG[(PostgreSQL 16<br/>Render)]
    LG --> OA[OpenAI]
    M1 --> EXT[Google / OpenWeather /<br/>Frankfurter APIs]
    M2 --> EXT
    M3 --> EXT
    M4 --> EXT
```

Backend is a Docker image defined by [`render.yaml`](render.yaml) — infrastructure as code, so the service, database, and environment are reproducible from the repo rather than dashboard clicks. The frontend is a Vercel project rooted at `frontend/`.

### Engineering notes

Things that turned out to matter in production, and how they're handled:

- **Migrations run on container start.** The entrypoint executes `alembic upgrade head` before `exec`-ing uvicorn — `exec` so uvicorn becomes PID 1 and the platform's `SIGTERM` reaches it, letting in-flight WebSocket turns close cleanly.
- **Conversation state survives restarts.** LangGraph checkpoints persist to Postgres (`CHECKPOINTER=postgres`), so a free-tier spin-down doesn't lose an in-progress plan.
- **MCP subprocesses are bounded.** Each tool server is its own Python process (~50 MB). The naive approach — asking the client for all tools — spawns every server on every call, which peaked at ~32 processes / ~1.6 GB during a planning turn and OOM-killed a 512 MB container. Calls are now scoped to a single server and capped by a semaphore: **3 processes / 174 MB peak, measured.**
- **Secrets never live in git.** Everything sensitive is `sync: false` in the blueprint — entered once in the dashboard. `JWT_SECRET` is generated by Render, never a checked-in default.
- **Config fails loudly.** `CORS_ORIGINS` is a typed `list[str]`; a malformed value aborts startup with a clear error instead of silently defaulting and surfacing later as unexplained browser CORS failures.
- **Portable by design.** Plain Docker with no host-specific code, so Railway or Fly.io is a config swap, not a rewrite.

<details>
<summary><b>Reproducing this deployment</b></summary>

Deploy the backend first — the frontend needs its URL, and the backend needs the frontend's origin for CORS.

**1. Backend → Render.** **New → Blueprint**, point it at this repo. It reads `render.yaml` and creates the web service plus a Postgres 16 instance, wiring `DATABASE_URL` automatically. Then set the `sync: false` secrets under **Environment**:

| Var | Value |
|---|---|
| `OPENAI_API_KEY` | OpenAI key |
| `OPENWEATHER_KEY` | openweathermap.org key |
| `GOOGLE_MAPS_KEY` | Maps Platform key — Places API (New) + Directions API enabled |
| `GOOGLE_CLIENT_ID` | Google Sign-In client id (blank disables Google auth) |
| `CORS_ORIGINS` | `["https://<your-app>.vercel.app"]` — JSON array, no trailing slash |

Health check is `/api/v1/health`. The database must be in the **same region** as the web service — Render's `connectionString` is an internal hostname that only resolves in-region.

**2. Frontend → Vercel.** Import the repo, set **Root Directory** to `frontend`; the Next.js preset handles the rest.

| Var | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://<service>.onrender.com` |
| `NEXT_PUBLIC_WS_URL` | `wss://<service>.onrender.com` — **`wss://`, not `ws://`** |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | same client id as the backend |
| `NEXT_PUBLIC_GOOGLE_MAPS_KEY` | Maps JS + Geocoding key, restricted by HTTP referrer |

These are baked in at build time, so a change needs a redeploy. Unset, the build falls back to `localhost:8000` and the deployed app can't reach the API — set them before the first build.

**3.** Add the Vercel URL to the backend's `CORS_ORIGINS`, and to the OAuth client's authorized JavaScript origins in the Google Cloud console.

</details>

---

