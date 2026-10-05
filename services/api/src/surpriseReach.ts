/**
 * The reach a client hands Surprise.pick (T-0253's SurpriseReach.roundTripMinutes [id: Int]), from /isochrone's
 * buckets (T-0262 R8). A candidate's round-trip minutes is the round_trip_minutes - the bucket's one-way upper bound
 * x 2 - of the SMALLEST bucket whose polygon contains it: inside the outer ring and inside no hole. In no bucket it
 * is outside the reach and absent from the map. An upper bound, so with 2L <= the dial every pick fits the budget.
 * roundTripMinutesAt is the reference the Swift client ports.
 */
import type { ReachBucket, Ring } from "./isochronePlanner";
import type { LatLon } from "./latLon";

/** A bucket's round trip: there and back, each at most the bucket's one-way minutes. */
export function roundTripMinutes(oneWayMinutes: number): number {
  return 2 * oneWayMinutes;
}

/** Even-odd ray casting over a GeoJSON ring of [lon, lat]. */
export function inRing(ring: Ring, point: LatLon): boolean {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i, i += 1) {
    const [xi, yi] = ring[i]!;
    const [xj, yj] = ring[j]!;
    if (yi > point.lat !== yj > point.lat && point.lon < ((xj - xi) * (point.lat - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

/** The round trip of the smallest bucket holding `point`, or null when it is outside the reach. */
export function roundTripMinutesAt(buckets: ReachBucket[], point: LatLon): number | null {
  let best: number | null = null;
  for (const bucket of buckets) {
    const [outer, ...holes] = bucket.polygon.coordinates;
    if (outer === undefined || !inRing(outer, point) || holes.some((hole) => inRing(hole, point))) continue;
    if (best === null || bucket.round_trip_minutes < best) best = bucket.round_trip_minutes;
  }
  return best;
}
