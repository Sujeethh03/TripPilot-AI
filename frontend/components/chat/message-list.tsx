"use client";

import { useEffect, useRef } from "react";

import { AgentActivity } from "@/components/chat/agent-activity";
import { MessageBubble } from "@/components/chat/message-bubble";
import { useChatStore } from "@/store/chat";

export function MessageList() {
  const messages = useChatStore((s) => s.messages);
  const status = useChatStore((s) => s.status);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to the newest message / activity.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, status]);

  return (
    <div className="flex-1 space-y-3 overflow-y-auto p-4">
      {messages.length === 0 && status === "idle" && (
        <p className="mt-8 text-center text-sm text-muted-foreground">
          Describe your trip to get started — e.g. “5 days in Kerala, ₹20k, waterfalls and street
          food.”
        </p>
      )}
      {messages.map((m, i) => (
        <MessageBubble key={i} message={m} />
      ))}
      <AgentActivity />
      <div ref={bottomRef} />
    </div>
  );
}
