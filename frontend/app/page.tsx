import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-8 text-center">
      <div className="space-y-3">
        <h1 className="text-4xl font-bold tracking-tight">TripPilot AI</h1>
        <p className="max-w-md text-muted-foreground">
          Plan Indian trips by chatting. A team of agents researches real options
          and builds an hour-by-hour itinerary, live.
        </p>
      </div>
      <div className="flex gap-3">
        <Button asChild>
          <Link href="/register">Get started</Link>
        </Button>
        <Button asChild variant="outline">
          <Link href="/login">Log in</Link>
        </Button>
      </div>
    </main>
  );
}
