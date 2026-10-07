/**
 * Scenic Drive API — Cloudflare Worker.
 *
 * Only operational routes exist yet. Every route is listed in ROUTES so tests can enumerate them
 * (pin P-COST-01 will later assert the kill switch covers every entry, not a hand-written list).
 * T-0292 R1: default.fetch passes a frozen per-call copy of env; a write to that copy throws and never reaches a later call.
 * T-0297: in that copy KILL_SWITCH is a fresh frozen reader over the binding's get as first seen, never the shared binding.
 */
import { accountDepsFromEnv, handleAuthApple, handleDeleteAccount } from "./account";
import { asnDepsFromEnv, handleAsn, handleEntitlement } from "./asn";
import { attestDepsFromEnv, handleAttest, handleAttestAssert, handleAttestChallenge } from "./attest";
import { runClosuresCron } from "./closuresCron";
import { handleConfig } from "./config";
import { handleIsochrone, isochroneDepsFromEnv } from "./isochrone";
import { killSwitchReader, type KillSwitchRead } from "./killSwitch";
import { handleLoop, loopDepsFromEnv } from "./loop";
import { handlePlan, planDepsFromEnv } from "./plan";
import type { QuotaCounter } from "./QuotaCounter";
import { readOnlyProblem } from "./ro";
import { handleTelemetry, telemetryDepsFromEnv } from "./telemetry";
import { handleTrip, tripDepsFromEnv } from "./trip";
import { handleWaitlist, waitlistDepsFromEnv } from "./waitlist";

export { QuotaCounter } from "./QuotaCounter";

export interface Env {
  DB: D1Database;
  GIT_SHA: string;
  BUILT_AT: string;
  RO_TOKEN?: string; // secret: `wrangler secret put RO_TOKEN`
  KILL?: string; // "1" pauses /plan, /loop, /isochrone and /trip with zero upstream calls (P-COST-01)
  KILL_SWITCH?: KillSwitchRead; // a KVNamespace; optional: its key KILL = "1" also pauses (T-0256 R5); not bound in wrangler.jsonc
  QUOTA?: DurableObjectNamespace<QuotaCounter>; // per-device daily + global monthly counters (T-0256 R1)
  ROUTER_URL?: string; // our GraphHopper; https://router.invalid (the shipped placeholder) counts as absent
  ROUTER_SECRET?: string; // secret: `wrangler secret put ROUTER_SECRET`; sent as x-scenic-router-secret
  ASN_ALLOW_SANDBOX?: string; // "1" applies App Store Sandbox notifications too (T-0267 R7); unset = production only
  CLOSURES?: KVNamespace; // the closures cron writes it, every planning route reads it (T-0276); not bound in wrangler.jsonc
  SESSION_JWT_SECRET?: string; // secret: `wrangler secret put SESSION_JWT_SECRET`; absent, /attest is 503 (T-0278 R7)
  IDENTITY_HEADERS?: string; // "1" = the bare x-scenic-device / x-scenic-account-token migration window (T-0278 R6)
  APP_ATTEST_ALLOW_DEVELOP?: string; // "1" accepts the appattestdevelop aaguid (T-0278 R4); unset = production only
  CONFIG?: KVNamespace; // T-0288: the remote config record config/v1 /config overlays on its defaults; not bound in wrangler.jsonc
  TELEMETRY?: AnalyticsEngineDataset; // T-0279: the Analytics Engine binding /telemetry writes to (declared, not created)
  APPLE_CLIENT_SECRET?: string; // owner secret (T-0287 R6): the pre-signed Sign in with Apple client-secret JWT; absent, revoke_pending
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
  "/attest/assert": (req, env) => handleAttestAssert(req, attestDepsFromEnv(env)),
  "/telemetry": (req, env) => handleTelemetry(req, env, telemetryDepsFromEnv(env)),
  "/config": (_req, env) => handleConfig(env),
  "/auth/apple": (req, env) => handleAuthApple(req, accountDepsFromEnv(env)),
  "/account": (req, env) => handleDeleteAccount(req, accountDepsFromEnv(env)),
  "/waitlist": (req, env) => handleWaitlist(req, waitlistDepsFromEnv(env)),
};

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    const handler = ROUTES[url.pathname.length > 1 && url.pathname.endsWith("/") ? url.pathname.slice(0, -1) : url.pathname];
    if (!handler) return json({ error: "not found" }, 404);
    return handler(req, Object.freeze({ ...env, KILL_SWITCH: killSwitchReader(env.KILL_SWITCH) }), url);
  },
  async scheduled(_controller: ScheduledController, env: Env, ctx: ExecutionContext): Promise<void> {
    ctx.waitUntil(runClosuresCron({ fetchImpl: (url) => fetch(url), kv: env.CLOSURES, now: () => new Date() }));
  },
} satisfies ExportedHandler<Env>;
