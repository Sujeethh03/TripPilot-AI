/**
 * Live, ephemeral chat state for the open trip (see FRONTEND_PLAN §5).
 *
 * This holds only what's in-flight for the current session: the message thread
 * (seeded from server history, then appended live), the current turn's route /
 * agent activity / partial itinerary / validation, and a streaming status.
 * Persisted truth (trip.itinerary, message rows) lives in TanStack Query; on a
 * page reload we re-read it from the API and reseed here.
 */
import { create } from "zustand";

import type { Itinerary, Message, Route, ValidationIssue, WsEvent } from "@/lib/schemas";

export type ChatMessage = { role: "user" | "assistant"; content: string };

type Validation = { is_valid: boolean; issues: ValidationIssue[] };

interface ChatState {
  status: "idle" | "streaming";
  messages: ChatMessage[];
  route: Route | null;
  activity: string[];
  liveItinerary: Itinerary | null;
  validation: Validation | null;
  error: string | null;

  seed: (messages: Message[], itinerary: Itinerary | null) => void;
  sendUserMessage: (content: string) => void;
  applyEvent: (event: WsEvent) => void;
  reset: () => void;
}

const initial = {
  status: "idle" as const,
  messages: [] as ChatMessage[],
  route: null,
  activity: [] as string[],
  liveItinerary: null as Itinerary | null,
  validation: null as Validation | null,
  error: null as string | null,
};

export const useChatStore = create<ChatState>((set) => ({
  ...initial,

  seed: (messages, itinerary) =>
    set({
      messages: messages
        .filter((m) => m.role === "user" || m.role === "assistant")
        .map((m) => ({ role: m.role as "user" | "assistant", content: m.content })),
      liveItinerary: itinerary,
    }),

  sendUserMessage: (content) =>
    set((s) => ({
      status: "streaming",
      messages: [...s.messages, { role: "user", content }],
      // reset per-turn scratch state
      route: null,
      activity: [],
      validation: null,
      error: null,
    })),

  applyEvent: (event) =>
    set((s) => {
      switch (event.type) {
        case "route_decision":
          return { route: event.route };
        case "assistant_message":
          return {
            messages: [...s.messages, { role: "assistant", content: event.content }],
          };
        case "agent_update":
          return { activity: [...s.activity, `${event.agent}: ${event.detail}`] };
        case "partial_itinerary":
          return event.data ? { liveItinerary: event.data } : {};
        case "validation_report":
          return { validation: { is_valid: event.is_valid, issues: event.issues } };
        case "complete":
          return {
            status: "idle",
            liveItinerary: event.itinerary ?? s.liveItinerary,
          };
        case "error":
          return { status: "idle", error: event.message };
        default:
          return {};
      }
    }),

  reset: () => set(initial),
}));
