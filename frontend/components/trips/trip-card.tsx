import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDate, formatINR } from "@/lib/format";
import type { Trip } from "@/lib/schemas";

export function TripCard({ trip }: { trip: Trip }) {
  const dates =
    trip.start_date && trip.end_date
      ? `${formatDate(trip.start_date)} – ${formatDate(trip.end_date)}`
      : null;

  return (
    <Link href={`/trip/${trip.id}`} className="block">
      <Card className="h-full transition-colors hover:border-foreground/20 hover:bg-accent/40">
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between gap-2">
            <CardTitle className="text-base">
              {trip.title || trip.destination || "Untitled trip"}
            </CardTitle>
            <Badge variant="secondary" className="shrink-0 capitalize">
              {trip.status}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-1 text-sm text-muted-foreground">
          {trip.destination && <p>{trip.destination}</p>}
          {dates && <p>{dates}</p>}
          {trip.budget_inr != null && <p>Budget {formatINR(trip.budget_inr)}</p>}
        </CardContent>
      </Card>
    </Link>
  );
}
