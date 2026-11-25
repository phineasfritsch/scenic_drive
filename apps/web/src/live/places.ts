import { round2 } from "./api";
import type { LivePlace, Origin } from "./types";

/** Scenic kinds first when two names match equally well. */
const CLASS_RANK = ["viewpoint", "peak", "beach", "waterfall", "trailhead", "town", "park", "garden", "museum", "cafe"];

export const CLASS_LABEL: Record<string, string> = {
  viewpoint: "Viewpoint",
  peak: "Peak",
  beach: "Beach",
  waterfall: "Waterfall",
  trailhead: "Trailhead",
  town: "Town",
  park: "Park",
  garden: "Garden",
  museum: "Museum",
  cafe: "Café",
};

/** Starting points, already at 2 decimals: what the server receives is exactly what is shown. */
export const ORIGINS: Origin[] = [
  { name: "Westwood", lat: 34.06, lon: -118.45 },
  { name: "Santa Monica", lat: 34.02, lon: -118.49 },
  { name: "Downtown LA", lat: 34.05, lon: -118.25 },
  { name: "Pasadena", lat: 34.15, lon: -118.14 },
];

export const SUGGESTED = ["Point Dume", "Top of Topanga Overlook", "Mount Wilson", "Griffith Observatory"];

export function mapPointOrigin(lon: number, lat: number): Origin {
  const o = { lat: round2(lat), lon: round2(lon) };
  return { name: `Map point ${o.lat.toFixed(2)}, ${o.lon.toFixed(2)}`, ...o };
}

function fold(s: string): string {
  return s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

/** Name matches, best first: whole-name prefix, then word prefix, then substring; scenic kinds break ties. */
export function searchPlaces(places: LivePlace[], query: string, limit = 8): LivePlace[] {
  const q = fold(query.trim());
  if (q.length === 0) return [];
  const scored: { place: LivePlace; score: number }[] = [];
  for (const place of places) {
    const name = fold(place.name);
    let score: number;
    if (name.startsWith(q)) score = 0;
    else if (name.split(/[\s\-–(]+/).some((w) => w.startsWith(q))) score = 1;
    else if (name.includes(q)) score = 2;
    else continue;
    const rank = CLASS_RANK.indexOf(place.cls);
    scored.push({ place, score: score * 100 + (rank < 0 ? 99 : rank) });
  }
  scored.sort((a, b) => a.score - b.score || a.place.name.localeCompare(b.place.name));
  return scored.slice(0, limit).map((s) => s.place);
}

export function kmBetween(a: [number, number], b: [number, number]): number {
  const toRad = Math.PI / 180;
  const dLat = (b[1] - a[1]) * toRad;
  const dLon = (b[0] - a[0]) * toRad;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(a[1] * toRad) * Math.cos(b[1] * toRad) * Math.sin(dLon / 2) ** 2;
  return 2 * 6371 * Math.asin(Math.sqrt(h));
}
