"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { AuthGuard } from "@/components/auth/auth-guard";
import { NewTripDialog } from "@/components/trips/new-trip-dialog";
import { TripCard } from "@/components/trips/trip-card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { clearToken } from "@/lib/auth";
import { useCurrentUser, useTrips } from "@/lib/query";

function DashboardContent() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { data: user } = useCurrentUser();
  const { data: trips, isLoading } = useTrips();

  function logout() {
    clearToken();
    queryClient.clear();
    router.replace("/login");
  }

  return (
    <main className="mx-auto max-w-4xl p-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Your trips</h1>
        <div className="flex items-center gap-3">
          <span className="hidden text-sm text-muted-foreground sm:inline">{user?.email}</span>
          <NewTripDialog />
          <Button variant="outline" size="sm" onClick={logout}>
            Log out
          </Button>
        </div>
      </div>

      <div className="mt-8">
        {isLoading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-32 w-full" />
            ))}
          </div>
        ) : trips && trips.length > 0 ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {trips.map((trip) => (
              <TripCard key={trip.id} trip={trip} />
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4 rounded-lg border border-dashed py-16 text-center">
            <p className="text-muted-foreground">
              No trips yet. Start planning your first one.
            </p>
            <NewTripDialog />
          </div>
        )}
      </div>
    </main>
  );
}

export default function DashboardPage() {
  return (
    <AuthGuard>
      <DashboardContent />
    </AuthGuard>
  );
}
