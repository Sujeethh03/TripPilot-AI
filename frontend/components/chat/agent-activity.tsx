import { Loader2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { ValidationIssue } from "@/lib/schemas";
import { cn } from "@/lib/utils";
import { useChatStore } from "@/store/chat";

const ROUTE_LABEL: Record<string, string> = {
  chit_chat: "Chatting",
  clarify: "Clarifying",
  plan: "Planning",
  refine: "Refining",
};

/** Live "agents working" panel shown during a streaming turn. */
export function AgentActivity() {
  const status = useChatStore((s) => s.status);
  const route = useChatStore((s) => s.route);
  const activity = useChatStore((s) => s.activity);
  const validation = useChatStore((s) => s.validation);
  const error = useChatStore((s) => s.error);

  if (error) {
    return (
      <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-sm text-destructive">
        Something went wrong: {error}
      </div>
    );
  }

  if (status !== "streaming" && activity.length === 0 && !validation) return null;

  return (
    <div className="space-y-2 rounded-lg border bg-muted/30 p-3 text-sm">
      <div className="flex items-center gap-2">
        {status === "streaming" && (
          <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
        )}
        {route && <Badge variant="secondary">{ROUTE_LABEL[route] ?? route}</Badge>}
        {status === "streaming" && !route && (
          <span className="text-muted-foreground">Thinking…</span>
        )}
      </div>
      {activity.length > 0 && (
        <ul className="space-y-1 text-muted-foreground">
          {activity.map((line, i) => (
            <li key={i}>• {line}</li>
          ))}
        </ul>
      )}
      {validation && <ValidationSummary issues={validation.issues} isValid={validation.is_valid} />}
    </div>
  );
}

function ValidationSummary({ issues, isValid }: { issues: ValidationIssue[]; isValid: boolean }) {
  if (issues.length === 0) {
    return <p className="text-emerald-600 dark:text-emerald-400">✓ Plan looks feasible</p>;
  }
  return (
    <ul className="space-y-1">
      {issues.map((issue, i) => (
        <li
          key={i}
          className={cn(
            issue.severity === "error"
              ? "text-destructive"
              : "text-amber-600 dark:text-amber-400"
          )}
        >
          {issue.severity === "error" ? "✗" : "⚠"} {issue.message}
        </li>
      ))}
      {!isValid && (
        <li className="text-xs text-muted-foreground">Refining to fix the above…</li>
      )}
    </ul>
  );
}
