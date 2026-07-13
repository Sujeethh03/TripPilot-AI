"use client";

import { SendHorizontal } from "lucide-react";
import { useState, type KeyboardEvent } from "react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useChatStore } from "@/store/chat";

export function Composer({
  connected,
  onSend,
}: {
  connected: boolean;
  onSend: (content: string) => boolean;
}) {
  const [value, setValue] = useState("");
  const status = useChatStore((s) => s.status);
  const sendUserMessage = useChatStore((s) => s.sendUserMessage);

  const disabled = !connected || status === "streaming";

  function submit() {
    const content = value.trim();
    if (!content || disabled) return;
    if (onSend(content)) {
      sendUserMessage(content);
      setValue("");
    }
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  return (
    <div className="border-t p-3">
      <div className="flex items-end gap-2">
        <Textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder={connected ? "Message TripPilot…" : "Connecting…"}
          rows={1}
          className="max-h-40 min-h-[40px] resize-none"
        />
        <Button size="icon" onClick={submit} disabled={disabled || value.trim() === ""}>
          <SendHorizontal className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
