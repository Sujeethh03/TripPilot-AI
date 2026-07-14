"use client";

import { Download, Loader2 } from "lucide-react";
import { useState } from "react";

import { ItineraryTimeline } from "@/components/itinerary/itinerary-timeline";
import { RouteMap } from "@/components/itinerary/route-map";
import { Button } from "@/components/ui/button";
import { tripsApi } from "@/lib/api";
import type { Trip } from "@/lib/schemas";
import { useChatStore } from "@/store/chat";

/**
 * Right-hand itinerary panel. Prefers the live (streaming) itinerary from the
 * store, falling back to the trip's persisted itinerary. The PDF button is
 * enabled only once an itinerary is persisted server-side (the endpoint 409s
 * otherwise).
 */
export function ItineraryPanel({ trip }: { trip: Trip }) {
  const liveItinerary = useChatStore((s) => s.liveItinerary);
  const itinerary = liveItinerary ?? trip.itinerary;
  const [downloading, setDownloading] = useState(false);

  async function downloadPdf() {
    setDownloading(true);
    try {
      const blob = await tripsApi.pdf(trip.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `trip-${trip.id}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b p-4">
        <h2 className="font-semibold">Itinerary</h2>
        <Button
          variant="outline"
          size="sm"
          onClick={downloadPdf}
          disabled={!trip.itinerary || downloading}
          title={trip.itinerary ? "Download PDF" : "No itinerary to export yet"}
        >
          {downloading ? (
            <Loader2 className="mr-1 h-4 w-4 animate-spin" />
          ) : (
            <Download className="mr-1 h-4 w-4" />
          )}
          PDF
        </Button>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        {itinerary ? (
          <div className="space-y-4">
            <RouteMap itinerary={itinerary} />
            <ItineraryTimeline itinerary={itinerary} budgetInr={trip.budget_inr} />
          </div>
        ) : (
          <p className="mt-8 text-center text-sm text-muted-foreground">
            Your itinerary will appear here as you plan.
          </p>
        )}
      </div>
    </div>
  );
}
