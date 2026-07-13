/**
 * Zod mirrors of the backend contract (see FRONTEND_PLAN §3).
 *
 * These are the single source of truth for types on the client. Parse at the
 * network/WS boundary so contract drift surfaces as a clear error instead of an
 * `undefined` deep in the UI. Keep these in sync with the backend Pydantic
 * schemas (app/schemas/*) — they are the same shapes.
 */
import { z } from "zod";

// --- Itinerary (SSOT: backend app/schemas/itinerary.py) ----------------------

export const blockSchema = z.object({
  time: z.string(), // "HH:MM" 24h
  activity: z.string(),
  location: z.string(),
  cost_inr: z.number(),
  notes: z.string(),
});

export const daySchema = z.object({
  day: z.number(),
  blocks: z.array(blockSchema),
});

export const itinerarySchema = z.object({
  destination: z.string(),
  days: z.array(daySchema),
  total_cost_inr: z.number(),
});

export type Block = z.infer<typeof blockSchema>;
export type Day = z.infer<typeof daySchema>;
export type Itinerary = z.infer<typeof itinerarySchema>;

// --- Validation (backend app/schemas/planning.py) ----------------------------

export const validationIssueSchema = z.object({
  code: z.string(),
  message: z.string(),
  severity: z.enum(["warning", "error"]),
});

export type ValidationIssue = z.infer<typeof validationIssueSchema>;

// --- REST DTOs (backend app/schemas/auth.py, trip_api.py) --------------------

export const userSchema = z.object({
  id: z.string(),
  email: z.string(),
  name: z.string().nullable().optional(),
});

export const tokenSchema = z.object({
  access_token: z.string(),
  token_type: z.string(),
});

export const tripSchema = z.object({
  id: z.string(),
  title: z.string().nullable(),
  destination: z.string().nullable(),
  start_date: z.string().nullable(),
  end_date: z.string().nullable(),
  budget_inr: z.number().nullable(),
  status: z.string(),
  itinerary: itinerarySchema.nullable(),
  created_at: z.string(),
  updated_at: z.string(),
});

export const messageSchema = z.object({
  id: z.string(),
  role: z.string(), // user | assistant | system
  content: z.string(),
  created_at: z.string(),
});

export type User = z.infer<typeof userSchema>;
export type Token = z.infer<typeof tokenSchema>;
export type Trip = z.infer<typeof tripSchema>;
export type Message = z.infer<typeof messageSchema>;

// --- WebSocket events (backend app/agents/streaming.py) ----------------------
//
// One turn streams zero+ of these and ends with exactly one `complete` (or
// `error`). Discriminated on `type` so the UI can switch exhaustively.

export const ROUTES = ["chit_chat", "clarify", "plan", "refine"] as const;

export const wsEventSchema = z.discriminatedUnion("type", [
  z.object({ type: z.literal("route_decision"), route: z.enum(ROUTES) }),
  z.object({ type: z.literal("assistant_message"), content: z.string() }),
  z.object({ type: z.literal("agent_update"), agent: z.string(), detail: z.string() }),
  z.object({
    type: z.literal("partial_itinerary"),
    agent: z.string(),
    data: itinerarySchema.nullable(),
  }),
  z.object({
    type: z.literal("validation_report"),
    is_valid: z.boolean(),
    issues: z.array(validationIssueSchema),
  }),
  z.object({ type: z.literal("complete"), itinerary: itinerarySchema.nullable() }),
  z.object({ type: z.literal("error"), message: z.string() }),
]);

export type WsEvent = z.infer<typeof wsEventSchema>;
export type Route = (typeof ROUTES)[number];
