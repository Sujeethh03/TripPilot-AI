"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useCallbackRef } from "@/hooks/use-callback-ref";
import { useEffect, useRef, useState } from "react";

import { getToken } from "@/lib/auth";
import { queryKeys } from "@/lib/query";
import { wsEventSchema } from "@/lib/schemas";
import { chatSocketUrl } from "@/lib/ws";
import { useChatStore } from "@/store/chat";

const MAX_RETRIES = 3;

/**
 * Opens the chat WebSocket for a trip and feeds parsed events into the chat
 * store. Invalidates the trip cache after each completed turn so the persisted
 * itinerary refreshes. Reconnects a few times on abnormal closes; a 4401 means
 * auth failed (shouldn't happen past AuthGuard) and is surfaced as an error.
 */
export function useChatSocket(tripId: string) {
  const queryClient = useQueryClient();
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const retriesRef = useRef(0);
  const closedRef = useRef(false);

  const applyEvent = useChatStore((s) => s.applyEvent);

  // Keep the latest applyEvent without re-opening the socket each render.
  const onEvent = useCallbackRef((raw: string) => {
    let parsed: unknown;
    try {
      parsed = JSON.parse(raw);
    } catch {
      return;
    }
    const result = wsEventSchema.safeParse(parsed);
    if (!result.success) return;
    applyEvent(result.data);
    if (result.data.type === "complete" || result.data.type === "error") {
      // Refresh persisted truth (itinerary + message history) so a later remount
      // reseeds correctly. Safe mid-session: the trip view seeds only once.
      queryClient.invalidateQueries({ queryKey: queryKeys.trip(tripId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.messages(tripId) });
    }
  });

  useEffect(() => {
    closedRef.current = false;
    retriesRef.current = 0;

    function connect() {
      const token = getToken();
      if (!token) return;
      const ws = new WebSocket(chatSocketUrl(tripId, token));
      wsRef.current = ws;

      ws.onopen = () => {
        retriesRef.current = 0;
        setConnected(true);
      };
      ws.onmessage = (e) => onEvent(String(e.data));
      ws.onclose = (e) => {
        setConnected(false);
        if (closedRef.current || e.code === 4401) return;
        if (retriesRef.current < MAX_RETRIES) {
          retriesRef.current += 1;
          setTimeout(connect, 1000 * retriesRef.current);
        }
      };
    }

    connect();
    return () => {
      closedRef.current = true;
      wsRef.current?.close();
      wsRef.current = null;
    };
  }, [tripId, onEvent]);

  function send(content: string): boolean {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return false;
    ws.send(JSON.stringify({ type: "user_message", content }));
    return true;
  }

  return { connected, send };
}
