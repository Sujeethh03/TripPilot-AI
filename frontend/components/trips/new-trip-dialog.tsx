"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api";
import { newTripFormSchema, type NewTripForm } from "@/lib/forms";
import { useCreateTrip } from "@/lib/query";

export function NewTripDialog() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const createTrip = useCreateTrip();
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<NewTripForm>({ resolver: zodResolver(newTripFormSchema) });

  async function onSubmit(values: NewTripForm) {
    setFormError(null);
    try {
      const trip = await createTrip.mutateAsync({
        destination: values.destination,
        title: values.title || undefined,
        origin: values.origin || undefined,
        transport_mode: values.origin ? values.transport_mode || "driving" : undefined,
        start_date: values.start_date || undefined,
        end_date: values.end_date || undefined,
        budget_inr: values.budget_inr,
      });
      reset();
      setOpen(false);
      // ?start=1 tells the trip view to auto-kick planning from the form data.
      router.push(`/trip/${trip.id}?start=1`);
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Could not create trip");
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>New trip</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Plan a new trip</DialogTitle>
          <DialogDescription>
            Just a destination is enough — the chat fills in the rest.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="destination">Destination</Label>
            <Input id="destination" placeholder="Kerala" {...register("destination")} />
            {errors.destination && (
              <p className="text-sm text-destructive">{errors.destination.message}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="title">Title (optional)</Label>
            <Input id="title" placeholder="Monsoon getaway" {...register("title")} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label htmlFor="origin">Starting from (optional)</Label>
              <Input id="origin" placeholder="Hyderabad" {...register("origin")} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="transport_mode">Transport</Label>
              <select
                id="transport_mode"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                {...register("transport_mode")}
              >
                <option value="driving">Drive</option>
                <option value="transit">Bus / Train</option>
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label htmlFor="start_date">Start date</Label>
              <Input id="start_date" type="date" {...register("start_date")} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="end_date">End date</Label>
              <Input id="end_date" type="date" {...register("end_date")} />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="budget_inr">Budget (₹, optional)</Label>
            <Input
              id="budget_inr"
              type="number"
              placeholder="20000"
              {...register("budget_inr", {
                setValueAs: (v) => (v === "" || v == null ? undefined : Number(v)),
              })}
            />
            {errors.budget_inr && (
              <p className="text-sm text-destructive">{errors.budget_inr.message}</p>
            )}
          </div>
          {formError && <p className="text-sm text-destructive">{formError}</p>}
          <DialogFooter>
            <Button type="submit" disabled={createTrip.isPending}>
              {createTrip.isPending ? "Creating…" : "Create & start planning"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
