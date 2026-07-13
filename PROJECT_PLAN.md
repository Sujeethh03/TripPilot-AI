# TripPilot AI — Project Plan

> A conversational, agentic AI travel planner that turns a chat into a validated, day-by-day itinerary — powered by OpenAI, orchestrated with LangGraph, and grounded in real data through MCP-based tools.

**Repository:** https://github.com/Sujeethh03/TripPilot-AI
**Status:** Planning → Scaffolding
**Owner:** Sujeeth

---

## 1. Executive Summary

TripPilot AI is a full-stack, conversational travel planner. Instead of forms and dropdowns, the user just *talks* — "5 days, ₹20k, Kerala, love waterfalls and street food" — and a team of coordinated AI agents ask clarifying questions, research real options, build an hour-by-hour plan, and refine it live as the conversation continues.

The stack is FastAPI (backend) + Next.js (frontend), OpenAI GPT-4o models for reasoning, LangGraph for stateful multi-agent orchestration, and MCP (Model Context Protocol) servers for every tool integration — Places, Weather, Directions, Buses, Trains, Currency. Data lives in PostgreSQL + pgvector; caching in Redis; deployment via Docker to Replit (backend) and Vercel (frontend).

The goal is a working conversational MVP in ~12 weeks that feels less like filling out a form and more like texting a knowledgeable travel friend who happens to have real-time access to maps, weather, and transport data.

---

## 2. Vision & Value Proposition

### Problem
Existing tools fail in different ways:
- Booking sites give you *inventory*, not *plans*
- Blog posts are static and out of date
- Generic chatbots hallucinate opening hours and can't validate anything
- Nothing actually *converses* — most "AI planners" are one-shot form-fills wearing a chat skin

### Solution
A genuinely conversational agent that:
- Asks clarifying questions before assuming anything
- Grounds every recommendation in a real tool call (no hallucinated hotels)
- Validates feasibility (drive times, opening hours, budget fit) as deterministic checks — not vibes
- Refines live: "actually skip day 3 and add a beach" just works
- Remembers context across turns (short-term via LangGraph checkpoints, long-term via pgvector)

### Key Differentiators
1. **True multi-turn conversation** — clarifications, interruptions, mid-flight edits
2. **Agent transparency** — the UI shows which agent is working and on what
3. **MCP-based tool architecture** — swap providers without touching agent code
4. **Feasibility validation** — no more "10 attractions in 6 hours" nonsense
5. **India-first** — trains, buses, autos, street food, festivals treated as native concepts
6. **Budget-aware** — budget is a hard constraint, not an afterthought

### Target Users
- Solo travelers and couples planning domestic Indian trips (₹5k–₹50k budgets)
- People overwhelmed by fragmented research on Reddit, YouTube, and blogs
- Later: international travel, families, group trips

---

## 3. Tech Stack

### Backend
| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.11+ | LangGraph, MCP SDK, FastAPI ecosystem |
| Framework | FastAPI 0.115+ | Async, auto-docs, Pydantic-native, WebSockets built-in |
| Agent orchestration | LangGraph | Checkpointing for conversation memory, interrupt/resume, streaming |
| Tool protocol | MCP (Model Context Protocol) | Standardized, hot-swappable, testable in isolation |
| MCP server framework | FastMCP (Python) | Fast to build MCP servers, ergonomic decorators |
| MCP client bridge | `langchain-mcp-adapters` | Exposes MCP tools as LangChain tools for LangGraph nodes |
| LLM provider | OpenAI (GPT-4o + GPT-4o-mini) | Native structured outputs, mature function calling, MCP client support via OpenAI Agents SDK |
| ORM | SQLAlchemy 2.0 (async) | Mature, typed, works with asyncpg |
| Validation | Pydantic v2 | Fast, first-class in FastAPI, defines MCP tool schemas |
| Migrations | Alembic | Standard for SQLAlchemy |
| Auth | FastAPI-Users or custom JWT | Google OAuth + email/password |
| Background jobs | ARQ (Redis-based) or Celery | For long-running trip generation |
| Testing | pytest + pytest-asyncio | Standard |

### Frontend
| Layer | Choice | Why |
|---|---|---|
| Framework | Next.js 14 (App Router) | Server components, streaming, Vercel-native |
| Language | TypeScript | Type safety across the API boundary |
| Styling | Tailwind CSS | Fast to iterate, works with shadcn |
| Components | shadcn/ui | Own the code, no lock-in, accessible defaults |
| State | Zustand | Simple, works with SSR, good for chat state |
| Data fetching | TanStack Query | Caching, mutations, optimistic updates |
| Forms | React Hook Form + Zod | Type-safe validation |
| Chat UI | Custom + `assistant-ui` (optional) | Streaming, tool-call visualization |
| Maps | Mapbox GL JS | Cheaper than Google Maps at scale, better styling |
| Animations | Framer Motion | For agent-thinking indicators, transitions |
| PDF export | Server-side WeasyPrint | Better fidelity than client-side react-pdf |

### Data
| Layer | Choice | Why |
|---|---|---|
| Primary DB | PostgreSQL 16 | Reliable, JSON support, pgvector plugin |
| Vector store | pgvector | Same DB — no separate service |
| Cache | Redis | LLM response caching, MCP tool caching, session state, rate limiting |
| Object storage | Cloudflare R2 or S3 | For PDFs, user uploads |

### External APIs (accessed through MCP servers)
- **Google Places API** — attractions, restaurants, hotels, reviews
- **OpenWeatherMap** — forecasts
- **Mapbox Directions** — routing, drive times
- **Rome2Rio API** — multi-modal transport (bus, train, flight, car) discovery. Best single API for Indian bus routes.
- **RailwayAPI / IRCTC scraping** (Phase 2) — Indian trains
- **RedBus / AbhiBus deep-links** (Phase 2) — actual bus booking
- **Amadeus / Skyscanner** (Phase 3) — flight prices

### DevOps
| Layer | Choice | Why |
|---|---|---|
| Containerization | Docker + Docker Compose | Consistent local dev, portable deploys |
| Backend hosting | Replit (initial) → Railway/Render (production) | Fast to start; migrate when scaling |
| Frontend hosting | Vercel | Zero-config for Next.js |
| CI/CD | GitHub Actions | Free, integrates with the repo |
| Error tracking | Sentry (free tier) | Catches production errors |
| Analytics | PostHog | Product analytics + session replay |
| Logging | structlog + Logfire | Structured logs matter for debugging agents |

---

## 4. Architecture

### High-Level

```
┌───────────────────────────────────────────────────────────────────────┐
│                     Next.js Frontend (Vercel)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────────┐    │
│  │ Chat UI      │  │ Itinerary    │  │ Map + Budget View         │    │
│  │ (streaming,  │  │ Timeline     │  │                           │    │
│  │  multi-turn) │  │              │  │                           │    │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬────────────────┘    │
└─────────┼─────────────────┼─────────────────────┼─────────────────────┘
          │                 │                     │
          │        REST + WebSocket (JSON)        │
          │                 │                     │
┌─────────▼─────────────────▼─────────────────────▼─────────────────────┐
│                    FastAPI Backend (Replit)                           │
│  ┌────────────┐  ┌────────────────┐  ┌────────────────────────────┐   │
│  │ API Layer  │  │ Auth (JWT)     │  │ WebSocket Handler          │   │
│  └─────┬──────┘  └────────────────┘  └───────────┬────────────────┘   │
│        │                                         │                    │
│  ┌─────▼─────────────────────────────────────────▼──────────────┐     │
│  │            LangGraph Conversational Orchestrator             │     │
│  │  ┌────────────────┐   ┌────────┐   ┌───────┐   ┌──────────┐  │     │
│  │  │Conversation Mgr│──▶│ Intake │──▶│Planner│──▶│Researchr │  │     │
│  │  │ (router +      │◀──└────────┘   └───────┘   └────┬─────┘  │     │
│  │  │  memory)       │      ▲             ▲            │        │     │
│  │  └────────────────┘   clarify        retry     ┌────▼──────┐ │     │
│  │           ▲              │             │       │Synthesizer│ │     │
│  │           │              │             │       └────┬──────┘ │     │
│  │           │              │             │            │        │     │
│  │           │              └─────────────┴────────────┤        │     │
│  │           │                                    ┌────▼─────┐  │     │
│  │           └────────────────────────────────────│Validator │  │     │
│  │                                                └──────────┘  │     │
│  │  Checkpointer (Postgres) — state persists per conversation   │     │
│  └───────────────┬─────────────────────┬────────────────────────┘     │
│                  │                     │                              │
│  ┌───────────────▼─────────┐  ┌────────▼──────────────────────┐       │
│  │  MCP Client Pool         │  │ OpenAI Client                │       │
│  │  (langchain-mcp-adapters)│  │ - GPT-4o (planning/synthesis)│       │
│  └───────────────┬─────────┘  │ - GPT-4o-mini (routing)      │       │
│                  │            │ - Structured Outputs         │       │
│                  │            └──────────────────────────────┘       │
│                  │  MCP Protocol (stdio / HTTP)                       │
│  ┌───────────────▼──────────────────────────────────────────────┐    │
│  │                  MCP Servers (FastMCP)                       │    │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌──────────────┐  │    │
│  │  │ places    │ │ weather   │ │directions │ │ buses (R2R)  │  │    │
│  │  └───────────┘ └───────────┘ └───────────┘ └──────────────┘  │    │
│  │  ┌───────────┐ ┌───────────┐ ┌──────────────────────────┐    │    │
│  │  │ trains    │ │ currency  │ │ + future: hotels, flights│    │    │
│  │  └───────────┘ └───────────┘ └──────────────────────────┘    │    │
│  └──────────────────────────────────────────────────────────────┘    │
└──────────┬───────────────────────────────────────┬───────────────────┘
           │                                       │
   ┌───────▼────────┐                     ┌────────▼────────┐
   │ PostgreSQL     │                     │ Redis           │
   │ - Users, Trips │                     │ - MCP tool cache│
   │ - Conversations│                     │ - LLM cache     │
   │ - Checkpoints  │                     │ - Session state │
   │ - pgvector     │                     └─────────────────┘
   └────────────────┘
```

### Conversational Flow (the important shift)

The old design was: user prompt → linear pipeline → itinerary. The new design is a **long-lived conversation** where the graph is entered on every user turn and can:

- Just chat (small talk about a destination)
- Ask a clarifying question and pause
- Plan (or replan) an itinerary
- Refine an existing itinerary based on feedback

**On every turn:**
1. Message arrives via WebSocket
2. LangGraph loads the conversation checkpoint (full history + last known trip state)
3. The **Conversation Manager** node routes the turn:
   - `chit_chat` → answer directly with GPT-4o-mini, done
   - `needs_clarification` → generate a question, stream it back, save checkpoint, exit
   - `ready_to_plan` → invoke the planning subgraph
   - `refine` → invoke the refinement subgraph
4. If planning, the graph runs Planner → Researcher → Synthesizer → Validator (with a max-2 refinement loop)
5. Streaming events flow back the entire time (agent status, partial itinerary, tool calls, validation reports)
6. Final state checkpointed so the next turn continues seamlessly

**Interrupt/resume:** LangGraph's `interrupt()` primitive is used when the Planner needs input mid-generation. The graph pauses, the frontend shows the question, the user replies, the graph resumes exactly where it stopped.

---

## 5. Engineering Principles & Standards (Must & Should Follow)

> These are the **non-negotiable engineering commitments** for TripPilot AI. Every design decision, PR, and code review must be justifiable against them. Where principles conflict, the rules in **§5.12 Conflict Resolution** apply. Nothing here is aspirational — this section is a checklist we hold ourselves to.

Two tiers throughout:
- **MUST** — hard requirement. A PR that violates these should not merge without explicit written justification.
- **SHOULD** — strongly preferred. Apply wherever it adds value; deviations must be justified in the PR description.

---

### 5.1 Software Design Principles (MUST)

1. **SOLID Principles** — every agent node, MCP server, and service class follows SRP, OCP, LSP, ISP, DIP
2. **Separation of Concerns (SoC)** — API layer, agent orchestration, MCP tools, and data layer stay strictly separated
3. **DRY (Don't Repeat Yourself)** — shared logic lives in `backend/app/services/` or `mcp_servers/shared/`
4. **KISS (Keep It Simple, Stupid)** — simpler design wins over cleverness at every review
5. **YAGNI (You Aren't Gonna Need It)** — no speculative abstractions; build for the MVP, not Phase 4
6. **Composition over Inheritance** — LangGraph nodes compose; no deep class hierarchies
7. **High Cohesion, Low Coupling** — each MCP server is self-contained; agents don't know about upstream APIs
8. **Principle of Least Astonishment (POLA)** — APIs, event names, and DB fields behave the way their name implies
9. **Law of Demeter (Least Knowledge)** — nodes talk to their immediate collaborators, not through chains
10. **Fail Fast** — Pydantic validation at every boundary; no silent coercion
11. **Defensive Programming** — assume every MCP response and LLM output can be malformed
12. **Separation of Interface and Implementation** — MCP tool contract is the interface; underlying API is swappable
13. **Immutability (where appropriate)** — LangGraph state is treated as immutable; new state per step
14. **Convention over Configuration** — sensible defaults in `config.py`; env vars only for what actually varies
15. **Single Source of Truth (SSOT)** — one canonical `Itinerary` schema; PDF, WebSocket, and DB all derive from it

> **Applied to TripPilot:** SoC and SSOT are the load-bearing ones for us. The agents must never touch external APIs directly — everything goes through MCP. The itinerary shape is defined once in `schemas/itinerary.py` and every consumer imports it.

---

### 5.2 Software Architecture Principles

**MUST follow:**
1. **Layered Architecture** — API → Service → Agent/Orchestrator → MCP/Data
2. **Clean Architecture** — inner layers (domain, agents) never depend on outer layers (frameworks, DBs)
3. **Hexagonal Architecture (Ports & Adapters)** — MCP servers are our adapters; agent code is the hexagon core
5. **Domain-Driven Design (DDD)** — `Trip`, `Itinerary`, `Conversation`, `DaySkeleton` are our bounded contexts
8. **Modular Monolith Architecture** — one deployable backend for MVP, structured so services can be extracted later
9. **Client-Server Architecture** — clean REST + WebSocket boundary between Next.js and FastAPI

**SHOULD follow (apply where it fits):**
4. **Onion Architecture** — equivalent to Clean; either framing is acceptable
6. **Event-Driven Architecture** — WebSocket streaming events already use this pattern; extend it for internal agent events
7. **Microservices Architecture** — Phase 4 only; MCP boundaries are our seams for later extraction
10. **Serverless Architecture** — MCP servers may run as serverless functions post-MVP; not required now

---

### 5.3 Backend Design Patterns (MUST use where the shape fits)

1. **Repository Pattern** — all DB access goes through `repositories/`; SQLAlchemy sessions never leak into agents
2. **Service Layer Pattern** — business logic lives in `services/`, not in FastAPI route handlers
3. **Unit of Work Pattern** — one transaction per request; commit at service boundary, not per query
4. **Dependency Injection** — FastAPI `Depends()` for services; agents receive MCP client via constructor
5. **Data Mapper Pattern** — Pydantic schemas map between DB models and API responses
6. **Active Record Pattern** — SHOULD avoid; we're using SQLAlchemy Core-style, not Django-style
7. **CQRS (Command Query Responsibility Segregation)** — SHOULD apply for `read trip` vs `plan trip` (they have very different shapes)
8. **Event Sourcing** — SHOULD apply to conversation events (already implicitly via LangGraph checkpoints)
9. **API Gateway Pattern** — FastAPI acts as the gateway; Phase 4 may extract a dedicated one
10. **Backend for Frontend (BFF)** — the FastAPI backend IS the BFF for the Next.js frontend

---

### 5.4 Gang of Four (GoF) Design Patterns (SHOULD — use where they genuinely fit)

> Rule: don't force a pattern. Use it when it makes the code clearer, skip it when it doesn't. KISS wins ties.

**Creational**
1. **Singleton** — the OpenAI client, MCP client pool, Redis pool
2. **Factory Method** — creating agent nodes based on route decision
3. **Abstract Factory** — LLM client factory (OpenAI now, Anthropic/others later)
4. **Builder** — constructing complex `Itinerary` objects in the Synthesizer
5. **Prototype** — cloning day skeletons for refinement variations

**Structural**
6. **Adapter** — `langchain-mcp-adapters` bridging MCP tools to LangChain
7. **Bridge** — separating LLM abstraction from concrete provider
8. **Composite** — an `Itinerary` is a composite of `Days` which are composites of `Blocks`
9. **Decorator** — caching, retry, and observability decorators on MCP client calls
10. **Facade** — service layer presents a simple face over agent + MCP + DB complexity
11. **Flyweight** — cached place details shared across itineraries
12. **Proxy** — cached MCP client proxies the real MCP call

**Behavioral**
13. **Chain of Responsibility** — Validator's ordered rule checks
14. **Command** — user refinement messages as command objects
15. **Interpreter** — parsing user constraints ("under ₹15k", "no early mornings")
16. **Iterator** — iterating days, blocks, candidate places
17. **Mediator** — the Conversation Manager mediates between user intent and specialist agents
18. **Memento** — LangGraph checkpoints ARE mementos
19. **Observer** — WebSocket clients observing agent progress events
20. **State** — conversation lifecycle (draft → planning → validated → refining → complete)
21. **Strategy** — routing strategy for `chit_chat` vs `plan` vs `refine`
22. **Template Method** — base MCP server class with tool-registration template
23. **Visitor** — traversing the itinerary to compute cost, feasibility, or export formats

---

### 5.5 API Design Principles (MUST)

1. **RESTful API Design** — resources over verbs, statelessness enforced
2. **Resource-Oriented Design** — `/trips`, `/trips/{id}/messages`, not `/planTrip`
3. **Proper HTTP Methods** — GET is safe & idempotent, POST creates, PATCH updates partial, DELETE removes
4. **Proper HTTP Status Codes** — 200/201/204/400/401/403/404/409/422/429/500 used correctly
5. **API Versioning** — `/api/v1/` prefix from day one
6. **Pagination** — all list endpoints paginated (cursor-based for messages, offset for trips)
7. **Filtering** — query params: `?status=complete&destination=kerala`
8. **Sorting** — `?sort=-created_at`
9. **Consistent Error Handling** — one error envelope: `{ error: { code, message, details } }`
10. **Idempotency** — `Idempotency-Key` header on trip creation and refinement submits
11. **Rate Limiting** — per-user (plan tier) and per-IP; 429 with `Retry-After`
12. **Request Validation** — Pydantic v2 at every endpoint; no manual dict poking
13. **Response Standardization** — all responses envelope-consistent
14. **OpenAPI/Swagger Documentation** — auto-generated from FastAPI; kept public

---

### 5.6 Database Design Principles (MUST)

1. **Database Normalization** — 3NF baseline for relational tables
2. **Denormalization (when appropriate)** — SHOULD; `itinerary JSONB` on `trips` is a deliberate denorm for read speed
3. **Indexing** — every FK indexed; every WHERE-clause column indexed after profiling
4. **Foreign Key Constraints** — enforced at DB level, not just app level
5. **ACID Transactions** — plan-commit spans one transaction; no dangling half-writes
6. **Eventual Consistency** — SHOULD; acceptable for cache, embeddings, analytics
7. **Optimistic Locking** — SHOULD; `updated_at` version check on trip edits
8. **Pessimistic Locking** — avoid; use only for critical section (e.g., quota decrement)
9. **Connection Pooling** — asyncpg pool sized to worker count; never open raw connections
10. **Soft Deletes** — `deleted_at` on `trips` and `conversations`; hard-delete via GDPR flow only
11. **Database Migrations** — every schema change is an Alembic migration; no manual DB edits in any environment
12. **Data Integrity** — CHECK constraints where meaningful (e.g., `budget_inr > 0`, `start_date <= end_date`)

---

### 5.7 Security Principles (MUST — no exceptions)

1. **Authentication** — JWT for API, signed WebSocket tokens for streaming
2. **Authorization** — every endpoint checks resource ownership
3. **Principle of Least Privilege** — DB user has only needed grants; API keys scoped to minimum
4. **Role-Based Access Control (RBAC)** — `user`, `admin`; extensible via roles table
5. **Attribute-Based Access Control (ABAC)** — SHOULD; for future team/collab features
6. **OAuth 2.0** — Google sign-in via standard OAuth 2.0 flow
7. **OpenID Connect** — used with Google OAuth for identity claims
8. **JWT Authentication** — short-lived access token + refresh token; HS256 or RS256
9. **Password Hashing** — argon2 or bcrypt (never MD5/SHA1/plaintext)
10. **Input Validation** — Pydantic at API boundary, MCP schema at tool boundary
11. **Output Encoding** — React handles by default; server-rendered strings escape explicitly
12. **SQL Injection Prevention** — parameterized queries via SQLAlchemy; NO string interpolation into SQL, ever
13. **XSS Prevention** — React auto-escape + CSP header
14. **CSRF Protection** — SameSite=Lax cookies + CSRF tokens for state-changing forms
15. **Secure Secrets Management** — env vars via Replit/Vercel secrets; never in code, never in logs
16. **HTTPS Everywhere** — HSTS enabled; HTTP requests 301'd
17. **CORS Configuration** — explicit allowlist of frontend origins; no `*` in production
18. **Rate Limiting** — Redis-backed sliding window; per-user and per-IP tiers
19. **API Keys** — hashed at rest; scoped to single MCP server; rotatable
20. **Audit Logging** — auth events, permission changes, and destructive actions logged with actor + timestamp

---

### 5.8 Code Quality Principles (MUST)

1. **Clean Code** — small functions, meaningful names, minimal comments explaining "why" not "what"
2. **Readability** — code is read 10× more than written; optimize for the reader
3. **Maintainability** — a new contributor should ship a small fix in <1 day
4. **Reusability** — extract only after the third occurrence; not before
5. **Simplicity** — the boring solution wins over the clever one
6. **Consistent Naming** — snake_case Python, camelCase TS, PascalCase types; no ambiguous abbreviations
7. **Code Reviews** — every PR reviewed; solo commits to `main` are prohibited
8. **Refactoring** — Boy Scout Rule: leave code cleaner than you found it
9. **Documentation** — every module has a docstring; every public function has typed signatures
10. **Static Code Analysis** — mypy (strict) on backend, TS strict mode on frontend
11. **Linting** — ruff for Python, ESLint for TS; CI-enforced
12. **Formatting** — black + ruff format for Python, Prettier for TS; pre-commit hooks

---

### 5.9 AI / LLM Engineering Patterns (MUST for anything touching agents)

1. **Prompt Engineering** — prompts are code; treat them with the same review rigor
2. **Prompt Templates** — versioned files under `agents/prompts/`; no inline string prompts in nodes
3. **Structured Outputs** — every LLM call uses `response_format={"type": "json_schema"}` or Pydantic parsing
4. **Function Calling / Tool Calling** — MCP tools bound via `bind_tools()`; no ad-hoc tool JSON
5. **Retrieval-Augmented Generation (RAG)** — Planner pulls destination knowledge from pgvector before generating
6. **Agentic Workflows** — LangGraph is the only orchestration primitive; no ad-hoc chains
7. **Multi-Agent Systems** — nodes are our agents; each has one job (see §9)
8. **Conversation Memory** — LangGraph Postgres checkpoints; nothing bespoke
9. **Semantic Search** — pgvector for "similar destinations", "similar past trips"
10. **Vector Databases** — pgvector; no separate service until scale demands it
11. **Embeddings** — OpenAI `text-embedding-3-small` for MVP; abstract behind an interface
12. **Streaming Responses** — every LLM call streams; WebSocket forwards tokens to UI
13. **LLM Evaluation** — golden prompt set + eval run on every agent-touching PR (see §14)
14. **LLM-as-a-Judge** — used for subjective quality scoring in evals
15. **Prompt Versioning** — prompt files versioned in Git; changes require review + eval delta
16. **AI Guardrails** — validator node is a guardrail; input sanitization is a guardrail; refuse out-of-domain requests
17. **Hallucination Detection** — Validator cross-checks LLM claims against MCP-grounded facts
18. **Confidence Scoring** — SHOULD; expose LLM confidence in structured outputs where useful
19. **Caching** — LLM response cache (Redis, 24h) on identical inputs
20. **Fallback Models** — GPT-4o-mini fallback if GPT-4o fails/times out; circuit breaker
21. **Retry Strategies** — exponential backoff with jitter; max 3 retries; total budget cap
22. **Human-in-the-Loop** — `interrupt()` primitive for clarifications; user always has veto on refinements
23. **AI Observability** — every LLM call logged: model, tokens, latency, cost, prompt hash
24. **AI Cost Optimization** — per-trip budget cap, per-user rate limit, cheap-model routing (see §9)

---

### 5.10 Scalability & Performance Principles

**MUST for MVP:**
1. **Caching** — Redis for MCP tool results, LLM responses, session state
2. **Asynchronous Processing** — all I/O is async; blocking calls in agent path are a bug
4. **Async Processing** — long-running planning offloaded to background workers post-MVP
8. **Load Balancing** — Replit handles L4; Vercel handles frontend; add L7 when moving off Replit

**SHOULD apply as scale demands:**
2. **Lazy Loading** — itinerary details paginated by day; PDF generated on demand
3. **Eager Loading** — SQLAlchemy `selectinload` for N+1 avoidance
5. **Message Queues** — ARQ/Celery for background trip generation post-MVP
6. **Horizontal Scaling** — stateless FastAPI workers; state in Postgres/Redis
7. **Vertical Scaling** — acceptable interim for MVP; not the long-term answer
9. **Database Sharding** — Phase 4+ only
10. **Read Replicas** — Phase 3+; Neon supports this natively
11. **CDN Usage** — Vercel handles frontend CDN; static MCP outputs cached at edge later
12. **Batch Processing** — MCP calls batched where API allows (e.g., Places bulk lookups)

---

### 5.11 Software Engineering Practices (MUST)

1. **Agile Development** — iterative delivery; weekly demos; no big-bang releases
2. **Scrum** — SHOULD; use lightweight scrum only if team grows past two
3. **Kanban** — used now: GitHub Projects board with `todo / in-progress / review / done`
4. **Git Flow** — SHOULD; `feature/*` branches off `main`, PR review, squash-merge
5. **Trunk-Based Development** — MUST for MVP; short-lived branches, main always deployable
6. **Semantic Versioning** — `MAJOR.MINOR.PATCH` on backend, frontend, and each MCP server
7. **Code Reviews** — every PR reviewed before merge; no self-approvals
8. **Pair Programming** — SHOULD; used for hard debugging and knowledge sharing
9. **Continuous Refactoring** — refactor tickets are first-class, not "we'll get to it"
10. **Documentation-Driven Development** — non-trivial features start with a short design doc in `docs/`

---

### 5.12 Conflict Resolution — When Principles Clash

Principles collide constantly. Here's the tie-breaking order for TripPilot:

1. **Security beats convenience.** Always. No exceptions.
2. **Feasibility validation beats LLM opinion.** The deterministic Validator is the source of truth for facts; the LLM is a suggestion engine.
3. **KISS beats pattern adoption.** Don't force a GoF pattern where a plain function is clearer.
4. **YAGNI beats speculative flexibility.** No abstraction layers "for the future." Add them the day the second use case appears.
5. **Fail Fast at boundaries beats Defensive Programming internally.** Validate hard at API/MCP/DB edges; trust internal contracts.
6. **Clean Architecture beats DRY across bounded contexts.** Some duplication between `agents/` and `mcp_servers/` is honest — don't share code just because it looks similar.
7. **Explicitness beats Convention where behavior surprises.** Convention over Configuration is great until it isn't obvious what's happening.
8. **Cost discipline beats capability maximalism.** Cheaper model + caching + validator loop > "just use GPT-4o for everything."

Every PR that touches these tensions should call out the trade-off in its description.

---

## 6. MVP Scope (Phase 1 — 12 weeks)

### In scope
- ✅ Email + Google auth
- ✅ Conversational trip planning (multi-turn, clarifying questions)
- ✅ Day-by-day itinerary with hour blocks
- ✅ Budget breakdown (transport / stay / food / activities)
- ✅ Map view with attraction markers and daily routes
- ✅ Bus route recommendations (via Rome2Rio MCP)
- ✅ Mid-conversation refinement ("skip day 3, add a beach")
- ✅ Save trips to profile
- ✅ Conversation history per trip
- ✅ PDF export
- ✅ Weather integration
- ✅ Streaming UI showing agent progress and tool calls
- ✅ 5 core MCP servers: places, weather, directions, buses, currency

### Explicitly OUT of scope for v1
- ❌ Flight/train booking (recommend only)
- ❌ Complex multi-agent negotiation
- ❌ Instagram/YouTube reel parsing
- ❌ Collaboration / group trips
- ❌ Gamification / badges
- ❌ AR navigation
- ❌ Voice input/output
- ❌ Expense tracker
- ❌ Push notifications
- ❌ Third-party MCP server marketplace

---

## 7. Feature Roadmap

### Phase 1 — MVP (Weeks 1–12)
Conversational loop with 5 MCP tools, itinerary generation, refinement, save, export.

### Phase 2 — Depth (Weeks 13–20)
- Trains MCP server (RailwayAPI)
- Hotels MCP server (Booking.com or Google Hotels)
- Smart replanning after schedule slips
- Packing assistant agent
- Expense tracker
- Safety & local intelligence agent
- Multi-language support (Hindi, Tamil, Kannada, Telugu)

### Phase 3 — Delight (Weeks 21–32)
- Collaborative trip planning
- Instagram reel → trip
- Photo-based destination discovery
- Voice input via Whisper API
- Gamification (badges, streaks)
- Carbon-aware planning MCP tool

### Phase 4 — Scale (Beyond)
- Mobile app (React Native or Expo)
- International trips
- Group coordination
- Marketplace for local guides
- Offline mode
- Publish MCP servers publicly (let others build on them)

---

## 8. Repository Structure

```
tripilot-ai/
├── backend/
│   ├── app/                            # FastAPI app (agent orchestrator)
│   │   ├── main.py
│   │   ├── config.py                   # pydantic-settings
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── auth.py
│   │   │   │   ├── trips.py
│   │   │   │   ├── chat.py             # WebSocket for conversation
│   │   │   │   └── users.py
│   │   │   └── deps.py
│   │   ├── agents/
│   │   │   ├── graph.py                # LangGraph definition (conversational)
│   │   │   ├── state.py                # ConversationState schema
│   │   │   ├── checkpointer.py         # Postgres checkpoint saver
│   │   │   ├── nodes/
│   │   │   │   ├── conversation_manager.py
│   │   │   │   ├── intake.py
│   │   │   │   ├── planner.py
│   │   │   │   ├── researcher.py
│   │   │   │   ├── synthesizer.py
│   │   │   │   ├── validator.py
│   │   │   │   └── refiner.py
│   │   │   └── prompts/                # Prompt templates
│   │   ├── mcp/
│   │   │   ├── client_pool.py          # Manages connections to MCP servers
│   │   │   └── config.py               # MCP server registry
│   │   ├── models/                     # SQLAlchemy models
│   │   ├── schemas/                    # Pydantic schemas
│   │   ├── services/
│   │   ├── db/
│   │   │   ├── session.py
│   │   │   └── migrations/             # Alembic
│   │   └── core/
│   │       ├── security.py
│   │       ├── logging.py
│   │       └── openai_client.py        # OpenAI client factory
│   ├── mcp_servers/                    # Standalone MCP servers
│   │   ├── places/
│   │   │   ├── server.py               # FastMCP server
│   │   │   ├── google_places.py        # Google Places API client
│   │   │   └── Dockerfile
│   │   ├── weather/
│   │   │   ├── server.py
│   │   │   ├── openweather.py
│   │   │   └── Dockerfile
│   │   ├── directions/
│   │   │   ├── server.py
│   │   │   ├── mapbox.py
│   │   │   └── Dockerfile
│   │   ├── buses/
│   │   │   ├── server.py
│   │   │   ├── rome2rio.py
│   │   │   └── Dockerfile
│   │   ├── currency/
│   │   │   ├── server.py
│   │   │   └── Dockerfile
│   │   └── shared/                     # Common utilities (auth, caching, schemas)
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── mcp/                        # MCP server tests
│   │   └── evals/                      # Agent quality evals
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── .env.example
│
├── frontend/
│   ├── app/                            # Next.js 14 App Router
│   │   ├── layout.tsx
│   │   ├── page.tsx                    # Landing
│   │   ├── (auth)/
│   │   ├── dashboard/
│   │   ├── trip/[id]/                  # Trip view + chat
│   │   └── new/                        # New trip flow
│   ├── components/
│   │   ├── chat/                       # Conversation UI
│   │   ├── itinerary/
│   │   ├── map/
│   │   ├── budget/
│   │   └── ui/                         # shadcn components
│   ├── lib/
│   │   ├── api.ts
│   │   ├── ws.ts                       # WebSocket client
│   │   └── store.ts                    # Zustand
│   ├── hooks/
│   ├── public/
│   ├── next.config.mjs
│   ├── tailwind.config.ts
│   └── package.json
│
├── docker-compose.yml                  # backend + postgres + redis + MCP servers
├── .github/
│   └── workflows/
│       ├── backend-ci.yml
│       ├── frontend-ci.yml
│       └── mcp-servers-ci.yml
├── docs/
│   ├── ARCHITECTURE.md
│   ├── AGENTS.md
│   ├── MCP_SERVERS.md
│   └── API.md
├── PROJECT_PLAN.md                     # this file
└── README.md
```

---

## 9. Agent System Design (Deep Dive)

### Design principles
1. **One agent, one job.** Each node has a single, testable responsibility.
2. **Structured state, not raw messages.** Nodes read/write typed Pydantic objects; the message log is separate.
3. **Tools speak MCP.** All tool calls go through the MCP client pool. Agent code doesn't know about Google Places specifically — only about the `places` MCP server.
4. **Bounded loops.** Max 2 refinement iterations, then ship with a warning.
5. **Conversation over completion.** The system's default posture is *dialog*, not batch generation.
6. **Streaming by default.** Every node emits progress events over WebSocket.

### Node contracts

**Conversation Manager (router)**
- Input: user message + full conversation state
- Output: routing decision — `chit_chat` | `clarify` | `plan` | `refine`
- LLM: GPT-4o-mini with structured output (`response_format` → enum)
- Also generates chit-chat responses inline

**Intake**
- Input: raw user string(s) across turns
- Output: `TripRequest { destination, dates, budget_inr, party_size, preferences[] }`
- Behavior: if any required field is missing/ambiguous, calls `interrupt()` to ask
- LLM: GPT-4o-mini with structured output

**Planner**
- Input: `TripRequest`
- Output: `DaySkeleton[] { day, theme, target_areas[], meal_slots }`
- LLM: GPT-4o
- Uses RAG: pulls destination knowledge from pgvector before generating

**Researcher**
- Input: `DaySkeleton[]`
- Output: `ResearchBundle { candidate_places, weather_by_day, transport_options, bus_routes }`
- **No LLM** — pure MCP tool orchestration. Parallel calls to `places`, `weather`, `directions`, `buses`.
- Aggressive Redis caching

**Synthesizer**
- Input: `TripRequest + DaySkeleton[] + ResearchBundle`
- Output: `Itinerary { days: [{ blocks: [{ time, activity, location, cost, notes }] }] }`
- LLM: GPT-4o with `response_format={"type": "json_schema", ...}` (strict structured output)

**Validator**
- Input: `Itinerary + ResearchBundle`
- Output: `ValidationReport { is_valid, issues[] }`
- **No LLM** — deterministic Python checks:
  - Every place open at scheduled time?
  - Drive time between consecutive blocks realistic?
  - Total cost within budget + 10% buffer?
  - Meal slots present at reasonable times?
  - Pacing not too dense (max ~5 activities/day)?

**Refiner**
- Input: `Itinerary + ValidationReport` OR user refinement message
- Output: revised `Itinerary` (or loops back to Planner)
- LLM: GPT-4o
- Streams the diff to the frontend so the user sees exactly what changed

### MCP Integration

Every tool the agents use is defined as an MCP server. Example — `buses` server:

```python
# backend/mcp_servers/buses/server.py
from fastmcp import FastMCP
from .rome2rio import Rome2RioClient

mcp = FastMCP("buses")
client = Rome2RioClient()

@mcp.tool()
async def search_bus_routes(
    origin: str,
    destination: str,
    date: str,
) -> BusRouteResults:
    """Find bus routes between two cities on a given date.

    Returns operators, timings, durations, price estimates, and
    booking deep-links for RedBus / AbhiBus.
    """
    return await client.search(origin, destination, date)

@mcp.tool()
async def get_bus_operators(city: str) -> list[BusOperator]:
    """List major bus operators departing from a city."""
    return await client.operators(city)

if __name__ == "__main__":
    mcp.run(transport="stdio")  # or "http" for remote
```

Inside LangGraph, the Researcher node consumes these via `langchain-mcp-adapters`:

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

mcp_client = MultiServerMCPClient({
    "places":     {"command": "python", "args": ["-m", "mcp_servers.places"]},
    "weather":    {"command": "python", "args": ["-m", "mcp_servers.weather"]},
    "directions": {"command": "python", "args": ["-m", "mcp_servers.directions"]},
    "buses":      {"command": "python", "args": ["-m", "mcp_servers.buses"]},
    "currency":   {"command": "python", "args": ["-m", "mcp_servers.currency"]},
})

tools = await mcp_client.get_tools()
# tools is now a list of LangChain-compatible tool objects
# bind them to the OpenAI model:
llm_with_tools = openai_llm.bind_tools(tools)
```

### Why MCP is worth the complexity
- **Provider swaps are trivial** — replace Google Places with Foursquare by rewriting one MCP server; agent code untouched
- **Tools can be tested in isolation** — spin up the `buses` server locally with `python -m mcp_servers.buses` and hit it with the MCP inspector
- **Deployment flexibility** — MCP servers can run in-process (stdio transport) for MVP, split into microservices (HTTP transport) later, without code changes to the agents
- **Future-proof** — can expose our MCP servers publicly later so others can use TripPilot as a data source

### Cost controls
- Route cheap decisions (Conversation Manager, Intake, Validator triage) to **GPT-4o-mini**
- Route planning + synthesis + refinement to **GPT-4o**
- Cache LLM responses on identical prompts (Redis, 24h TTL)
- Cache MCP tool responses aggressively (places 7d, weather 1h, directions 1d, buses 6h)
- Hard token budget per trip generation (target: <$0.12 per full plan)
- Track cost per user in DB; rate limit per tier

---

## 10. Data Layer

### Core tables

```sql
users (id, email, google_id, name, preferences JSONB, created_at)

trips (
  id, user_id, title, destination, start_date, end_date,
  budget_inr, status, itinerary JSONB, created_at, updated_at
)

conversations (
  id, trip_id, thread_id UUID, created_at
)

messages (
  id, conversation_id, role, content,
  agent_events JSONB,      -- streamed events (tool calls, agent progress)
  created_at
)

langgraph_checkpoints (
  thread_id, checkpoint_id, parent_id, checkpoint JSONB, metadata JSONB
)  -- managed by LangGraph's Postgres saver

mcp_tool_cache (key, value JSONB, expires_at)

place_embeddings (
  id, place_id, embedding vector(1536), metadata JSONB
)

llm_calls (
  id, user_id, trip_id, model, input_tokens, output_tokens,
  cost_usd, latency_ms, created_at
)
```

### Why JSONB for itineraries and events
Itinerary shape will evolve. Agent event streams have variable shapes per node. Rigid columns will fight us. We validate everything with Pydantic at the app boundary; JSONB is just storage.

### pgvector usage
- Embed places and destination knowledge base
- Semantic search: "find similar destinations to Coorg" → vector similarity
- RAG for the Planner node: retrieve relevant destination context before generating skeleton

### LangGraph Checkpointing
The Postgres checkpointer stores the full conversation state on every graph step. This is what makes the conversation feel continuous — reconnect three days later, resume exactly where you left off, agents remember what was already decided.

---

## 11. API Design

### REST endpoints (v1)

```
POST   /auth/register            # Email signup
POST   /auth/login               # JWT issue
POST   /auth/google              # Google OAuth callback
GET    /me                       # Current user profile
PATCH  /me/preferences

POST   /trips                    # Create trip shell + start conversation
GET    /trips                    # List user's trips
GET    /trips/{id}               # Get trip details + latest itinerary
GET    /trips/{id}/messages      # Full conversation history
PATCH  /trips/{id}               # Update trip metadata
DELETE /trips/{id}               # Delete trip
GET    /trips/{id}/pdf           # Download PDF
```

### WebSocket (the core interaction)

```
WS /ws/trips/{id}/chat

→ Client sends: { type: "user_message", content: "..." }

← Server streams:
  { type: "route_decision", route: "plan" }
  { type: "agent_start", agent: "planner" }
  { type: "agent_thinking", agent: "researcher", detail: "Fetching bus routes..." }
  { type: "tool_call", server: "buses", tool: "search_bus_routes", input: {...} }
  { type: "tool_result", server: "buses", output_summary: "3 routes found" }
  { type: "partial_itinerary", data: {...} }
  { type: "clarification_request", question: "Do you want to include Alleppey backwaters?" }
  { type: "validation_report", issues: [...] }
  { type: "assistant_message", content: "..." }
  { type: "complete", itinerary: {...} }
  { type: "error", message: "..." }
```

The frontend renders these events as a live "agent working" experience — the user sees the buses MCP tool being called, the results coming back, the plan being assembled. This transparency is a feature, not just debug output.

---

## 12. Deployment

### Local development
```bash
docker compose up  # backend + postgres + redis + all MCP servers
cd frontend && pnpm dev
```

For MVP, MCP servers run **in-process** as stdio subprocesses spawned by the main FastAPI backend. No separate containers needed. This is the simplest setup and works well on Replit.

### Backend → Replit
- `.replit` config runs `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Secrets: `OPENAI_API_KEY`, `GOOGLE_PLACES_KEY`, `OPENWEATHER_KEY`, `MAPBOX_TOKEN`, `ROME2RIO_KEY`, `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`
- Use Neon (Postgres) + Upstash (Redis) — free tiers, more reliable than Replit's built-ins
- Enable "Always On" for demo periods

**Replit caveat:** LLM + tool orchestration can take 30–90s for a full plan. Use WebSockets exclusively for generation — HTTP will time out. Ping/pong keepalives every 20s.

### Frontend → Vercel
- Connect the GitHub repo
- Set `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_WS_URL` to Replit URLs
- Vercel previews per PR automatically

### CI/CD
- On PR: run tests, linters, type checks (backend + frontend + each MCP server)
- On merge to main: build backend Docker image; push; trigger Replit redeploy via webhook
- Frontend redeploys automatically via Vercel

### Migration path (post-MVP)
When ready to leave Replit:
- Backend Docker image → Railway or Fly.io
- MCP servers split into independent Docker services (HTTP transport)
- Postgres/Redis stay on Neon/Upstash
- Frontend stays on Vercel
- Zero code changes needed — that's the whole point of MCP

---

## 13. Cost Model

### LLM budget targets (OpenAI pricing, approx. as of writing)

| Item | Model | Est. cost per full trip |
|---|---|---|
| Conversation Manager (per turn) | GPT-4o-mini | $0.0005 |
| Intake | GPT-4o-mini | $0.001 |
| Planner | GPT-4o | $0.03 |
| Researcher (no LLM) | — | $0.00 |
| Synthesizer | GPT-4o | $0.05 |
| Validator (no LLM) | — | $0.00 |
| Refiner (avg 0.5 loops) | GPT-4o | $0.02 |
| **Total per trip** | | **~$0.10** |
| **+ per refinement message** | | **~$0.02** |

### External APIs
- Google Places: ~$17 per 1000 Place Details requests. Cache 7 days.
- OpenWeatherMap: free tier = 1000 calls/day.
- Mapbox: free 50k requests/mo.
- Rome2Rio: partner pricing, usually ~$0.005–0.01 per request. Cache 6h.

### Infrastructure (monthly, MVP scale)
- Replit "Hacker" or Reserved VM: $7–20
- Neon Postgres free tier: $0 (upgrade at ~1GB)
- Upstash Redis free tier: $0
- Vercel Hobby: $0
- **Total infra: <$20/mo**

### Break-even math
At $0.10 LLM + $0.05 tool costs = ~$0.15 per full trip. At 500 trips/month = ~$75 in variable costs. Free tier absorbs this comfortably; monetization can come later.

---

## 14. Testing Strategy

### Unit tests
- Every MCP server tested with mocked upstream APIs
- Validator logic tested exhaustively (deterministic Python — no excuse for gaps)
- Pydantic schemas validated with edge cases
- Conversation router tested with example turns

### Integration tests
- Full graph run against mocked MCP servers + deterministic LLM stubs
- WebSocket streaming tested end-to-end
- Database migrations tested on clean DB
- Checkpoint save/restore tested for continuity

### MCP-specific tests
- Each MCP server can be exercised with the MCP Inspector CLI
- Schema conformance tests (input/output types match declared schemas)
- Contract tests: agents mock MCP servers with recorded fixtures

### Agent evals (this is where AI projects usually fail)
```
tests/evals/
├── golden_prompts.jsonl       # 20-50 real prompts
├── run_evals.py               # Runs each through the graph
└── judges.py                  # LLM-as-judge for quality
```

Metrics tracked per eval run:
- Validation pass rate (% of itineraries that pass Validator)
- Budget adherence (within ±10%)
- Feasibility (drive times fit slots)
- LLM-judged quality score (1-5)
- Turns-to-completion (fewer is usually better)
- Latency p50/p95
- Cost per trip

Run evals on every PR that touches `agents/` or any MCP server.

### E2E tests
Playwright: signup → conversation → itinerary → refinement → export.

---

## 15. Timeline (12-Week MVP)

| Week | Focus | Deliverable |
|---|---|---|
| 1 | Setup | Repo scaffolded, Docker Compose runs, CI green, empty FastAPI + Next.js deployed |
| 2 | Auth + DB | Google OAuth + JWT, users/trips/conversations schema, Alembic migrations |
| 3 | MCP infra + first server | MCP client pool, `weather` MCP server (simplest), integrated end-to-end |
| 4 | Core MCP servers | `places`, `directions`, `buses` (Rome2Rio), `currency` all live |
| 5 | LangGraph skeleton | Conversational graph structure, checkpointing, streaming events |
| 6 | Intake + Planner | GPT-4o wired, structured outputs, clarification via `interrupt()` |
| 7 | Researcher + Synthesizer | First real itineraries generating from real data |
| 8 | Validator + Refiner | Validation loop; refinement via chat working |
| 9 | Frontend: chat + streaming | Chat UI, WebSocket integration, agent progress + tool-call display |
| 10 | Frontend: itinerary + map | Timeline, Mapbox integration, budget breakdown |
| 11 | Save/load + PDF + deploy | Trip persistence, PDF export, Replit + Vercel live, Sentry |
| 12 | Evals + docs + launch | Eval suite, README, demo video, ship v1 |

Buffer: assume 2 weeks slippage. Plan realistically for 14 weeks.

---

## 16. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| LLM costs spiral | Medium | High | Aggressive caching, GPT-4o-mini for routing, per-user rate limits, cost dashboard from day 1 |
| Google Places API too expensive | Medium | Medium | Cache 7 days, evaluate Foursquare fallback (easy — just swap MCP server) |
| Rome2Rio quota / cost issues | Medium | Medium | Cache 6h, fallback to Google Places transit + direct scraping for MVP |
| Replit reliability issues | Medium | High | Keep Docker portable, plan Railway migration path |
| MCP protocol immaturity / breaking changes | Low | Medium | Pin MCP SDK versions, contribute to spec if needed |
| Hallucinated places / hours | High | High | Validator + tool grounding (never trust LLM for facts) |
| Agent loops burn tokens | Medium | Medium | Hard retry cap (2), timeout per node, cost circuit breaker |
| Conversation state gets corrupted | Medium | High | Immutable checkpoints, versioned state schema |
| Scope creep from feature list | Very High | Very High | This document. Say no. Ship MVP first. |
| No users on launch | High | Medium | Reddit r/india + r/travel, Product Hunt, targeted India-travel subreddits |
| Feasibility validation is wrong | Medium | High | Manual review of 20 test itineraries; iterate on Validator rules |

---

## 17. Next Steps

**Immediate (this week):**
1. Scaffold backend: FastAPI app, config, Docker, health endpoint
2. Set up LangGraph conversational graph skeleton: state schema, checkpointer, empty nodes
3. Create the first MCP server (`weather` — simplest) to validate the MCP integration pattern
4. Commit this `PROJECT_PLAN.md` to the repo
5. Create GitHub issues from Week 1–2 tasks
6. Set up basic CI

**Week 2:**
1. Implement auth
2. Create Alembic migrations for users/trips/conversations
3. Stand up Postgres + Redis in Docker Compose
4. Deploy empty backend to Replit + frontend to Vercel end-to-end

The **very next action** is scaffolding the FastAPI backend + LangGraph agent skeleton (with MCP wiring stub) — that's what we're building next.

---

## Appendix A — Key Design Decisions Log

- **2026-07-13:** Chose LangGraph over CrewAI. Reason: checkpointing for conversation memory, interrupt/resume for clarifications, better streaming, more mature.
- **2026-07-13:** Chose pgvector over separate vector DB. Reason: one less service, sufficient scale for MVP.
- **2026-07-13:** Chose linear graph + validation loop over autonomous multi-agent. Reason: predictable, cheaper, easier to debug.
- **2026-07-13:** Chose Replit for MVP backend deployment. Reason: fast to start, easy to demo. Migration path to Railway/Fly kept open via Docker.
- **2026-07-13:** Switched to OpenAI as primary LLM. Reason: mature structured outputs, strong function calling, integrates cleanly with OpenAI Agents SDK and LangChain adapters.
- **2026-07-13:** Adopted MCP for all tool integrations. Reason: provider-agnostic, testable in isolation, deployment flexibility, future-proof for public MCP server ecosystem.
- **2026-07-13:** Added Rome2Rio as the buses (and multi-modal transport) API. Reason: single API covers bus/train/flight/car for Indian cities; RedBus/AbhiBus have no public API for non-partners.
- **2026-07-13:** Reframed architecture as conversational-first. Reason: forms and one-shot generation feel dated; multi-turn dialog with clarification is the point.
- **2026-07-13:** Adopted formal Engineering Principles & Standards (§5) as project commitments — SOLID, Clean Architecture, MCP as Ports & Adapters, security-by-default, and the full AI/LLM engineering pattern set. Reason: an agentic system fails silently and expensively without hard discipline; the principles section is the checklist we hold PRs to.

## Appendix B — Non-Goals

Things we are consciously *not* doing, and why:

- **Building our own booking flow** — booking is a commodity; we're a planner. Deep-link to partners.
- **Real-time flight prices** — expensive API, low added value for the planning stage.
- **Native mobile apps** — Next.js PWA is enough for v1; native comes with real users.
- **General-purpose chat** — this is a trip planner. Constrain the domain to stay useful.
- **Serving international destinations at launch** — India-first gives us focus and defensible knowledge.
- **A public MCP server marketplace at launch** — cool idea, but a Phase 4 problem.

---

*This document is living. Update it as decisions change.*
