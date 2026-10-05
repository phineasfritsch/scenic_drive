/**
 * POST /isochrone - the Surprise reach (T-0262). The /loop order, held the same way (R5):
 *   1. KILL=1 (env, or the KV switch when bound - killSwitch.ts) -> 503 planning_paused, before the body is read.
 *   2. The body against the whitelist (R1, P-PRIV-05) -> 400. Costs nothing.
 *   3. The daily reach cache (R6): a hit answers with zero router requests and spends NO quota.
 *   4. On a miss guardedPlan with kind "surprise" and ISOCHRONE_UPSTREAM_COST: the surprise allowance and the month's
 *      call are RESERVED before the one GraphHopper /isochrone request (P-COST-01, P-COST-04).
 * ROUTES["/isochrone"] builds the deps from env; with any router binding missing it answers 503 planning_unavailable.
 */
import { killSwitch, type KillEnv } from "./killSwitch";
import { oneWayLimit, parseReachRequest } from "./isochroneRequest";
import { ISOCHRONE_UPSTREAM_COST, planReach, ReachError } from "./isochronePlanner";
import { cacheApiReachCache, reachCacheKey, UNVERSIONED_GRAPH, type ReachCache } from "./reachCache";
import { routerDepsFromEnv, type RouterDeps, type RouterEnv } from "./routerDeps";
import { guardedPlan, PlanBudgetExceeded, UpstreamPaused } from "./upstream";

export interface IsochroneDeps extends RouterDeps {
  cache: ReachCache;
  /** The graph/closures version in the cache key (R6). */
  graphVersion: string;
}

export interface IsochroneEnv extends KillEnv, RouterEnv {
  /** The routing graph's version, set with a graph rebuild; unset keys the cache as UNVERSIONED_GRAPH. */
  GRAPH_VERSION?: string;
}

const json = (body: unknown, status: number) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });

/** The production deps: T-0256's router deps, the Cache API, and GRAPH_VERSION - or null when the router is not bound. */
export function isochroneDepsFromEnv(env: IsochroneEnv): IsochroneDeps | null {
  const router = routerDepsFromEnv(env);
  if (router === null) return null;
  const version = typeof env.GRAPH_VERSION === "string" && env.GRAPH_VERSION.length > 0 ? env.GRAPH_VERSION : UNVERSIONED_GRAPH;
  return { ...router, cache: cacheApiReachCache(caches.default), graphVersion: version };
}

function failure(error: unknown): Response {
  if (error instanceof UpstreamPaused) {
    const verdict = error.verdict;
    if (!verdict.ok && verdict.reason === "quota_exhausted") {
      return json({ error: "quota_exhausted", resets_at: verdict.resetsAt }, 429);
    }
    return json({ error: "planning_paused" }, 503);
  }
  if (error instanceof ReachError || error instanceof PlanBudgetExceeded) {
    return json({ error: "no_route", detail: error.message }, 502);
  }
  throw error;
}

export async function handleIsochrone(req: Request, env: KillEnv, deps: IsochroneDeps | null): Promise<Response> {
  if (await killSwitch(env)) return json({ error: "planning_paused" }, 503);
  if (req.method !== "POST") return json({ error: "POST only" }, 405);

  let raw: unknown;
  try {
    raw = await req.json();
  } catch {
    return json({ error: "invalid_request", detail: "the body is not JSON" }, 400);
  }
  const parsed = parseReachRequest(raw);
  if (!parsed.ok) return json({ error: "invalid_request", detail: parsed.problem }, 400);
  if (deps === null) return json({ error: "planning_unavailable" }, 503);

  const { start, minutes } = parsed.request;
  const limit = oneWayLimit(minutes);
  const now = deps.upstream.now();
  const key = reachCacheKey(start, limit, now, deps.graphVersion);
  const cached = await deps.cache.get(key).catch(() => null);
  if (cached !== null) return json({ minutes, buckets: cached }, 200);

  try {
    const buckets = await guardedPlan(deps.upstream, { ...deps.identify(req), kind: "surprise" }, (call) =>
      planReach(call, deps.routerBase, start, limit), ISOCHRONE_UPSTREAM_COST);
    await deps.cache.put(key, buckets, now).catch(() => undefined);
    return json({ minutes, buckets }, 200);
  } catch (error) {
    return failure(error);
  }
}
