/**
 * The road-trip day splitter - the port of Sources/ScenicKit/RoadTrip/RoadTrip.swift (T-0249 R3-R6, T-0268 R2).
 *
 * A -> B over N days on a +40% scenic budget: the budget ceiling first, then a forward pass over the route's edges
 * under a max drive and max distance per day, 2-4 corridor stops a day, an overnight town per boundary. Pure: it
 * reads a recorded route and a list of places and fetches nothing. Integer arithmetic throughout, unit-agnostic:
 * the Worker feeds it milliseconds and whole metres. Held to the Swift original by Tests/Fixtures/t0268/trips.json.
 * One addition to the original: `percent` (default BUDGET_PERCENT, the original's fixed 40).
 */
import type { LatLon } from "./latLon";

export const BUDGET_PERCENT = 40;
export const CORRIDOR_METERS = 5_000;
export const MAX_STOPS_PER_DAY = 4;
export const OVERNIGHT_RADIUS_METERS = 15_000;
/** Geo.earthRadiusMeters - the same sphere as the Swift original. */
export const EARTH_RADIUS_METERS = 6_371_008.8;

export interface RoadTripEdge { start: LatLon; end: LatLon; seconds: number; meters: number }
export interface RoadTripPlace { name: string; kind: "stop" | "lodging"; score: number; coordinate: LatLon }
export interface RoadTripLimits { days: number; maxDriveSeconds: number; maxMeters: number }
/** null on the last day (it arrives at B); otherwise the nearest lodging in the radius, or said absent. */
export type RoadTripOvernight = { lodging: { name: string; meters: number } } | "no_lodging" | null;
export interface RoadTripDay {
  day: number;
  start_vertex: number;
  end_vertex: number;
  seconds: number;
  meters: number;
  stops: string[];
  overnight: RoadTripOvernight;
}
export type RoadTripOutcome =
  | { plan: RoadTripDay[] }
  | { over_budget: { route_s: number; ceiling_s: number } }
  | { too_few_days: { days: number; reached_vertex: number } };

/** The extra-time budget: `percent` of the fastest, rounded DOWN (the ceiling's safe side). */
export function budgetSeconds(fastestSeconds: number, percent: number = BUDGET_PERCENT): number {
  return Math.floor((fastestSeconds * percent) / 100);
}

const radians = (degrees: number) => (degrees * Math.PI) / 180;

/** Geo.distanceMeters: haversine, written as the Swift original writes it. */
export function distanceMeters(a: LatLon, b: LatLon): number {
  const lat1 = radians(a.lat), lat2 = radians(b.lat);
  const dLat = radians(b.lat - a.lat);
  const dLon = radians(b.lon - a.lon);
  const h = Math.sin(dLat / 2) * Math.sin(dLat / 2) + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
  return 2 * EARTH_RADIUS_METERS * Math.asin(Math.min(1, Math.sqrt(h)));
}

interface Span { start: number; end: number; seconds: number; meters: number }

/** R4: day d drives until it holds an edge AND has reached its even share (cumulative x N >= d x total), and never
 *  past either limit (both inclusive). A day that cannot take its first edge ends the pass. */
function forwardPass(edges: RoadTripEdge[], total: number, limits: RoadTripLimits): Span[] {
  const spans: Span[] = [];
  let index = 0, cumulative = 0;
  for (let day = 1; day <= limits.days; day++) {
    if (index >= edges.length) break;
    const start = index;
    let seconds = 0, meters = 0;
    while (index < edges.length) {
      const edge = edges[index]!;
      if (index > start && cumulative * limits.days >= day * total) break;
      if (seconds + edge.seconds > limits.maxDriveSeconds || meters + edge.meters > limits.maxMeters) break;
      seconds += edge.seconds;
      meters += edge.meters;
      cumulative += edge.seconds;
      index += 1;
    }
    if (index <= start) break;
    spans.push({ start, end: index, seconds, meters });
  }
  return spans;
}

interface CorridorStop { place: RoadTripPlace; vertex: number }

/** R5: a stop whose nearest vertex (ties -> the lower index) lies within CORRIDOR_METERS. */
function corridorStops(places: RoadTripPlace[], vertices: LatLon[]): CorridorStop[] {
  const found: CorridorStop[] = [];
  for (const place of places) {
    if (place.kind !== "stop") continue;
    let best = 0, bestMeters = Infinity;
    vertices.forEach((vertex, i) => {
      const meters = distanceMeters(place.coordinate, vertex);
      if (meters < bestMeters) {
        best = i;
        bestMeters = meters;
      }
    });
    if (bestMeters <= CORRIDOR_METERS) found.push({ place, vertex: best });
  }
  return found;
}

const byName = (a: string, b: string) => (a < b ? -1 : a > b ? 1 : 0);

/** R5: the day owns vertices (start, end], day 1 also vertex 0; the top MAX_STOPS_PER_DAY by score (ties -> lower
 *  vertex, then name), listed in route order (vertex, then name). */
function stops(corridor: CorridorStop[], start: number, end: number): string[] {
  const first = start === 0 ? 0 : start + 1;
  const owned = corridor.filter((c) => c.vertex >= first && c.vertex <= end);
  const ranked = [...owned].sort((a, b) =>
    a.place.score !== b.place.score ? b.place.score - a.place.score
      : a.vertex !== b.vertex ? a.vertex - b.vertex : byName(a.place.name, b.place.name));
  return ranked.slice(0, MAX_STOPS_PER_DAY)
    .sort((a, b) => (a.vertex !== b.vertex ? a.vertex - b.vertex : byName(a.place.name, b.place.name)))
    .map((c) => c.place.name);
}

/** R6: the nearest lodging within OVERNIGHT_RADIUS_METERS of the boundary (ties -> name), or said absent. */
function overnight(boundary: LatLon, lodgings: RoadTripPlace[]): RoadTripOvernight {
  let best: { name: string; meters: number } | null = null;
  for (const lodging of lodgings) {
    const meters = distanceMeters(lodging.coordinate, boundary);
    if (!(meters <= OVERNIGHT_RADIUS_METERS)) continue;
    if (best !== null && (best.meters < meters || (best.meters === meters && best.name < lodging.name))) continue;
    best = { name: lodging.name, meters };
  }
  return best === null ? "no_lodging" : { lodging: { name: best.name, meters: Math.round(best.meters) } };
}

/** The whole day plan (T-0249 R3-R6): the ceiling first, then the forward pass, then each day's stops and night. */
export function planRoadTrip(edges: RoadTripEdge[], places: RoadTripPlace[], fastestSeconds: number,
  limits: RoadTripLimits, percent: number = BUDGET_PERCENT): RoadTripOutcome {
  const total = edges.reduce((sum, e) => sum + e.seconds, 0);
  const ceiling = fastestSeconds + budgetSeconds(fastestSeconds, percent);
  if (total > ceiling) return { over_budget: { route_s: total, ceiling_s: ceiling } };
  if (edges.length === 0) return { plan: [] };
  if (limits.days < 1) return { too_few_days: { days: limits.days, reached_vertex: 0 } };
  const spans = forwardPass(edges, total, limits);
  const reached = spans.length > 0 ? spans[spans.length - 1]!.end : 0;
  if (reached !== edges.length) return { too_few_days: { days: limits.days, reached_vertex: reached } };
  const vertices = [edges[0]!.start, ...edges.map((e) => e.end)];
  const corridor = corridorStops(places, vertices);
  const lodgings = places.filter((p) => p.kind === "lodging");
  return {
    plan: spans.map((span, index) => ({
      day: index + 1, start_vertex: span.start, end_vertex: span.end, seconds: span.seconds, meters: span.meters,
      stops: stops(corridor, span.start, span.end),
      overnight: index === spans.length - 1 ? null : overnight(vertices[span.end]!, lodgings),
    })),
  };
}
