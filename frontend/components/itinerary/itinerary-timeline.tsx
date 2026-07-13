import { BudgetSummary } from "@/components/budget/budget-summary";
import { formatINR } from "@/lib/format";
import type { Block, Day, Itinerary } from "@/lib/schemas";

export function ItineraryTimeline({
  itinerary,
  budgetInr,
}: {
  itinerary: Itinerary;
  budgetInr?: number | null;
}) {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">{itinerary.destination}</h2>
        <p className="text-sm text-muted-foreground">
          {itinerary.days.length} day{itinerary.days.length === 1 ? "" : "s"}
        </p>
      </div>
      <BudgetSummary itinerary={itinerary} budgetInr={budgetInr} />
      <div className="space-y-5">
        {itinerary.days.map((day) => (
          <DayCard key={day.day} day={day} />
        ))}
      </div>
    </div>
  );
}

function DayCard({ day }: { day: Day }) {
  return (
    <div>
      <h3 className="mb-2 text-sm font-semibold">Day {day.day}</h3>
      <ol className="space-y-2 border-l pl-4">
        {day.blocks.map((block, i) => (
          <BlockRow key={i} block={block} />
        ))}
      </ol>
    </div>
  );
}

function BlockRow({ block }: { block: Block }) {
  return (
    <li className="relative">
      <span className="absolute -left-[21px] top-1 h-2 w-2 rounded-full bg-border" />
      <div className="flex items-baseline justify-between gap-3">
        <div>
          <span className="font-mono text-xs text-muted-foreground">{block.time}</span>{" "}
          <span className="font-medium">{block.activity}</span>
          {block.location && (
            <span className="text-muted-foreground"> · {block.location}</span>
          )}
          {block.notes && <p className="text-xs text-muted-foreground">{block.notes}</p>}
        </div>
        {block.cost_inr > 0 && (
          <span className="shrink-0 text-xs text-muted-foreground">
            {formatINR(block.cost_inr)}
          </span>
        )}
      </div>
    </li>
  );
}
