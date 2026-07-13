"use client";

import { MoreVertical, Trash2 } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { formatDate, formatINR } from "@/lib/format";
import { useDeleteTrip } from "@/lib/query";
import type { Trip } from "@/lib/schemas";

export function TripCard({ trip }: { trip: Trip }) {
  const [confirmOpen, setConfirmOpen] = useState(false);
  const deleteTrip = useDeleteTrip();

  const name = trip.title || trip.destination || "Untitled trip";
  const dates =
    trip.start_date && trip.end_date
      ? `${formatDate(trip.start_date)} – ${formatDate(trip.end_date)}`
      : null;

  return (
    <div className="relative">
      <Link href={`/trip/${trip.id}`} className="block">
        <Card className="h-full transition-colors hover:border-foreground/20 hover:bg-accent/40">
          <CardHeader className="pb-2 pr-10">
            <CardTitle className="text-base">{name}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-sm text-muted-foreground">
            {trip.destination && trip.title && <p>{trip.destination}</p>}
            {dates && <p>{dates}</p>}
            {trip.budget_inr != null && <p>Budget {formatINR(trip.budget_inr)}</p>}
            <Badge variant="secondary" className="mt-1 capitalize">
              {trip.status}
            </Badge>
          </CardContent>
        </Card>
      </Link>

      {/* Actions menu — sibling of the Link so it never triggers navigation. */}
      <div className="absolute right-2 top-2">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8" aria-label="Trip actions">
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem
              className="text-destructive focus:text-destructive"
              onSelect={(e) => {
                e.preventDefault();
                setConfirmOpen(true);
              }}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete “{name}”?</AlertDialogTitle>
            <AlertDialogDescription>
              This permanently deletes the trip along with its entire conversation and
              itinerary. This can’t be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleteTrip.isPending}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              disabled={deleteTrip.isPending}
              onClick={(e) => {
                e.preventDefault();
                deleteTrip.mutate(trip.id, { onSuccess: () => setConfirmOpen(false) });
              }}
            >
              {deleteTrip.isPending ? "Deleting…" : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
