/**
 * JWT storage for the client (see FRONTEND_PLAN §7).
 *
 * MVP choice: keep the token in memory with a localStorage fallback so it
 * survives refreshes. This is readable by JS (XSS trade-off noted); the
 * hardening path is httpOnly cookies, which need backend cookie support we
 * haven't built — deferred.
 */

const STORAGE_KEY = "trippilot_token";

let inMemoryToken: string | null = null;

export function getToken(): string | null {
  if (inMemoryToken) return inMemoryToken;
  if (typeof window === "undefined") return null;
  inMemoryToken = window.localStorage.getItem(STORAGE_KEY);
  return inMemoryToken;
}

export function setToken(token: string): void {
  inMemoryToken = token;
  if (typeof window !== "undefined") {
    window.localStorage.setItem(STORAGE_KEY, token);
  }
}

export function clearToken(): void {
  inMemoryToken = null;
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(STORAGE_KEY);
  }
}

export function isAuthenticated(): boolean {
  return getToken() !== null;
}
