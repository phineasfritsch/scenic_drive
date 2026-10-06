/**
 * POST /trip - A -> B over N days (T-0268). The /plan order, held the same way:
 *   1. KILL=1 (env, or the KV switch when bound - killSwitch.ts) -> 503 planning_paused, before the body is read.
 *      Zero upstream calls, no reservation.
 *   2. The body against the whitelist (R1, P-PRIV-05) -> 400. Costs nothing.
 *   3. The destination place id -> its coordinate, or 404. Not an upstream call.
 *   4. guardedPlan with TRIP_UPSTREAM_COST under kind "trip": the quota is read and RESERVED before the first
 *      router request, and the `call` it hands out refuses a 13th (P-COST-04).
 * Free and anon get the PREVIEW, paid the FULL itinerary with one leg a day (R5, the plan's feature table). Deps
 * are injected so the tests count real fetch invocations; ROUTES["/trip"] builds them from env exactly as /plan does.
 */
import { killSwitch } from "./killSwitch";
import type { LatLon } from "./latLon";
import { BudgetError } from "./lambdaSearch";
import { planDepsFromEnv, type PlanDeps, type PlanEnv } from "./plan";
import type { RouterEnv } from "./routerDeps";
import { RouteError } from "./routePath";
import { parseTripRequest } from "./tripRequest";
import { MAX_DRIVE_MS_PER_DAY, MAX_METERS_PER_DAY, planTrip, TRIP_UPSTREAM_COST, TripFailure } from "./tripPlanner";
import { guardedPlan, PlanBudgetExceeded, UpstreamPaused, type UpstreamDeps } from "./upstream";

export { MAX_EXTRA_BUDGET_PCT, MAX_TRIP_DAYS, MIN_TRIP_DAYS } from "./tripRequest";
export { MAX_DRIVE_MS_PER_DAY, MAX_METERS_PER_DAY, TRIP_UPSTREAM_COST } from "./tripPlanner";

/** A trip needs what a plan needs: the quota, the router and the D1 place resolver. */
export type TripDeps = PlanDeps;

const json = (body: unknown, status: number) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });

/** The production deps: real exactly when QUOTA, a routable ROUTER_URL, ROUTER_SECRET and DB are all bound. */
export function tripDepsFromEnv(env: PlanEnv & RouterEnv & { DB?: D1Database }): TripDeps | null {
  return planDepsFromEnv(env);
}

function failure(error: unknown, days: number): Response {
  if (error instanceof UpstreamPaused) {
    const verdict = error.verdict;
    if (!verdict.ok && verdict.reason === "quota_exhausted") {
      return json({ error: "quota_exhausted", resets_at: verdict.resetsAt }, 429);
    }
    return json({ error: "planning_paused" }, 503);
  }
  if (error instanceof TripFailure) {
    if (error.reason === "too_few_days") {
      return json({ error: "too_few_days", days, max_drive_s: MAX_DRIVE_MS_PER_DAY / 1000, max_distance_m: MAX_METERS_PER_DAY }, 422);
    }
    if (error.reason === "ceiling_breached") return json({ error: "ceiling_breached", detail: error.message }, 422);
    return json({ error: error.reason }, 500);
  }
  if (error instanceof BudgetError || error instanceof RouteError || error instanceof PlanBudgetExceeded) {
    return json({ error: "no_route", detail: error.message }, 502);
  }
  throw error;
}

export async function handleTrip(req: Request, env: PlanEnv, deps: TripDeps | null): Promise<Response> {
  const paused = await killSwitch(env);
  if (paused) return json({ error: "planning_paused" }, 503);
  if (req.method !== "POST") return json({ error: "POST only" }, 405);

  let raw: unknown;
  try {
    raw = await req.json();
  } catch {
    return json({ error: "invalid_request", detail: "the body is not JSON" }, 400);
  }
  const parsed = parseTripRequest(raw);
  if (!parsed.ok) return json({ error: "invalid_request", detail: parsed.problem }, 400);
  if (deps === null) return json({ error: "planning_unavailable" }, 503);

  const { request } = parsed;
  let destination: LatLon | null;
  try {
    destination = await deps.resolvePlace(request.destinationPlace);
  } catch {
    return json({ error: "planning_unavailable" }, 503);
  }
  if (destination === null) return json({ error: "unknown_place" }, 404);

  const who = await deps.identify(req);
  const upstream: UpstreamDeps = { ...deps.upstream, killed: () => paused || deps.upstream.killed() };
  try {
    const trip = await guardedPlan(upstream, { ...who, kind: "trip" }, (call) =>
      planTrip(call, deps.routerBase, request.origin, destination, request.days, request.extraBudgetPct,
        who.tier === "paid"), TRIP_UPSTREAM_COST);
    return json(trip, 200);
  } catch (error) {
    return failure(error, request.days);
  }
}
