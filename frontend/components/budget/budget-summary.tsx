import { formatINR } from "@/lib/format";
import type { Itinerary } from "@/lib/schemas";

/** Budget breakdown derived from the itinerary (no separate endpoint). */
export function BudgetSummary({
  itinerary,
  budgetInr,
}: {
  itinerary: Itinerary;
  budgetInr?: number | null;
}) {
  const total = itinerary.total_cost_inr;
  const overBudget = budgetInr != null && total > budgetInr;

  return (
    <div className="rounded-lg border p-3 text-sm">
      <div className="flex items-center justify-between">
        <span className="text-muted-foreground">Estimated total</span>
        <span className="font-semibold">{formatINR(total)}</span>
      </div>
      {budgetInr != null && (
        <div className="mt-1 flex items-center justify-between">
          <span className="text-muted-foreground">Budget</span>
          <span className={overBudget ? "text-destructive" : "text-emerald-600 dark:text-emerald-400"}>
            {formatINR(budgetInr)}
            {overBudget ? " (over)" : " (within)"}
          </span>
        </div>
      )}
    </div>
  );
}
