/**
 * POST /loop - "just drive 45 minutes and come back" (T-0252). The /plan order, held the same way (R8):
 *   1. KILL=1 (env, or the KV switch when bound - killSwitch.ts) -> 503 planning_paused, before the body is read. Zero upstream calls, no reservation.
 *   2. The body against the whitelist (R1, P-PRIV-05) -> 400. Costs nothing.
 *   3. guardedPlan with LOOP_UPSTREAM_COST: the quota is read and RESERVED before the first router request, and
 *      the `call` it hands out refuses a 4th (P-COST-04).
 * Deps are injected so the tests count real fetch invocations; ROUTES["/loop"] builds them from env (T-0256,
 * routerDeps.ts) and, with any binding missing, answers 503 planning_unavailable with zero upstream calls. A loop
 * spends the LOOP allowance (kind "loop", T-0256 R4), never a plan.
 */
import { withClosuresHazard, type ClosureSnapshot } from "./closuresStore";
import { killSwitch } from "./killSwitch";
import { parseLoopRequest } from "./loopRequest";
import { LOOP_UPSTREAM_COST, LoopFailure, loopSeed, planLoop } from "./loopPlanner";
import type { PlanEnv } from "./plan";
import { dayKey } from "./quota";
import { routerDepsFromEnv, type Identity, type RouterEnv } from "./routerDeps";
import { RouteError } from "./routePath";
import { guardedPlan, PlanBudgetExceeded, UpstreamPaused, type UpstreamDeps } from "./upstream";

export interface LoopDeps {
  upstream: UpstreamDeps;
  /** Our GraphHopper, e.g. https://routing.example - `/route` is appended. */
  routerBase: string;
  /** Who is looping: the quota and the seed. */
  identify(req: Request): Identity | Promise<Identity>;
  /** The closures every driven request routes around, read once after the kill switch (T-0276). */
  closures(): Promise<ClosureSnapshot>;
}

const json = (body: unknown, status: number) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });

/** The production deps: real exactly when QUOTA, a routable ROUTER_URL and ROUTER_SECRET are all bound. */
export function loopDepsFromEnv(env: PlanEnv & RouterEnv): LoopDeps | null {
  return routerDepsFromEnv(env);
}

function failure(error: unknown): Response {
  if (error instanceof UpstreamPaused) {
    const verdict = error.verdict;
    if (!verdict.ok && verdict.reason === "quota_exhausted") {
      return json({ error: "quota_exhausted", resets_at: verdict.resetsAt }, 429);
    }
    return json({ error: "planning_paused" }, 503);
  }
  if (error instanceof LoopFailure) return json({ error: "no_clean_loop", retrace_fraction: error.fraction }, 422);
  if (error instanceof RouteError || error instanceof PlanBudgetExceeded) {
    return json({ error: "no_route", detail: error.message }, 502);
  }
  throw error;
}

export async function handleLoop(req: Request, env: PlanEnv, deps: LoopDeps | null): Promise<Response> {
  const paused = await killSwitch(env);
  if (paused) return json({ error: "planning_paused" }, 503);
  if (req.method !== "POST") return json({ error: "POST only" }, 405);

  let raw: unknown;
  try {
    raw = await req.json();
  } catch {
    return json({ error: "invalid_request", detail: "the body is not JSON" }, 400);
  }
  const parsed = parseLoopRequest(raw);
  if (!parsed.ok) return json({ error: "invalid_request", detail: parsed.problem }, 400);
  if (deps === null) return json({ error: "planning_unavailable" }, 503);

  const { request } = parsed;
  const who = await deps.identify(req);
  const snapshot = await deps.closures();
  const upstream: UpstreamDeps = { ...deps.upstream, killed: () => paused || deps.upstream.killed() };
  try {
    const seed = loopSeed(who.userId, dayKey(deps.upstream.now()));
    const loop = await guardedPlan(upstream, { ...who, kind: "loop" }, (call) =>
      planLoop(call, deps.routerBase, request.start, request.minutes, seed, snapshot.closures),
      LOOP_UPSTREAM_COST);
    return json(withClosuresHazard(loop, snapshot), 200);
  } catch (error) {
    return failure(error);
  }
}
