/**
 * Typed REST client for the TripPilot backend (see FRONTEND_PLAN §3).
 *
 * One thin wrapper over fetch: injects the bearer token, throws a typed
 * `ApiError` on non-2xx, and parses success bodies through the Zod schemas so
 * the rest of the app works with validated types. No caching here — that's
 * TanStack Query's job (lib/query.ts).
 */
import { z } from "zod";

import { clearToken, getToken } from "@/lib/auth";
import {
  messageSchema,
  tokenSchema,
  tripSchema,
  userSchema,
  type Message,
  type Token,
  type Trip,
  type User,
} from "@/lib/schemas";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const PREFIX = "/api/v1";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type RequestOptions = {
  method?: string;
  body?: unknown;
  auth?: boolean; // attach the bearer token (default true)
  schema?: z.ZodType<unknown>; // parse the JSON response if provided
};

async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, auth = true, schema } = opts;

  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${PREFIX}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (res.status === 401) {
    clearToken(); // stale/expired token — force re-auth
    throw new ApiError(401, "Not authenticated");
  }
  if (!res.ok) {
    throw new ApiError(res.status, await extractError(res));
  }

  if (res.status === 204) return undefined as T;
  const json = await res.json();
  return (schema ? schema.parse(json) : json) as T;
}

async function extractError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data?.detail === "string") return data.detail;
    return JSON.stringify(data);
  } catch {
    return res.statusText || `HTTP ${res.status}`;
  }
}

// --- Auth --------------------------------------------------------------------

export const authApi = {
  register: (body: { email: string; password: string; name?: string }): Promise<User> =>
    request("/auth/register", { method: "POST", body, auth: false, schema: userSchema }),

  login: (body: { email: string; password: string }): Promise<Token> =>
    request("/auth/login", { method: "POST", body, auth: false, schema: tokenSchema }),

  google: (idToken: string): Promise<Token> =>
    request("/auth/google", {
      method: "POST",
      body: { id_token: idToken },
      auth: false,
      schema: tokenSchema,
    }),

  me: (): Promise<User> => request("/me", { schema: userSchema }),
};

// --- Trips -------------------------------------------------------------------

export type TripCreate = {
  title?: string;
  destination?: string;
  origin?: string;
  transport_mode?: string;
  start_date?: string;
  end_date?: string;
  budget_inr?: number;
};

export type TripUpdate = { title?: string; status?: string };

export const tripsApi = {
  list: (): Promise<Trip[]> => request("/trips", { schema: z.array(tripSchema) }),

  get: (id: string): Promise<Trip> => request(`/trips/${id}`, { schema: tripSchema }),

  create: (body: TripCreate): Promise<Trip> =>
    request("/trips", { method: "POST", body, schema: tripSchema }),

  update: (id: string, body: TripUpdate): Promise<Trip> =>
    request(`/trips/${id}`, { method: "PATCH", body, schema: tripSchema }),

  remove: (id: string): Promise<void> => request(`/trips/${id}`, { method: "DELETE" }),

  messages: (id: string): Promise<Message[]> =>
    request(`/trips/${id}/messages`, { schema: z.array(messageSchema) }),

  /** Download the itinerary PDF as a Blob (auth header attached manually). */
  pdf: async (id: string): Promise<Blob> => {
    const token = getToken();
    const res = await fetch(`${API_URL}${PREFIX}/trips/${id}/pdf`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) throw new ApiError(res.status, await extractError(res));
    return res.blob();
  },
};
