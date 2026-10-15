/**
 * POST /search - typed address search through our Photon (T-0359). The /isochrone order (R5):
 *   1. KILL=1 (env, or the KV switch when bound - killSwitch.ts) -> 503 planning_paused, before the body is read.
 *   2. POST only (405), then the body against the whitelist (R3, P-PRIV-05) -> 400. Costs nothing.
 *   3. No Photon binding -> 503 search_unavailable; a session that does not verify -> 401 session_rejected.
 *   4. guardedPlan with kind "search" and SEARCH_UPSTREAM_COST: the daily search allowance and the month's call are
 *      RESERVED before the one Photon request (P-COST-01).
 * The request upstream is photonUrl's (R4) with x-scenic-search-secret and nothing else; the answer is
 * readPhotonAnswer's, fail-closed (R6).
 */
import { killSwitch, type KillEnv } from "./killSwitch";
import { routerBase, routerDepsFromEnv, type RouterEnv } from "./routerDeps";
import { readPhotonAnswer } from "./searchAnswer";
import { parseSearchRequest, photonUrl } from "./searchRequest";
import { guardedPlan, UpstreamPaused, type UpstreamDeps } from "./upstream";
import type { Identity } from "./routerDeps";

/** Every request to our Photon carries this, valued SEARCH_SECRET; the box's Caddy refuses without it (R10). */
export const SEARCH_SECRET_HEADER = "x-scenic-search-secret";
/** One search is one Photon request. */
export const SEARCH_UPSTREAM_COST = 1;

export interface SearchEnv extends KillEnv, RouterEnv {
  /** https://... of our Photon's front door; `/api` is appended. Absent, not https or *.invalid: 503. */
  SEARCH_URL?: string;
  /** secret: `wrangler secret put SEARCH_SECRET`. */
  SEARCH_SECRET?: string;
}

export interface SearchDeps {
  upstream: UpstreamDeps;
  searchBase: string;
  identify(req: Request): Promise<Identity>;
}

const json = (body: unknown, status: number) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });

/** The production deps: the router deps' quota counters and identity over SEARCH_URL, with the search secret's header,
 *  or null when any of QUOTA, a routable SEARCH_URL or SEARCH_SECRET is missing. ROUTER_URL plays no part. */
export function searchDepsFromEnv(env: SearchEnv): SearchDeps | null {
  const base = routerBase(env.SEARCH_URL);
  const secret = env.SEARCH_SECRET;
  if (base === null || typeof secret !== "string" || secret.length === 0) return null;
  const router = routerDepsFromEnv({ ...env, ROUTER_URL: base, ROUTER_SECRET: secret });
  if (router === null) return null;
  const fetchImpl = (url: string, init?: RequestInit): Promise<Response> =>
    fetch(url, { ...init, headers: { [SEARCH_SECRET_HEADER]: secret } });
  return { upstream: { ...router.upstream, fetchImpl }, searchBase: base, identify: router.identify };
}

async function photon(call: (url: string, init?: RequestInit) => Promise<Response>, url: string): Promise<Response> {
  let response: Response;
  try {
    response = await call(url, { method: "GET" });
  } catch {
    return json({ error: "search_failed" }, 502);
  }
  if (response.status !== 200) return json({ error: "search_failed" }, 502);
  let body: unknown;
  try {
    body = await response.json();
  } catch {
    return json({ error: "search_failed" }, 502);
  }
  const results = readPhotonAnswer(body);
  return results === null ? json({ error: "search_failed" }, 502) : json({ results }, 200);
}

export async function handleSearch(req: Request, env: KillEnv, deps: SearchDeps | null): Promise<Response> {
  if (await killSwitch(env)) return json({ error: "planning_paused" }, 503);
  if (req.method !== "POST") return json({ error: "POST only" }, 405);

  let raw: unknown;
  try {
    raw = await req.json();
  } catch {
    return json({ error: "invalid_request", detail: "the body is not JSON" }, 400);
  }
  const parsed = parseSearchRequest(raw);
  if (!parsed.ok) return json({ error: "invalid_request", detail: parsed.problem }, 400);
  if (deps === null) return json({ error: "search_unavailable" }, 503);

  const who = await deps.identify(req);
  if (who.rejected === true) return json({ error: "session_rejected" }, 401);
  const url = photonUrl(deps.searchBase, parsed.request);
  try {
    return await guardedPlan(deps.upstream, { userId: who.userId, tier: who.tier, kind: "search" },
      (call) => photon(call, url), SEARCH_UPSTREAM_COST);
  } catch (error) {
    if (error instanceof UpstreamPaused) {
      const verdict = error.verdict;
      if (!verdict.ok && verdict.reason === "quota_exhausted") {
        return json({ error: "quota_exhausted", resets_at: verdict.resetsAt }, 429);
      }
      return json({ error: "planning_paused" }, 503);
    }
    throw error;
  }
}
