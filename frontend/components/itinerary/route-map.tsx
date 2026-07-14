"use client";

import { APIProvider, Map, useMap, useMapsLibrary } from "@vis.gl/react-google-maps";
import { useEffect, useMemo, useState } from "react";

import type { Itinerary } from "@/lib/schemas";

const MAPS_KEY = process.env.NEXT_PUBLIC_GOOGLE_MAPS_KEY;
const INDIA_CENTER = { lat: 20.5937, lng: 78.9629 };

/** Ordered, de-duplicated stop labels drawn from every block's location. */
function stopsFrom(itinerary: Itinerary): string[] {
  const stops: string[] = [];
  for (const day of itinerary.days) {
    for (const block of day.blocks) {
      const loc = block.location?.trim();
      if (loc && stops[stops.length - 1] !== loc) stops.push(loc);
    }
  }
  return stops;
}

/**
 * A small Google map plotting the itinerary's locations as numbered markers in
 * visiting order, joined by a route line. Locations are geocoded client-side
 * (the blocks carry only a name, not coordinates). Renders nothing if no Maps
 * key is configured or there are no locations to show.
 */
export function RouteMap({ itinerary }: { itinerary: Itinerary }) {
  const stops = useMemo(() => stopsFrom(itinerary), [itinerary]);

  if (!MAPS_KEY || stops.length === 0) return null;

  return (
    <div className="overflow-hidden rounded-lg border">
      <APIProvider apiKey={MAPS_KEY}>
        <Map
          defaultZoom={9}
          defaultCenter={INDIA_CENTER}
          gestureHandling="cooperative"
          disableDefaultUI
          style={{ width: "100%", height: 260 }}
        >
          <RouteOverlay stops={stops} region={itinerary.destination} />
        </Map>
      </APIProvider>
    </div>
  );
}

function RouteOverlay({ stops, region }: { stops: string[]; region: string }) {
  const map = useMap();
  const geocoding = useMapsLibrary("geocoding");
  const [points, setPoints] = useState<google.maps.LatLngLiteral[]>([]);

  // Geocode each stop (append the region + India to disambiguate short names).
  useEffect(() => {
    if (!geocoding) return;
    const geocoder = new geocoding.Geocoder();
    let cancelled = false;

    const locate = (label: string) =>
      new Promise<google.maps.LatLngLiteral | null>((resolve) => {
        const address = region ? `${label}, ${region}, India` : `${label}, India`;
        geocoder.geocode({ address }, (results, status) => {
          if (status === "OK" && results && results[0]) {
            const loc = results[0].geometry.location;
            resolve({ lat: loc.lat(), lng: loc.lng() });
          } else {
            resolve(null);
          }
        });
      });

    void Promise.all(stops.map(locate)).then((located) => {
      if (cancelled) return;
      setPoints(located.filter((p): p is google.maps.LatLngLiteral => p !== null));
    });

    return () => {
      cancelled = true;
    };
  }, [geocoding, stops, region]);

  // Draw markers + a connecting line, then fit the map to them.
  useEffect(() => {
    if (!map || points.length === 0) return;

    const markers = points.map(
      (position, i) =>
        new google.maps.Marker({ position, map, label: String(i + 1) }),
    );
    const line = new google.maps.Polyline({
      path: points,
      map,
      strokeColor: "#2563eb",
      strokeOpacity: 0.85,
      strokeWeight: 3,
    });

    const bounds = new google.maps.LatLngBounds();
    points.forEach((p) => bounds.extend(p));
    if (points.length === 1) {
      map.setCenter(points[0]);
      map.setZoom(12);
    } else {
      map.fitBounds(bounds, 48);
    }

    return () => {
      markers.forEach((m) => m.setMap(null));
      line.setMap(null);
    };
  }, [map, points]);

  return null;
}
