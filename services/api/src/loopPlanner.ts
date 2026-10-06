/**
 * "Just drive 45 minutes and come back" over our router (T-0252, plan Problem B).
 *
 * One GraphHopper `round_trip` request from the ONE start coordinate: `round_trip.distance = v_eff * T_loop`
 * (R2), `round_trip.seed` from (user, UTC day) (R3), the custom model buildCustomModel(LOOP_LAMBDA, closures)
 * (R4). The returned geometry is held to the retrace check (retrace.ts, the port of RetraceDetector); a loop
 * that fails it is not shown. At most two retries (R5): reseed, then the same seed with `areas` over the
 * retraced road - 3 requests, LOOP_UPSTREAM_COST, which the guarded `call` enforces (P-COST-04).
 */
import { appleMapsUrl } from "./appleMaps";
import { mergeClosures } from "./closuresStore";
import { buildCustomModel, rejectCustomModel, type ClosureCollection } from "./customModel";
import type { LatLon } from "./latLon";
import { decisionPoints } from "./planWaypoints";
import { distanceMeters, isAcceptable, metersPerDegreeLongitude, METERS_PER_DEGREE_LATITUDE, retraceScan,
  type RetraceScan } from "./retrace";
import { decodeRoutePath, durationSeconds, RouteError, type RoutePath } from "./routePath";
import { ROUTE_DETAILS, SCENIC_PROFILE } from "./scenicPlanner";
import type { GuardedFetch } from "./upstream";

export const LOOP_LAMBDA = 2;
export const V_EFF_KMH = 40;
/** 1 request + 2 retries (plan Problem B, P-COST-04). */
export const LOOP_UPSTREAM_COST = 3;
export const START_CLEARANCE_M = 300;
export const AREA_SPACING_M = 100;
export const AREA_HALF_SIDE_M = 30;
export const MAX_LOOP_AREAS = 50;

export class LoopFailure extends Error {
  readonly reason = "no_clean_loop";
  readonly fraction: number | null;

  constructor(fraction: number | null) {
    super(`no loop came back under the retrace limit; the least retraced was ${fraction}`);
    this.fraction = fraction;
    this.name = "LoopFailure";
  }
}

export interface LoopResult {
  route: { coordinates: [number, number][]; distance_m: number };
  duration_s: number;
  retrace_fraction: number;
  attempts: number;
  seed: number;
  target_distance_m: number;
  minutes: number;
  eta_is_estimate: true;
  waypoints: LatLon[];
  apple_maps_url: string;
}

/** round_trip.distance in metres: minutes at V_EFF_KMH. */
export function roundTripDistance(minutes: number): number {
  return Math.round((minutes * V_EFF_KMH * 1000) / 60);
}

/** FNV-1a 32-bit over the UTF-8 of `text`, unsigned. */
export function fnv1a32(text: string): number {
  let hash = 0x811c9dc5;
  for (const byte of new TextEncoder().encode(text)) {
    hash = Math.imul((hash ^ byte) >>> 0, 0x01000193) >>> 0;
  }
  return hash >>> 0;
}

/** The seed from (user, UTC day): the same user on the same day gets the same loop. */
export function loopSeed(userId: string, day: string): number {
  return fnv1a32(`${userId}|${day}`);
}

/** Closure squares over the retraced samples: clear of the start, thinned, capped. Null when none survive. */
export function retracedAreas(retraced: LatLon[], start: LatLon): ClosureCollection | null {
  const kept: LatLon[] = [];
  for (const sample of retraced) {
    if (kept.length >= MAX_LOOP_AREAS) break;
    if (distanceMeters(start, sample) < START_CLEARANCE_M) continue;
    if (kept.some((k) => distanceMeters(k, sample) < AREA_SPACING_M)) continue;
    kept.push(sample);
  }
  if (kept.length === 0) return null;
  return {
    type: "FeatureCollection",
    features: kept.map((c) => {
      const dLat = AREA_HALF_SIDE_M / METERS_PER_DEGREE_LATITUDE;
      const dLon = AREA_HALF_SIDE_M / metersPerDegreeLongitude(c.lat);
      const ring = [[c.lon - dLon, c.lat - dLat], [c.lon + dLon, c.lat - dLat], [c.lon + dLon, c.lat + dLat],
        [c.lon - dLon, c.lat + dLat], [c.lon - dLon, c.lat - dLat]];
      return { type: "Feature" as const, geometry: { type: "Polygon" as const, coordinates: [ring] } };
    }),
  };
}

async function roundTrip(call: GuardedFetch, routerBase: string, start: LatLon, distance: number, seed: number,
  closures: ClosureCollection | null): Promise<RoutePath> {
  const model = buildCustomModel(LOOP_LAMBDA, closures);
  const problem = rejectCustomModel(model);
  if (problem !== null) throw new RouteError("router_refused", `refusing to send: ${problem}`);
  const response = await call(`${routerBase}/route`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      points: [[start.lon, start.lat]],
      profile: SCENIC_PROFILE,
      algorithm: "round_trip",
      "round_trip.distance": distance,
      "round_trip.seed": seed,
      points_encoded: false,
      instructions: false,
      "ch.disable": true,
      details: ROUTE_DETAILS,
      custom_model: model,
    }),
  });
  const path = decodeRoutePath(await response.text());
  if (!response.ok) throw new RouteError("router_refused", `router answered ${response.status}`);
  return path;
}

interface Attempt {
  path: RoutePath;
  scan: RetraceScan | null;
  seed: number;
}

const clean = (a: Attempt) => a.scan !== null && isAcceptable(a.scan.fraction);

export async function planLoop(call: GuardedFetch, routerBase: string, start: LatLon, minutes: number,
  seed: number, feed: ClosureCollection | null): Promise<LoopResult> {
  const distance = roundTripDistance(minutes);
  const tried: Attempt[] = [];
  const attempt = async (s: number, closures: ClosureCollection | null) => {
    const path = await roundTrip(call, routerBase, start, distance, s, closures);
    const made = { path, scan: retraceScan(path.coordinates.map(([lon, lat]) => ({ lat, lon }))), seed: s };
    tried.push(made);
    return made;
  };

  let current = await attempt(seed, feed);
  if (!clean(current)) {
    const reseed = (seed + 1) >>> 0;
    current = await attempt(reseed, feed);
    if (!clean(current)) {
      const areas = retracedAreas(current.scan?.retraced ?? [], start);
      if (areas !== null) current = await attempt(reseed, mergeClosures(feed, areas));
    }
  }
  if (!clean(current)) {
    const fractions = tried.flatMap((a) => (a.scan === null ? [] : [a.scan.fraction]));
    throw new LoopFailure(fractions.length === 0 ? null : Math.min(...fractions));
  }

  const chosen = current.path;
  const waypoints = decisionPoints(chosen);
  return {
    route: { coordinates: chosen.coordinates, distance_m: chosen.distanceM },
    duration_s: durationSeconds(chosen),
    retrace_fraction: current.scan!.fraction,
    attempts: tried.length,
    seed: current.seed,
    target_distance_m: distance,
    minutes,
    eta_is_estimate: true,
    waypoints,
    apple_maps_url: appleMapsUrl(start, start, waypoints),
  };
}
