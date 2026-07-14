import { BudgetSummary } from "@/components/budget/budget-summary";
import { formatDuration, formatINR, weatherEmoji } from "@/lib/format";
import type { Block, Day, Hotel, Itinerary, TravelLeg, Weather } from "@/lib/schemas";

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
      {itinerary.travel && <TravelBanner travel={itinerary.travel} />}
      <BudgetSummary itinerary={itinerary} budgetInr={budgetInr} />
      {itinerary.hotels.length > 0 && <HotelList hotels={itinerary.hotels} />}
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
      <div className="mb-2 flex items-center justify-between gap-2">
        <h3 className="text-sm font-semibold">Day {day.day}</h3>
        {day.weather && <WeatherBadge weather={day.weather} />}
      </div>
      <ol className="space-y-2 border-l pl-4">
        {day.blocks.map((block, i) => (
          <BlockRow key={i} block={block} />
        ))}
      </ol>
    </div>
  );
}

function TravelBanner({ travel }: { travel: TravelLeg }) {
  const icon = travel.mode === "transit" ? "🚌" : "🚗";
  const parts: string[] = [];
  if (travel.distance_km != null) parts.push(`${Math.round(travel.distance_km)} km`);
  if (travel.duration_min != null) parts.push(formatDuration(travel.duration_min));
  return (
    <div className="flex items-center gap-2 rounded-lg border bg-accent/40 px-3 py-2 text-sm">
      <span aria-hidden>{icon}</span>
      <span className="font-medium">
        {travel.origin} → {travel.destination}
      </span>
      {parts.length > 0 && (
        <span className="text-muted-foreground">· {parts.join(" · ")}</span>
      )}
    </div>
  );
}

// A full formatted address is verbose; show the first couple of segments.
function shortArea(area: string): string {
  return area.split(",").slice(0, 2).join(",").trim();
}

function HotelList({ hotels }: { hotels: Hotel[] }) {
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold">Where to stay</h3>
      <ul className="space-y-1.5">
        {hotels.map((hotel, i) => (
          <li key={i} className="flex items-baseline justify-between gap-3 text-sm">
            <div className="min-w-0">
              <span className="font-medium">{hotel.name}</span>
              {hotel.area && (
                <span className="text-muted-foreground"> · {shortArea(hotel.area)}</span>
              )}
            </div>
            {hotel.rating != null && (
              <span className="shrink-0 text-xs text-muted-foreground">★ {hotel.rating}</span>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

function WeatherBadge({ weather }: { weather: Weather }) {
  const temps =
    weather.max_temp_c != null && weather.min_temp_c != null
      ? `${Math.round(weather.max_temp_c)}° / ${Math.round(weather.min_temp_c)}°`
      : null;
  return (
    <span
      className="flex items-center gap-1 rounded-full bg-accent px-2 py-0.5 text-xs text-muted-foreground"
      title={weather.condition}
    >
      <span aria-hidden>{weatherEmoji(weather.condition)}</span>
      {temps && <span className="tabular-nums">{temps}</span>}
    </span>
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
