/**
 * The road trip over our router (T-0268 R3-R7). At most TRIP_UPSTREAM_COST requests, in this order:
 *   1. the fastest A->B (car_fast, no model)                                      1
 *   2. searchLambda over car_scenic A->B at MAX_EVALUATIONS, keeping every path   <= 6
 *   3. FULL only: ONE car_scenic leg per day at the winning lambda               <= MAX_TRIP_DAYS (5)
 * Every A->B request asks for the per-edge `time` (ms) and `distance` (m) runs; the chosen path's runs become the
 * splitter's edges (roadTrip.ts, fed milliseconds and whole metres). The ceiling is held per day and for the trip:
 * the splitter refuses a route over fastest + budget, each day's ceiling is its share of that, and a full leg over
 * its day's ceiling refuses the whole trip.
 * The places are the server's own trip_places rows (T-0316); null when the read failed, and then every night is
 * "not_searched" and places_searched false - a search that did not happen is never reported as "no_lodging".
 */
import type { ClosuresFor, PathGuard } from "./closuresNearest";
import { buildCustomModel, formatMultiplier, rejectCustomModel } from "./customModel";
import { searchLambda } from "./lambdaSearch";
import type { LatLon } from "./latLon";
import { budgetSeconds, planRoadTrip, type RoadTripEdge, type RoadTripOvernight, type RoadTripPlace } from "./roadTrip";
import { decodeRoutePath, durationSeconds, RouteError, type RoutePath } from "./routePath";
import { isHonestFailure, routeScoreOf } from "./routeScore";
import { FAST_PROFILE, MAX_EVALUATIONS, SCENIC_PROFILE } from "./scenicPlanner";
import type { GuardedFetch } from "./upstream";

export const TRIP_UPSTREAM_COST = 12;
/** time and distance cut the days; scenic_score is what the chosen route is scored with (T-0335 R2). */
export const TRIP_DETAILS = ["time", "distance", "scenic_score"];
/** R7: a day drives at most 6 h and 300 mi (1609.344 m a mile, to the metre). */
export const MAX_DRIVE_MS_PER_DAY = 21_600_000;
export const MAX_METERS_PER_DAY = 482_803;

export type TripRefusal = "ceiling_breached" | "too_few_days" | "no_recorded_lambda" | "nothing_pretty";

export class TripFailure extends Error {
  readonly reason: TripRefusal;
  constructor(reason: TripRefusal, message: string) {
    super(message);
    this.reason = reason;
    this.name = "TripFailure";
  }
}

/** A night: the nearest lodging in the radius, a search that found none, or no search (the read failed). */
export type TripOvernight = { kind: "lodging"; name: string; meters: number } | { kind: "no_lodging" } | { kind: "not_searched" };

export interface TripDayResult {
  day: number;
  start: LatLon;
  end: LatLon;
  drive_s: number;
  distance_m: number;
  ceiling_s: number;
  stops: string[];
  overnight: TripOvernight | null;
  leg: { coordinates: [number, number][]; eta_s: number; distance_m: number } | null;
}

export interface TripResult {
  view: "preview" | "full";
  route: { coordinates: [number, number][]; distance_m: number };
  eta_s: number;
  fastest_eta_s: number;
  ceiling_s: number;
  budget_s: number;
  extra_budget_pct: number;
  lambda: number;
  evaluations: number;
  eta_is_estimate: true;
  places_searched: boolean;
  days: TripDayResult[];
}

async function route(call: GuardedFetch, routerBase: string, from: LatLon, to: LatLon, profile: string,
  model: unknown): Promise<RoutePath> {
  const body: Record<string, unknown> = {
    points: [[from.lon, from.lat], [to.lon, to.lat]],
    profile,
    points_encoded: false,
    instructions: false,
    "ch.disable": true,
    details: TRIP_DETAILS,
  };
  if (model !== undefined) {
    const problem = rejectCustomModel(model);
    if (problem !== null) throw new RouteError("router_refused", `refusing to send: ${problem}`);
    body.custom_model = model;
  }
  const response = await call(`${routerBase}/route`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  const path = decodeRoutePath(await response.text());
  if (!response.ok) throw new RouteError("router_refused", `router answered ${response.status}`);
  return path;
}

const malformed = (message: string) => new RouteError("malformed_response", message);

/** The path's edges from its time and distance runs, which must tile [0, last point] edge for edge (R3). */
export function edgesOf(path: RoutePath): RoadTripEdge[] {
  const times = path.details.time ?? [];
  const distances = path.details.distance ?? [];
  if (times.length === 0 || distances.length !== times.length) {
    throw malformed("the route carries no per-edge time and distance runs");
  }
  let at = 0;
  times.forEach((run, i) => {
    const d = distances[i]!;
    if (run.from !== at || run.to <= run.from || d.from !== run.from || d.to !== run.to) {
      throw malformed(`the time and distance runs do not tile the route at point ${at}`);
    }
    if (!Number.isInteger(run.value) || (run.value as number) < 0 || typeof d.value !== "number" ||
      !Number.isFinite(d.value) || d.value < 0) {
      throw malformed(`edge ${i} has no whole-millisecond time and finite distance`);
    }
    at = run.to;
  });
  const last = path.coordinates.length - 1;
  if (at !== last) throw malformed(`the runs end at point ${at}, not the route's last point ${last}`);
  const point = (i: number) => ({ lat: path.coordinates[i]![1], lon: path.coordinates[i]![0] });
  const edges = times.map((run, i) => ({ start: point(run.from), end: point(run.to), seconds: run.value as number,
    meters: Math.round(distances[i]!.value as number) }));
  if (edges.every((e) => e.seconds === 0)) throw malformed("the route takes no time");
  return edges;
}

/** R7: a day's share of fastest + budget, floor(ceiling x day / total), exact in BigInt (the product passes 2^53). */
function dayCeilingMs(ceilingMs: number, dayMs: number, totalMs: number): number {
  return Number((BigInt(ceilingMs) * BigInt(dayMs)) / BigInt(totalMs));
}

export async function planTrip(call: GuardedFetch, routerBase: string, origin: LatLon, destination: LatLon,
  days: number, extraBudgetPct: number, full: boolean, closuresFor: ClosuresFor, returned: PathGuard,
  places: RoadTripPlace[] | null): Promise<TripResult> {
  let used = 0;
  const counted: GuardedFetch = (url, init) => {
    used += 1;
    return call(url, init);
  };
  const closures = closuresFor(origin, destination);
  const fastest = await route(counted, routerBase, origin, destination, FAST_PROFILE, undefined);
  const fastestMs = fastest.timeMs;
  const budgetMs = budgetSeconds(fastestMs, extraBudgetPct);
  const ceilingMs = fastestMs + budgetMs;
  const measured = new Map<string, RoutePath>();
  const outcome = await searchLambda(fastestMs / 1000, budgetMs / 1000, async (lambda) => {
    const path = await route(counted, routerBase, origin, destination, SCENIC_PROFILE, buildCustomModel(lambda, closures));
    measured.set(formatMultiplier(lambda), path);
    return durationSeconds(path);
  }, MAX_EVALUATIONS);
  const measuredChosen = measured.get(formatMultiplier(outcome.lambda));
  if (!measuredChosen) throw new TripFailure("no_recorded_lambda", `no route was measured at lambda ${outcome.lambda}`);

  const splitOf = (path: RoutePath) => {
    const pathEdges = edgesOf(path);
    return { path, edges: pathEdges, split: planRoadTrip(pathEdges, places ?? [], fastestMs,
      { days, maxDriveSeconds: MAX_DRIVE_MS_PER_DAY, maxMeters: MAX_METERS_PER_DAY }, extraBudgetPct) };
  };
  const first = splitOf(measuredChosen);
  if ("over_budget" in first.split) {
    throw new TripFailure("ceiling_breached",
      `the route takes ${first.split.over_budget.route_s} ms against a ceiling of ${first.split.over_budget.ceiling_s} ms`);
  }
  if ("too_few_days" in first.split) throw new TripFailure("too_few_days", `the route needs more than ${days} days`);
  // T-0286 C3-C5: the chosen route against every stored closure; the full view reserves `days` legs inside the cap.
  const shown = await returned(first, (s) => s.path.coordinates, origin, destination,
    used + 1 + (full ? days : 0) <= TRIP_UPSTREAM_COST ? async (swapped) => {
      const again = splitOf(await route(counted, routerBase, origin, destination, SCENIC_PROFILE, buildCustomModel(outcome.lambda, swapped)));
      return "plan" in again.split ? again : null;
    } : null);
  const { path: chosen, edges, split } = shown;
  if (!("plan" in split)) throw new TripFailure("too_few_days", `the route needs more than ${days} days`);
  // T-0335 R2: the route that would ship, scored before any day leg is requested; dull or unscorable is refused.
  if (isHonestFailure(routeScoreOf(chosen))) {
    throw new TripFailure("nothing_pretty", "the chosen route scores below the honest-failure threshold");
  }

  const totalMs = edges.reduce((sum, e) => sum + e.seconds, 0);
  const vertices = [edges[0]!.start, ...edges.map((e) => e.end)];
  const night = (o: RoadTripOvernight): TripOvernight | null => o === null ? null
    : places === null ? { kind: "not_searched" } : o === "no_lodging" ? { kind: "no_lodging" }
      : { kind: "lodging", name: o.lodging.name, meters: o.lodging.meters };
  const result: TripDayResult[] = [];
  let etaMs = totalMs;
  if (full) etaMs = 0;
  for (const [index, day] of split.plan.entries()) {
    const ceiling = dayCeilingMs(ceilingMs, day.seconds, totalMs);
    let leg: TripDayResult["leg"] = null;
    if (full) {
      const [from, to] = [vertices[day.start_vertex]!, vertices[day.end_vertex]!];
      const legPath = await route(counted, routerBase, from, to, SCENIC_PROFILE, buildCustomModel(outcome.lambda, closuresFor(from, to)));
      if (legPath.timeMs > ceiling) {
        throw new TripFailure("ceiling_breached", `day ${day.day} leg takes ${legPath.timeMs} ms against its ceiling of ${ceiling} ms`);
      }
      // T-0286 C3-C5: each leg against every stored closure; it reserves the legs after it inside the cap.
      const path = await returned(legPath, (p) => p.coordinates, from, to,
        used + 1 + (split.plan.length - index - 1) <= TRIP_UPSTREAM_COST ? async (swapped) => {
          const again = await route(counted, routerBase, from, to, SCENIC_PROFILE, buildCustomModel(outcome.lambda, swapped));
          return again.timeMs > ceiling ? null : again;
        } : null);
      etaMs += path.timeMs;
      leg = { coordinates: path.coordinates, eta_s: path.timeMs / 1000, distance_m: path.distanceM };
    }
    result.push({
      day: day.day, start: vertices[day.start_vertex]!, end: vertices[day.end_vertex]!, drive_s: day.seconds / 1000,
      distance_m: day.meters, ceiling_s: ceiling / 1000, stops: day.stops,
      overnight: night(day.overnight), leg,
    });
  }
  return {
    view: full ? "full" : "preview",
    route: { coordinates: chosen.coordinates, distance_m: chosen.distanceM },
    eta_s: etaMs / 1000,
    fastest_eta_s: fastestMs / 1000,
    ceiling_s: ceilingMs / 1000,
    budget_s: budgetMs / 1000,
    extra_budget_pct: extraBudgetPct,
    lambda: outcome.lambda,
    evaluations: outcome.evaluations,
    eta_is_estimate: true,
    places_searched: places !== null,
    days: result,
  };
}
