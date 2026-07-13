"use client";

import { ArrowLeft, Loader2 } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { AuthGuard } from "@/components/auth/auth-guard";
import { Composer } from "@/components/chat/composer";
import { MessageList } from "@/components/chat/message-list";
import { ItineraryPanel } from "@/components/itinerary/itinerary-panel";
import { Button } from "@/components/ui/button";
import { useChatSocket } from "@/hooks/use-chat-socket";
import { useMessages, useTrip } from "@/lib/query";
import { cn } from "@/lib/utils";
import { useChatStore } from "@/store/chat";

function TripView({ tripId }: { tripId: string }) {
  const { data: trip, isLoading, isError } = useTrip(tripId);
  const { data: messages } = useMessages(tripId);
  const { connected, send } = useChatSocket(tripId);
  const [mobileTab, setMobileTab] = useState<"chat" | "itinerary">("chat");

  const seed = useChatStore((s) => s.seed);
  const reset = useChatStore((s) => s.reset);

  // Seed the store from server history once it (and the trip) load.
  useEffect(() => {
    if (messages && trip) seed(messages, trip.itinerary);
  }, [messages, trip, seed]);

  // Clear live state when leaving the trip.
  useEffect(() => reset, [tripId, reset]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }
  if (isError || !trip) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3">
        <p className="text-muted-foreground">Trip not found.</p>
        <Link href="/dashboard" className="text-sm underline underline-offset-4">
          Back to dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col">
      <header className="flex items-center gap-3 border-b p-3">
        <Link href="/dashboard" className="text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div className="min-w-0">
          <h1 className="truncate font-semibold">
            {trip.title || trip.destination || "Trip"}
          </h1>
        </div>
        <span
          className={`ml-auto text-xs ${connected ? "text-emerald-600 dark:text-emerald-400" : "text-muted-foreground"}`}
        >
          {connected ? "● connected" : "○ connecting…"}
        </span>
      </header>

      {/* Mobile tab switcher (side-by-side on md+). */}
      <div className="flex gap-1 border-b p-2 md:hidden">
        <Button
          variant={mobileTab === "chat" ? "secondary" : "ghost"}
          size="sm"
          className="flex-1"
          onClick={() => setMobileTab("chat")}
        >
          Chat
        </Button>
        <Button
          variant={mobileTab === "itinerary" ? "secondary" : "ghost"}
          size="sm"
          className="flex-1"
          onClick={() => setMobileTab("itinerary")}
        >
          Itinerary
        </Button>
      </div>

      <div className="grid flex-1 grid-cols-1 overflow-hidden md:grid-cols-2">
        <section
          className={cn(
            "flex-col overflow-hidden border-r md:flex",
            mobileTab === "chat" ? "flex" : "hidden"
          )}
        >
          <MessageList />
          <Composer connected={connected} onSend={send} />
        </section>
        <section
          className={cn(
            "overflow-hidden md:block",
            mobileTab === "itinerary" ? "block" : "hidden"
          )}
        >
          <ItineraryPanel trip={trip} />
        </section>
      </div>
    </div>
  );
}

export default function TripPage() {
  const params = useParams<{ id: string }>();
  return (
    <AuthGuard>
      <TripView tripId={params.id} />
    </AuthGuard>
  );
}
