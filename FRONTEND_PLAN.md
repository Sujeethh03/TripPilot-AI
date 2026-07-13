# FRONTEND_PLAN.md — TripPilot AI (Frontend)

The source-of-truth spec for the Next.js frontend. Read this before touching the
`frontend/` app. It mirrors what `PROJECT_PLAN.md` is for the backend, but is
grounded in the **actually implemented** backend contract (see §3), not the
aspirational one. Where the two differ, this file wins for frontend work.

Keep it honest: update the "Build order" checkboxes here and the running log in
`PROGRESS.md` as we go, same as the backend.

---

## 1. Purpose & scope

TripPilot's frontend is a **conversational trip-planning UI**. The whole product
is the chat: the user talks in plain language, watches a team of agents work in
real time (routing → planning → researching → synthesizing → validating), and
sees an hour-by-hour itinerary assemble and refine live. Everything else
(auth, trip list) is scaffolding around that one experience.

**MVP goal:** a logged-in user can create a trip, chat to plan it, watch the
agents stream progress, see the itinerary render and update on refine turns, and
download the PDF.

**In scope (MVP):** auth (email + Google), trip dashboard, new-trip flow, the
trip/chat view with live streaming, itinerary timeline, budget summary, PDF
download.

**Out of scope (defer):** Mapbox map, pgvector-powered "similar destinations",
`interrupt()`/clarification UI (backend doesn't emit it yet — see §3), collaborative
editing, mobile-native. Build the seams so these slot in later; don't build them now.

---

## 2. Stack (from PROJECT_PLAN §3 — do not swap without asking)

| Concern | Choice | Notes |
|---|---|---|
| Framework | Next.js 14, App Router | RSC where it helps; the chat view is a client component |
| Language | TypeScript, `strict` | Matches backend's mypy-strict discipline |
| Styling | Tailwind CSS | |
| Components | shadcn/ui | Own the code, accessible defaults |
| Client state | Zustand | Chat/streaming state (see §5) |
| Server state | TanStack Query | Trips, messages, user — caching + mutations |
| Forms | React Hook Form + Zod | Type-safe; Zod schemas mirror backend Pydantic |
| Package manager | pnpm | Per PROJECT_PLAN (`pnpm dev`) |
| Hosting | Vercel | |

**Principle:** KISS/YAGNI, same as backend. Zustand holds only what's genuinely
client-side and ephemeral (the live event stream for the open trip). Everything
that lives in the DB is TanStack Query's job — don't duplicate it into Zustand.

---

## 3. Backend contract (implemented — build against THIS)

Base URL: `http://localhost:8000`. REST is under `/api/v1`; the WebSocket has no
prefix. CORS already allows `http://localhost:3000`.

### Auth
- `POST /api/v1/auth/register` → `201` `{ id, email, name }` (or `409` on dup).
  Body: `{ email, password (>=8), name? }`.
- `POST /api/v1/auth/login` → `{ access_token, token_type: "bearer" }` (or `401`).
  Body: `{ email, password }`.
- `POST /api/v1/auth/google` → `{ access_token, token_type }` (or `401`).
  Body: `{ id_token }` — the Google Sign-In ID token from the browser SDK.
- `GET /api/v1/me` → `{ id, email, name }`. Requires `Authorization: Bearer <jwt>`.

The JWT is an opaque bearer token (HS256, 24h expiry). Send it as
`Authorization: Bearer <token>` on every REST call except register/login/google.

### Trips
- `POST /api/v1/trips` → `201` TripResponse. Body (all optional):
  `{ title?, destination?, start_date?, end_date?, budget_inr? }`.
  Creating a trip also starts its conversation (thread_id == trip id).
- `GET /api/v1/trips?limit=&offset=` → `TripResponse[]` (newest first).
- `GET /api/v1/trips/{id}` → TripResponse (or `404` if not owned — no existence leak).
- `PATCH /api/v1/trips/{id}` → TripResponse. Body: `{ title?, status? }`.
- `DELETE /api/v1/trips/{id}` → `204` (soft delete).
- `GET /api/v1/trips/{id}/messages?limit=&offset=` → `MessageResponse[]`
  (`{ id, role, content, created_at }`, oldest first).
- `GET /api/v1/trips/{id}/pdf` → `application/pdf` attachment (or `409` if the
  trip has no itinerary yet).

**TripResponse:** `{ id, title, destination, start_date, end_date, budget_inr,
status, itinerary, created_at, updated_at }`. `status` ∈ `draft | ...`.
`itinerary` is `null` until the first plan turn completes, then the Itinerary shape below.

### WebSocket — the core interaction
```
WS ws://localhost:8000/ws/trips/{tripId}/chat?token=<JWT>
```
Auth is via the `?token=` query param (browsers can't set headers on the WS
handshake). Invalid token OR not-your-trip → the server closes with code **4401
before accepting** (no distinction, mirroring the REST 404 no-leak policy).
Handle 4401 by bouncing to login / showing "not found".

**Client → server:** `{ "type": "user_message", "content": "..." }`
(any other `type` gets an inline `error` event but keeps the socket open).

**Server → client** — the *actual* implemented event types (note: these differ
from PROJECT_PLAN §11's wishlist; there are no `agent_start`/`tool_call`/
`clarification_request` events yet):

| `type` | payload | meaning |
|---|---|---|
| `route_decision` | `{ route }` | `chit_chat` \| `clarify` \| `plan` \| `refine` |
| `assistant_message` | `{ content }` | inline text reply (chit-chat/clarify) |
| `agent_update` | `{ agent, detail }` | progress ping: `intake`/`planner`/`researcher` |
| `partial_itinerary` | `{ agent, data }` | itinerary so far (`synthesizer`/`refiner`); `data` is an Itinerary or null |
| `validation_report` | `{ is_valid, issues[] }` | `issues`: `{ code, severity, message, ... }` |
| `complete` | `{ itinerary }` | end of turn; final Itinerary (or null) |
| `error` | `{ message }` | turn failed; socket stays open |

Every turn ends with exactly one `complete` (or `error`). Use that to flip the
"agents working" UI back to idle and to invalidate the TanStack Query cache for
the trip + messages (both are persisted server-side per turn).

### Itinerary shape (SSOT — mirror in a Zod schema)
```ts
type Block = { time: string; activity: string; location: string; cost_inr: number; notes: string };
type Day   = { day: number; blocks: Block[] };
type Itinerary = { destination: string; days: Day[]; total_cost_inr: number };
```
`time` is `"HH:MM"` 24h. Budget breakdown is derived client-side by summing
`cost_inr` across blocks/days — no separate endpoint.

---

## 4. App structure

```
frontend/
├── app/
│   ├── layout.tsx                 # providers: TanStack Query, theme, auth guard
│   ├── page.tsx                   # landing / redirect to dashboard if authed
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── dashboard/page.tsx         # trip list + "new trip"
│   ├── new/page.tsx               # new-trip form (or a modal on dashboard)
│   └── trip/[id]/page.tsx         # THE view: chat (left) + itinerary (right)
├── components/
│   ├── chat/                      # MessageList, MessageBubble, Composer, AgentActivity
│   ├── itinerary/                 # ItineraryTimeline, DayCard, BlockRow
│   ├── budget/                    # BudgetSummary
│   ├── trips/                     # TripCard, NewTripForm
│   └── ui/                        # shadcn primitives
├── lib/
│   ├── api.ts                     # typed REST client (fetch wrapper + auth header)
│   ├── ws.ts                      # WebSocket client (connect, send, event stream)
│   ├── schemas.ts                 # Zod schemas: Itinerary, events, API DTOs
│   ├── auth.ts                    # token storage + helpers
│   └── query.ts                   # TanStack Query keys + hooks
├── hooks/
│   ├── useChatSocket.ts           # opens WS, feeds Zustand, handles reconnect/4401
│   └── useTrip.ts / useTrips.ts   # TanStack Query wrappers
├── store/
│   └── chat.ts                    # Zustand: live events + streaming status per turn
├── .env.local.example             # NEXT_PUBLIC_API_URL, NEXT_PUBLIC_GOOGLE_CLIENT_ID
├── next.config.mjs
├── tailwind.config.ts
└── package.json
```

**The trip view (`trip/[id]`) is a client component.** It's a split layout: chat
on the left (message history + live agent activity + composer), the itinerary
timeline + budget on the right. On mobile, stack them (tabs or a toggle).

---

## 5. State management (the one design decision that matters)

- **TanStack Query = server truth.** User (`/me`), trips list, single trip
  (incl. persisted itinerary), message history. Query keys in `lib/query.ts`.
  After each turn's `complete`, invalidate `['trip', id]` and `['messages', id]`.
- **Zustand = live, ephemeral turn state only.** The in-flight event stream for
  the currently open trip: current route, the rolling list of `agent_update`
  pings, the latest `partial_itinerary`, `validation_report`, and a
  `status: 'idle' | 'streaming'`. Cleared/replaced per turn. Nothing here needs
  to survive a refresh — on reload we re-read the persisted state from the API.

This split avoids the classic trap of shadowing DB data in a client store.
During a turn the UI reads the *optimistic* live itinerary from Zustand; once
`complete` fires and the query refetches, it reads the *canonical* one from the
cache. Keep the swap seamless (same component, prefer live while streaming).

---

## 6. Key flows

**Auth.** Login/register → store JWT (see §7) → set default Authorization header
in `lib/api.ts` → redirect to `/dashboard`. Google: load Google Identity
Services, get an ID token, POST to `/auth/google`, same token handling. A route
guard in `app/layout.tsx` (or middleware) bounces unauthed users to `/login`.

**New trip.** Form (React Hook Form + Zod) → `POST /trips` → redirect to
`/trip/{id}`. Fields optional because the chat fills the rest — a bare
"destination" is enough to start.

**Chat + streaming (the heart).**
1. On mount, `useChatSocket` opens `WS …/chat?token=<jwt>`; on 4401 close, bounce
   to login/404.
2. User types → send `{ type: "user_message", content }` → set Zustand
   `status='streaming'`, optimistically append the user message.
3. Route events into Zustand: `route_decision` sets the badge; `agent_update`
   appends an activity line ("Planner: drafted 3 days"); `partial_itinerary`
   updates the live itinerary; `validation_report` shows issues (warnings amber,
   errors red — the backend self-corrects errors via the refine loop, so expect
   a follow-up `partial_itinerary`); `assistant_message` appends a chat bubble.
4. On `complete`: set `status='idle'`, invalidate trip + messages queries.
5. On `error`: surface it, keep the socket open.

**Itinerary render.** `ItineraryTimeline` maps days → `DayCard` → `BlockRow`
(time, activity, location, cost, notes). Source is the live Zustand itinerary
while streaming, else the cached `trip.itinerary`.

**PDF.** A "Download PDF" button hits `GET /trips/{id}/pdf` with the auth header
(fetch as blob → object URL → click). Disable it when `trip.itinerary` is null
(the endpoint 409s).

---

## 7. Auth token handling

- Store the JWT so REST + WS can both read it. Simplest defensible MVP choice:
  keep it in memory (Zustand/React context) with a `localStorage` fallback for
  refresh persistence. Note the XSS trade-off in a comment; httpOnly cookies are
  the hardening path but require backend cookie support we haven't built — defer.
- `lib/api.ts` injects `Authorization: Bearer <jwt>`; on `401` clear the token
  and redirect to login.
- The WS gets the token via `?token=` (the only channel available). Don't log
  the URL with the token in it.

---

## 8. Environment

`frontend/.env.local` (git-ignored; commit `.env.local.example`):
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_GOOGLE_CLIENT_ID=      # must match backend GOOGLE_CLIENT_ID
```
Only `NEXT_PUBLIC_*` vars reach the browser — never put a secret here.

---

## 9. Build order (check off as we go; log in PROGRESS.md)

- [x] **0. Scaffold** — Next.js 14 (TS strict, App Router, Tailwind 3) via pnpm
      (corepack); shadcn set up in **classic Radix/Tailwind-v3 style** (the latest
      CLI defaults to base-ui + Tailwind v4 "base-nova" — reset to Radix + HSL vars
      for a more defensible, documented foundation; drive future components with
      `shadcn@2`). `.env.local.example`, `frontend-ci.yml` (lint + typecheck +
      build). Landing renders; build + lint + tsc all green.
- [x] **1. API + types layer** — `lib/schemas.ts` (Zod mirrors: Itinerary, WS
      events discriminated union, REST DTOs), `lib/auth.ts` (token storage),
      `lib/api.ts` (typed fetch client: `authApi`/`tripsApi`, bearer injection,
      `ApiError`, Zod-parsed responses, PDF blob, 401→clearToken), `lib/query.ts`
      (query keys + `useTrips`/`useTrip`/`useMessages`/`useCurrentUser` + create/
      update/delete mutations), `app/providers.tsx` (QueryClientProvider, no-retry
      on 401) wired into the root layout. tsc + lint + build green. No UI yet.
- [x] **2. Auth** — login + register pages (RHF + Zod, `lib/forms.ts`), Google
      Sign-In (`GoogleSignInButton` via GIS → `/auth/google`, renders only when
      `NEXT_PUBLIC_GOOGLE_CLIENT_ID` is set), `AuthGuard` (validates via `/me`,
      redirects to /login), token storage across refresh, logout (clear token +
      query cache). Landing CTAs + a minimal guarded `/dashboard` placeholder to
      close the loop. shadcn `input`/`label`/`card` added via `shadcn@2`.
      tsc + lint + build green. (Live browser click-through pending — best done
      once dashboard/chat exist.)
- [x] **3. Dashboard + new trip** — trips list (`useTrips`), `TripCard`,
      `NewTripDialog` (RHF + Zod, `budget_inr` via `setValueAs`) → `useCreateTrip`
      → navigate to `/trip/{id}`. Loading skeletons + empty state.
- [x] **4. Chat shell + history** — trip view split layout, message history from
      `/messages` seeded into the store, `MessageList` (auto-scroll) + `Composer`
      (Enter to send, disabled while streaming/disconnected).
- [x] **5. WebSocket streaming** — `lib/ws.ts` + `useChatSocket` (token via query
      param, reconnect w/ backoff, cache invalidation on complete) + Zustand
      `store/chat.ts`; full event handling; `AgentActivity` panel (route badge,
      agent lines, validation issues, errors). **Live-verified end-to-end**
      (self-correction loop visible; itinerary + messages persisted).
- [x] **6. Itinerary + budget** — `ItineraryTimeline` (live store itinerary,
      falling back to persisted), `BudgetSummary` (derived, over/within budget),
      validation display.
- [x] **7. PDF + polish** — `ItineraryPanel` PDF download (blob, disabled until
      persisted), loading/empty/error states throughout, mobile Chat/Itinerary
      tab toggle, connection indicator.

All 8 steps done. tsc + lint + production build green; streaming verified live.

---

## 10. Testing

- **Type safety is the first test** — TS strict + Zod parsing at the API/WS
  boundary catches most contract drift for free.
- **Component tests** (Vitest + Testing Library) for the event→UI reducer logic
  in the chat store and the itinerary render — these are the parts with real logic.
- **One E2E happy path** (Playwright, optional for MVP): login → new trip →
  send a message → see `complete` → itinerary renders. Point it at a running
  backend with mocked LLM, or stub the WS.
- Keep it proportional (KISS): don't unit-test shadcn wrappers.

---

## 11. Notes / deltas from PROJECT_PLAN

- **Event names differ.** PROJECT_PLAN §11 lists `agent_start`, `agent_thinking`,
  `tool_call`, `tool_result`, `clarification_request`. The backend currently
  emits the coarser set in §3 (`agent_update`, `partial_itinerary`, etc.). Build
  to §3. If we later enrich the backend stream (e.g. per-tool events), the
  activity panel is where they'll surface.
- **No `interrupt()`/clarification UI yet.** The Intake node doesn't pause for
  missing fields today; `clarify` just comes back as an `assistant_message`.
  Treat clarify like chit-chat for now.
- **Map is deferred.** `places` returns lat/lng, but the Itinerary blocks don't
  carry coordinates yet, so Mapbox is Phase 2 (needs a backend change to surface
  coords per block). Don't scaffold the map until that lands.
- **PDF is server-side already** (fpdf2), so the frontend just downloads it — no
  client-side PDF library.
</content>
