/**
 * POST /plan - one request from the app becomes one scenic route (T-0248).
 *
 * The order is the property (R4, P-COST-01):
 *   1. KILL=1 (env, or the KV switch when bound - killSwitch.ts) -> 503 planning_paused, before the body is read. Zero upstream calls, no reservation.
 *   2. The body against the whitelist (R1/R2, P-PRIV-05) -> 400. Not an upstream call; costs no plan.
 *   2b. The origin outside the served region (servedRegion.ts, T-0293) -> 422 region_unsupported. Costs nothing.
 *   3. The destination place id -> its coordinate, or 404. Not an upstream call; costs no plan.
 *   3b. T-0319 R5: a `reroute` token is recalled from PLANS; an unusable one is simply the fresh plan below.
 *   3c. T-0332: a fresh plan whose route scores below RouteScore's 0.45 is 422 nothing_pretty with its offers
 *      (honestFailure.ts); a reroute is exempt - the driver already accepted the drive.
 *   4. guardedPlan: the quota is read and RESERVED before the first router request; every request goes through
 *      the `call` it hands out, which refuses a 13th (P-COST-04).
 * Deps are injected so the tests count real fetch invocations; ROUTES["/plan"] builds them from env (T-0256:
 * routerDeps.ts + the D1 place resolver) and, with any binding missing, answers 503 planning_unavailable with zero
 * upstream calls. A resolver that cannot answer is 503 planning_unavailable too - never a 404, never a call.
 */
import { closurePicker } from "./closuresNearest";
import { withClosuresHazard, type ClosureSnapshot } from "./closuresStore";
import { killSwitch, type KillEnv } from "./killSwitch";
import type { LatLon } from "./latLon";
import { HonestFailure, honestFailureBody } from "./honestFailure";
import { BudgetError } from "./lambdaSearch";
import { d1PlaceResolver } from "./placeResolver";
import { parsePlanRequest } from "./planRequest";
import { kvPlanTokens, type PlanTokenKv, type PlanTokens, type RememberedPlan } from "./planToken";
import { planReroute } from "./reroutePlanner";
import { routerDepsFromEnv, type Identity, type RouterEnv } from "./routerDeps";
import { RouteError } from "./routePath";
import { PlanFailure, planScenic } from "./scenicPlanner";
import { inServedRegion } from "./servedRegion";
import { guardedPlan, PlanBudgetExceeded, UpstreamPaused, type UpstreamDeps } from "./upstream";

export type PlanEnv = KillEnv;

export interface PlanDeps {
  upstream: UpstreamDeps;
  /** Our GraphHopper, e.g. https://routing.example - `/route` is appended. */
  routerBase: string;
  /** A corpus place id -> its coordinate, or null when the corpus does not know it. */
  resolvePlace(id: string): Promise<LatLon | null>;
  /** Who is planning, for the quota. Until /attest lands every caller is whatever this says. */
  identify(req: Request): Identity | Promise<Identity>;
  /** The closures every driven request routes around, read once after the kill switch (T-0276). */
  closures(): Promise<ClosureSnapshot>;
  /** T-0319 R3: where every answer is remembered under its plan_token; null (or absent) when PLANS is unbound. */
  plans?: PlanTokens | null;
}

const json = (body: unknown, status: number) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });

/** The production deps: real exactly when QUOTA, a routable ROUTER_URL, ROUTER_SECRET and DB are all bound. */
export function planDepsFromEnv(env: PlanEnv & RouterEnv & { DB?: D1Database; PLANS?: PlanTokenKv }): PlanDeps | null {
  const router = routerDepsFromEnv(env);
  if (router === null || !env.DB) return null;
  return { ...router, resolvePlace: d1PlaceResolver(env.DB), plans: env.PLANS ? kvPlanTokens(env.PLANS) : null };
}

function failure(error: unknown, budgetMinutes: number): Response {
  if (error instanceof UpstreamPaused) {
    const verdict = error.verdict;
    if (!verdict.ok && verdict.reason === "quota_exhausted") {
      return json({ error: "quota_exhausted", resets_at: verdict.resetsAt }, 429);
    }
    return json({ error: "planning_paused" }, 503);
  }
  if (error instanceof HonestFailure) return json(honestFailureBody(budgetMinutes, error), 422);
  if (error instanceof PlanFailure) {
    if (error.reason === "no_scenic_alternative") return json({ error: "no_scenic_alternative" }, 422);
    return json({ error: error.reason }, 500);
  }
  if (error instanceof BudgetError || error instanceof RouteError || error instanceof PlanBudgetExceeded) {
    return json({ error: "no_route", detail: error.message }, 502);
  }
  throw error;
}

export async function handlePlan(req: Request, env: PlanEnv, deps: PlanDeps | null): Promise<Response> {
  const paused = await killSwitch(env);
  if (paused) return json({ error: "planning_paused" }, 503);
  if (req.method !== "POST") return json({ error: "POST only" }, 405);

  let raw: unknown;
  try {
    raw = await req.json();
  } catch {
    return json({ error: "invalid_request", detail: "the body is not JSON" }, 400);
  }
  const parsed = parsePlanRequest(raw);
  if (!parsed.ok) return json({ error: "invalid_request", detail: parsed.problem }, 400);
  const { request } = parsed;
  if (!inServedRegion(request.origin)) return json({ error: "region_unsupported" }, 422);
  if (deps === null) return json({ error: "planning_unavailable" }, 503);

  let destination: LatLon | null;
  try {
    destination = await deps.resolvePlace(request.destinationPlace);
  } catch {
    return json({ error: "planning_unavailable" }, 503);
  }
  if (destination === null) return json({ error: "unknown_place" }, 404);

  const snapshot = await deps.closures();
  const picker = closurePicker(snapshot.closures);
  const upstream: UpstreamDeps = { ...deps.upstream, killed: () => paused || deps.upstream.killed() };
  const who = await deps.identify(req);
  const plans = deps.plans ?? null;
  const reroute = request.reroute;
  const recalled = reroute && plans ? await plans.recall(reroute.token) : null;
  const usable: RememberedPlan | null = recalled && reroute && recalled.device === who.userId &&
    recalled.place === request.destinationPlace && reroute.firstPin <= recalled.pins.length ? recalled : null;
  try {
    const plan = await guardedPlan(upstream, who, async (call) => {
      const budget = request.budgetMinutes * 60;
      const rest = usable && reroute ? await planReroute(call, deps.routerBase, request.origin, destination, budget,
        usable.pins.slice(reroute.firstPin), usable.lambda, picker.pick, picker.returned) : null;
      return rest ?? planScenic(call, deps.routerBase, request.origin, destination, budget, picker.pick, picker.returned);
    });
    const token = plans ? await plans.remember({ device: who.userId, place: request.destinationPlace,
      pins: plan.waypoints, lambda: plan.lambda }) : null;
    return json({ ...withClosuresHazard(plan, snapshot, picker.dropped(), picker.crosses()), plan_token: token }, 200);
  } catch (error) {
    return failure(error, request.budgetMinutes);
  }
}
