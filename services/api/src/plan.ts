/**
 * POST /plan - one request from the app becomes one scenic route (T-0248).
 *
 * The order is the property (R4, P-COST-01):
 *   1. KILL=1 -> 503 planning_paused, before the body is read. Zero upstream calls, no reservation.
 *   2. The body against the whitelist (R1/R2, P-PRIV-05) -> 400. Not an upstream call; costs no plan.
 *   3. The destination place id -> its coordinate, or 404. Not an upstream call; costs no plan.
 *   4. guardedPlan: the quota is read and RESERVED before the first router request; every request goes through
 *      the `call` it hands out, which refuses a 13th (P-COST-04).
 * Deps are injected so the tests count real fetch invocations; ROUTES["/plan"] builds them from env and, with
 * no router / counters / corpus configured, answers 503 planning_unavailable with zero upstream calls.
 */
import type { LatLon } from "./latLon";
import { BudgetError } from "./lambdaSearch";
import { parsePlanRequest } from "./planRequest";
import type { Tier } from "./quota";
import { RouteError } from "./routePath";
import { PlanFailure, planScenic } from "./scenicPlanner";
import { guardedPlan, PlanBudgetExceeded, UpstreamPaused, type UpstreamDeps } from "./upstream";

export interface PlanEnv {
  /** Manual override: "1" pauses all planning without a deploy. */
  KILL?: string;
}

export interface PlanDeps {
  upstream: UpstreamDeps;
  /** Our GraphHopper, e.g. https://routing.example - `/route` is appended. */
  routerBase: string;
  /** A corpus place id -> its coordinate, or null when the corpus does not know it. */
  resolvePlace(id: string): Promise<LatLon | null>;
  /** Who is planning, for the quota. Until /attest lands every caller is whatever this says. */
  identify(req: Request): { userId: string; tier: Tier };
}

const json = (body: unknown, status: number) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });

export const killed = (env: PlanEnv) => env.KILL === "1";

/** The production deps. None of the three exists in this Worker yet (R4), so this is null: fail closed. */
export function planDepsFromEnv(_env: PlanEnv): PlanDeps | null {
  return null;
}

function failure(error: unknown): Response {
  if (error instanceof UpstreamPaused) {
    const verdict = error.verdict;
    if (!verdict.ok && verdict.reason === "quota_exhausted") {
      return json({ error: "quota_exhausted", resets_at: verdict.resetsAt }, 429);
    }
    return json({ error: "planning_paused" }, 503);
  }
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
  if (killed(env)) return json({ error: "planning_paused" }, 503);
  if (req.method !== "POST") return json({ error: "POST only" }, 405);

  let raw: unknown;
  try {
    raw = await req.json();
  } catch {
    return json({ error: "invalid_request", detail: "the body is not JSON" }, 400);
  }
  const parsed = parsePlanRequest(raw);
  if (!parsed.ok) return json({ error: "invalid_request", detail: parsed.problem }, 400);
  if (deps === null) return json({ error: "planning_unavailable" }, 503);

  const { request } = parsed;
  const destination = await deps.resolvePlace(request.destinationPlace);
  if (destination === null) return json({ error: "unknown_place" }, 404);

  const upstream: UpstreamDeps = { ...deps.upstream, killed: () => killed(env) || deps.upstream.killed() };
  try {
    const plan = await guardedPlan(upstream, deps.identify(req), (call) =>
      planScenic(call, deps.routerBase, request.origin, destination, request.budgetMinutes * 60));
    return json(plan, 200);
  } catch (error) {
    return failure(error);
  }
}
