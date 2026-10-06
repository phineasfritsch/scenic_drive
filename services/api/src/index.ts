/**
 * Scenic Drive API — Cloudflare Worker.
 *
 * Only operational routes exist yet. Every route is listed in ROUTES so tests can enumerate them
 * (pin P-COST-01 will later assert the kill switch covers every entry, not a hand-written list).
 */
import { asnDepsFromEnv, handleAsn, handleEntitlement } from "./asn";
import { attestDepsFromEnv, handleAttest, handleAttestChallenge } from "./attest";
import { handleIsochrone, isochroneDepsFromEnv } from "./isochrone";
import { handleLoop, loopDepsFromEnv } from "./loop";
import { handlePlan, planDepsFromEnv } from "./plan";
import type { QuotaCounter } from "./QuotaCounter";
import { readOnlyProblem } from "./ro";
import { handleTelemetry, telemetryDepsFromEnv } from "./telemetry";
import { handleTrip, tripDepsFromEnv } from "./trip";

export { QuotaCounter } from "./QuotaCounter";

export interface Env {
  DB: D1Database;
  GIT_SHA: string;
  BUILT_AT: string;
  RO_TOKEN?: string; // secret: `wrangler secret put RO_TOKEN`
  KILL?: string; // "1" pauses /plan, /loop, /isochrone and /trip with zero upstream calls (P-COST-01)
  KILL_SWITCH?: KVNamespace; // optional: its key KILL = "1" also pauses (T-0256 R5); not bound in wrangler.jsonc
  QUOTA?: DurableObjectNamespace<QuotaCounter>; // per-device daily + global monthly counters (T-0256 R1)
  ROUTER_URL?: string; // our GraphHopper; https://router.invalid (the shipped placeholder) counts as absent
  ROUTER_SECRET?: string; // secret: `wrangler secret put ROUTER_SECRET`; sent as x-scenic-router-secret
  ASN_ALLOW_SANDBOX?: string; // "1" applies App Store Sandbox notifications too (T-0267 R7); unset = production only
  SESSION_JWT_SECRET?: string; // secret: `wrangler secret put SESSION_JWT_SECRET`; absent, /attest is 503 (T-0278 R7)
  IDENTITY_HEADERS?: string; // "1" = the bare x-scenic-device / x-scenic-account-token migration window (T-0278 R6)
  APP_ATTEST_ALLOW_DEVELOP?: string; // "1" accepts the appattestdevelop aaguid (T-0278 R4); unset = production only
  TELEMETRY?: AnalyticsEngineDataset; // T-0279: the Analytics Engine binding /telemetry writes to (declared, not created)
  GRAPH_VERSION?: string; // the routing graph's version, in the /isochrone cache key (T-0262 R6); unset = "unversioned"
}

type Handler = (req: Request, env: Env, url: URL) => Promise<Response>;

const json = (body: unknown, status = 200, extra: Record<string, string> = {}) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", ...extra },
  });

// The corpus schema this Worker speaks for. ONE value with services/etl/etl/schema.py's SCHEMA_VERSION:
// a device downloads a corpus only when the two agree (plan, Runtime lifecycles / OTA), and there is no
// compiler between a Python literal and this one. ops/lib/check-schema-version reads both and refuses on
// disagreement; P-PROD-05 is what runs it. Bumping this alone is exactly the defect it guards.
export const SCHEMA_VERSION = 3;

async function dbUp(env: Env): Promise<boolean> {
  try {
    const r = await env.DB.prepare("SELECT 1 AS one").first<{ one: number }>();
    return r?.one === 1;
  } catch {
    return false;
  }
}

const health: Handler = async (_req, env) => {
  const db = await dbUp(env);
  return json({ ok: db, db: db ? "up" : "down", git_sha: env.GIT_SHA }, db ? 200 : 503);
};

const version: Handler = async (_req, env) =>
  json({ git_sha: env.GIT_SHA, built_at: env.BUILT_AT, schema_version: SCHEMA_VERSION });

/** Read-only SQL for ops/prod-read. Bearer token + grammar allowlist; never more than 200 rows. */
const ro: Handler = async (req, env) => {
  if (req.method !== "POST") return json({ error: "POST only" }, 405);
  const token = req.headers.get("authorization")?.replace(/^Bearer\s+/i, "") ?? "";
  if (!env.RO_TOKEN || token.length === 0 || token !== env.RO_TOKEN) return json({ error: "unauthorized" }, 401);
  let sql = "";
  try {
    sql = String(((await req.json()) as { sql?: unknown }).sql ?? "");
  } catch {
    return json({ error: "body must be JSON {sql}" }, 400);
  }
  const problem = readOnlyProblem(sql);
  if (problem) return json({ error: `refused: ${problem}` }, 400);
  try {
    const { results } = await env.DB.prepare(sql).all();
    return json({ rows: results.slice(0, 200), truncated: results.length > 200 });
  } catch (e) {
    return json({ error: `d1: ${(e as Error).message}` }, 400);
  }
};

export const ROUTES: Record<string, Handler> = {
  "/__health": health,
  "/__version": version,
  "/__ro": ro,
  "/plan": (req, env) => handlePlan(req, env, planDepsFromEnv(env)),
  "/loop": (req, env) => handleLoop(req, env, loopDepsFromEnv(env)),
  "/isochrone": (req, env) => handleIsochrone(req, env, isochroneDepsFromEnv(env)),
  "/trip": (req, env) => handleTrip(req, env, tripDepsFromEnv(env)),
  "/asn": (req, env) => handleAsn(req, asnDepsFromEnv(env)),
  "/entitlement": (req, env) => handleEntitlement(req, asnDepsFromEnv(env)),
  "/attest/challenge": (req, env) => handleAttestChallenge(req, attestDepsFromEnv(env)),
  "/attest": (req, env) => handleAttest(req, attestDepsFromEnv(env)),
  "/telemetry": (req, env) => handleTelemetry(req, env, telemetryDepsFromEnv(env)),
};

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    const handler = ROUTES[url.pathname];
    if (!handler) return json({ error: "not found" }, 404);
    return handler(req, env, url);
  },
} satisfies ExportedHandler<Env>;
