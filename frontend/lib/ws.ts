/** WebSocket URL builder for the chat stream (see FRONTEND_PLAN §3).
 * The JWT rides as a query param — browsers can't set WS headers. */
export function chatSocketUrl(tripId: string, token: string): string {
  const base = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";
  return `${base}/ws/trips/${tripId}/chat?token=${encodeURIComponent(token)}`;
}
