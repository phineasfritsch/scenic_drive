/**
 * The one GraphHopper /isochrone request behind a Surprise reach (T-0262 R3), and its answer read into buckets.
 *
 * GraphHopper 11.0 (services/routing/Dockerfile): `GET /isochrone?point=<lat>,<lon>&profile=..&time_limit=<s>&buckets=<n>`
 * answers `{polygons: [Feature {properties: {bucket: i}, geometry: Polygon}]}`, bucket i covering (i + 1) / n of
 * time_limit. One request with time_limit = L minutes and n = L / 15 is every 15-min bucket at once. Polygons are read
 * by properties.bucket, never by array order; anything else is a ReachError (502 no_route).
 */
import { BUCKET_MINUTES } from "./isochroneRequest";
import type { LatLon } from "./latLon";
import { roundTripMinutes } from "./surpriseReach";
import type { GuardedFetch } from "./upstream";

/** Reach is a travel-time bound; car_fast is the time-honest profile (R3). */
export const ISOCHRONE_PROFILE = "car_fast";
/** One reach is exactly one router request (P-COST-04). */
export const ISOCHRONE_UPSTREAM_COST = 1;

/** A GeoJSON linear ring, [lon, lat] pairs. */
export type Ring = [number, number][];

export interface ReachPolygon {
  type: "Polygon";
  coordinates: Ring[];
}

export interface ReachBucket {
  minutes: number;
  round_trip_minutes: number;
  polygon: ReachPolygon;
}

export class ReachError extends Error {}

/** The one request: the one coordinate at 2 dp, the one-way limit in seconds, one bucket per 15 minutes. */
export function isochroneUrl(routerBase: string, start: LatLon, limit: number): string {
  const query = new URLSearchParams({
    point: `${start.lat.toFixed(2)},${start.lon.toFixed(2)}`,
    profile: ISOCHRONE_PROFILE,
    time_limit: String(limit * 60),
    buckets: String(limit / BUCKET_MINUTES),
    reverse_flow: "false",
  });
  return `${routerBase}/isochrone?${query.toString()}`;
}

function ring(value: unknown): Ring | null {
  if (!Array.isArray(value) || value.length < 4) return null;
  const out: Ring = [];
  for (const position of value) {
    if (!Array.isArray(position) || position.length < 2) return null;
    const [lon, lat] = position as unknown[];
    if (typeof lon !== "number" || typeof lat !== "number" || !Number.isFinite(lon) || !Number.isFinite(lat)) return null;
    out.push([lon, lat]);
  }
  return out;
}

function polygon(geometry: unknown): ReachPolygon | null {
  const g = geometry as { type?: unknown; coordinates?: unknown } | null;
  if (g?.type !== "Polygon" || !Array.isArray(g.coordinates) || g.coordinates.length === 0) return null;
  const rings = g.coordinates.map(ring);
  if (rings.some((r) => r === null)) return null;
  return { type: "Polygon", coordinates: rings as Ring[] };
}

/** GraphHopper's polygons as the L / 15 buckets, ascending; a missing, duplicated or malformed bucket refuses. */
export function readBuckets(answer: unknown, limit: number): ReachBucket[] {
  const count = limit / BUCKET_MINUTES;
  const polygons = (answer as { polygons?: unknown } | null)?.polygons;
  if (!Array.isArray(polygons)) throw new ReachError("the router answer has no polygons");
  const byBucket = new Map<number, ReachPolygon>();
  for (const feature of polygons) {
    const bucket = (feature as { properties?: { bucket?: unknown } } | null)?.properties?.bucket;
    if (typeof bucket !== "number" || !Number.isInteger(bucket) || bucket < 0 || bucket >= count || byBucket.has(bucket)) {
      throw new ReachError(`bucket ${JSON.stringify(bucket)} is not one of 0..${count - 1}, once`);
    }
    const shape = polygon((feature as { geometry?: unknown }).geometry);
    if (shape === null) throw new ReachError(`bucket ${bucket} is not a GeoJSON Polygon`);
    byBucket.set(bucket, shape);
  }
  if (byBucket.size !== count) throw new ReachError(`the router answered ${byBucket.size} of ${count} buckets`);
  return Array.from({ length: count }, (_, i) => {
    const minutes = (i + 1) * BUCKET_MINUTES;
    return { minutes, round_trip_minutes: roundTripMinutes(minutes), polygon: byBucket.get(i)! };
  });
}

export async function planReach(call: GuardedFetch, routerBase: string, start: LatLon, limit: number): Promise<ReachBucket[]> {
  const response = await call(isochroneUrl(routerBase, start, limit), { method: "GET" });
  if (!response.ok) throw new ReachError(`the router answered ${response.status}`);
  let answer: unknown;
  try {
    answer = await response.json();
  } catch {
    throw new ReachError("the router answer is not JSON");
  }
  return readBuckets(answer, limit);
}
