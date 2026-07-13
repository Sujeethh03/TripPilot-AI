/**
 * TanStack Query keys + hooks — all server-state access goes through here
 * (see FRONTEND_PLAN §5). Query keys are centralized so invalidation after a
 * chat turn (lib/ws consumers) targets the right caches.
 */
import {
  useMutation,
  useQuery,
  useQueryClient,
  type UseQueryResult,
} from "@tanstack/react-query";

import { authApi, tripsApi, type TripCreate, type TripUpdate } from "@/lib/api";
import type { Message, Trip, User } from "@/lib/schemas";

export const queryKeys = {
  me: ["me"] as const,
  trips: ["trips"] as const,
  trip: (id: string) => ["trip", id] as const,
  messages: (id: string) => ["messages", id] as const,
};

// --- Queries -----------------------------------------------------------------

export function useCurrentUser(enabled = true): UseQueryResult<User> {
  return useQuery({ queryKey: queryKeys.me, queryFn: authApi.me, enabled });
}

export function useTrips(): UseQueryResult<Trip[]> {
  return useQuery({ queryKey: queryKeys.trips, queryFn: tripsApi.list });
}

export function useTrip(id: string): UseQueryResult<Trip> {
  return useQuery({ queryKey: queryKeys.trip(id), queryFn: () => tripsApi.get(id) });
}

export function useMessages(id: string): UseQueryResult<Message[]> {
  return useQuery({ queryKey: queryKeys.messages(id), queryFn: () => tripsApi.messages(id) });
}

// --- Mutations ---------------------------------------------------------------

export function useCreateTrip() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: TripCreate) => tripsApi.create(body),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.trips }),
  });
}

export function useUpdateTrip(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: TripUpdate) => tripsApi.update(id, body),
    onSuccess: (trip) => {
      qc.setQueryData(queryKeys.trip(id), trip);
      qc.invalidateQueries({ queryKey: queryKeys.trips });
    },
  });
}

export function useDeleteTrip() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => tripsApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: queryKeys.trips }),
  });
}
