/**
 * The scenic plan over our router - the port of Sources/ScenicKit/Plan/ScenicPlanner.plan (T-0248 R7).
 *
 * One fastest request (car_fast, no model), then LambdaSearch over car_scenic requests carrying
 * buildCustomModel(lambda, null). Every route the search measures is kept, keyed by formatMultiplier(lambda),
 * because the plan is built from the ROUTE at the winning lambda, never from the duration the search
 * remembered. Then the two guards ScenicPlanner owns, over values recomputed HERE:
 *   1. the ceiling - the chosen route's own `time` <= fastest + budget, else nothing is returned;
 *   2. actually different - Jaccard over OSM way ids < 0.6, else the "scenic" route is the fastest one.
 */
import type { ClosuresFor } from "./closuresNearest";
import { buildCustomModel, formatMultiplier, rejectCustomModel } from "./customModel";
import { appleMapsUrl } from "./appleMaps";
import { hazardsOf, HAZARD_DETAILS, type Hazard } from "./hazards";
import { searchLambda } from "./lambdaSearch";
import type { LatLon } from "./latLon";
import { decisionPoints } from "./planWaypoints";
import { decodeRoutePath, durationSeconds, MAXIMUM_OVERLAP, overlap, RouteError, wayIds, type RoutePath } from "./routePath";
import type { GuardedFetch } from "./upstream";

export const FAST_PROFILE = "car_fast";
export const SCENIC_PROFILE = "car_scenic";
/** The details ops/plan asks for, then the hazard details the Worker adds after the model gate (plan :120). */
export const ROUTE_DETAILS = ["scenic_score", "road_class", "osm_way_id", ...HAZARD_DETAILS];
/** LambdaSearch's default; 1 fastest + 6 scenic = 7 requests, inside PLAN_UPSTREAM_COST (P-COST-04). */
export const MAX_EVALUATIONS = 6;

export type PlanRefusal = "ceiling_breached" | "no_scenic_alternative" | "no_recorded_lambda";

export class PlanFailure extends Error {
  readonly reason: PlanRefusal;

  constructor(reason: PlanRefusal, message: string) {
    super(message);
    this.reason = reason;
    this.name = "PlanFailure";
  }
}

export interface ScenicPlanResult {
  route: { coordinates: [number, number][]; distance_m: number };
  eta_s: number;
  fastest_eta_s: number;
  ceiling_s: number;
  budget_s: number;
  lambda: number;
  evaluations: number;
  used_budget: boolean;
  eta_is_estimate: true;
  hazards: Hazard[];
  waypoints: LatLon[];
  apple_maps_url: string;
}

async function route(call: GuardedFetch, routerBase: string, origin: LatLon, destination: LatLon,
  profile: string, model: unknown): Promise<RoutePath> {
  const body: Record<string, unknown> = {
    points: [[origin.lon, origin.lat], [destination.lon, destination.lat]],
    profile,
    points_encoded: false,
    instructions: false,
    "ch.disable": true,
    details: ROUTE_DETAILS,
  };
  if (model !== undefined) {
    // The gate reads the MODEL - the details list above names surface and road_access on purpose.
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

export async function planScenic(call: GuardedFetch, routerBase: string, origin: LatLon, destination: LatLon,
  budgetSeconds: number, closuresFor: ClosuresFor): Promise<ScenicPlanResult> {
  const closures = closuresFor(origin, destination);
  const fastest = await route(call, routerBase, origin, destination, FAST_PROFILE, undefined);
  const fastestSeconds = durationSeconds(fastest);
  const ceiling = fastestSeconds + budgetSeconds;

  const measured = new Map<string, RoutePath>();
  const outcome = await searchLambda(fastestSeconds, budgetSeconds, async (lambda) => {
    const path = await route(call, routerBase, origin, destination, SCENIC_PROFILE, buildCustomModel(lambda, closures));
    measured.set(formatMultiplier(lambda), path);
    return durationSeconds(path);
  }, MAX_EVALUATIONS);

  const chosen = measured.get(formatMultiplier(outcome.lambda));
  if (!chosen) throw new PlanFailure("no_recorded_lambda", `no route was measured at lambda ${outcome.lambda}`);

  const eta = durationSeconds(chosen);
  if (!(eta <= ceiling)) {
    throw new PlanFailure("ceiling_breached", `the chosen route takes ${eta} s against a ceiling of ${ceiling} s`);
  }
  const shared = overlap(wayIds(chosen), wayIds(fastest));
  if (!(shared < MAXIMUM_OVERLAP)) {
    throw new PlanFailure("no_scenic_alternative", `the scenic route shares ${shared} of its ways with the fastest`);
  }

  const waypoints = decisionPoints(chosen);
  return {
    route: { coordinates: chosen.coordinates, distance_m: chosen.distanceM },
    eta_s: eta,
    fastest_eta_s: fastestSeconds,
    ceiling_s: ceiling,
    budget_s: budgetSeconds,
    lambda: outcome.lambda,
    evaluations: outcome.evaluations,
    used_budget: outcome.usedBudget,
    eta_is_estimate: true,
    hazards: hazardsOf(chosen),
    waypoints,
    apple_maps_url: appleMapsUrl(origin, destination, waypoints),
  };
}
