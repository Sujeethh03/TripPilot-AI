# CLAUDE.md — TripPilot AI

Read this at the start of every session before doing anything else. It tells you what this project is, how we work, and where to look.

## What this is

TripPilot AI is a conversational, agentic travel planner for Indian trips. The user talks in plain language ("5 days, ₹20k, Kerala, waterfalls and street food") and a LangGraph-orchestrated team of agents asks clarifying questions, researches real options through MCP tool servers, builds an hour-by-hour itinerary, validates it deterministically, and refines it live.

**Full spec:** `PROJECT_PLAN.md` — the source of truth for vision, architecture, tech stack, scope, and timeline. Read it before proposing anything structural.

**Current status & history:** `PROGRESS.md` — read this every session to see what's done, what's in flight, and what's next. Keep it updated as we work.

## Stack (see PROJECT_PLAN.md §3 for the full table)

- **Backend:** Python 3.11+, FastAPI, LangGraph (orchestration), FastMCP (tool servers), SQLAlchemy 2.0 async, Pydantic v2, Alembic
- **LLM:** OpenAI (GPT-4o / GPT-4o-mini). This is an OpenAI project — do not swap in other providers without asking.
- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind, shadcn/ui, Zustand, TanStack Query
- **Data:** PostgreSQL 16 + pgvector, Redis
- **Tools:** every external API (Places, Weather, Directions, Buses, Currency) is wrapped in its own MCP server. Agents never call external APIs directly — always through the MCP client pool.

## How we work

- **Sujeeth writes the code; you pair.** Explain trade-offs, propose approaches, and let him make the calls. This is a portfolio project he must be able to defend end-to-end, so don't hand him code he can't explain.
- **KISS and YAGNI win.** Build for the MVP, not Phase 4. Don't add abstractions until the second use case appears. The pattern list in PROJECT_PLAN.md §5 is aspirational — apply a principle only where it genuinely earns its place.
- **Agents never touch external APIs directly.** Everything goes through MCP. The `Itinerary` schema is defined once and every consumer imports it (SSOT).
- **Feasibility is deterministic.** The Validator node is plain Python, not an LLM. Never trust the LLM for facts (opening hours, drive times, prices).
- **Ask before big moves.** New dependencies, schema changes, or architectural shifts get discussed first.

## Git conventions

- **Author is always Sujeeth**, never Claude. Do not add `Co-Authored-By: Claude` trailers to commits on this repo.
- **Commit messages are short and human** — lowercase, plain, no ceremony. E.g. `add weather mcp server`, `fix budget rounding`, `wire up chat websocket`. No "feat:/chore:" prefixes, no generated-with footers.
- Commit or push only when Sujeeth asks.
- Remote: `https://github.com/Sujeethh03/TripPilot-AI.git` (origin, main).

## When you start a session

1. Read `PROGRESS.md` to see where we left off.
2. Skim the relevant part of `PROJECT_PLAN.md` for whatever we're touching.
3. Pick up the next task, or ask what to work on.
4. Update `PROGRESS.md` as things move.
