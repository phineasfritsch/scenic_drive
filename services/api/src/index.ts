/**
 * Scenic Drive API — Cloudflare Worker.
 *
 * Only operational routes exist yet. Every route is listed in ROUTES so tests can enumerate them
 * (pin P-COST-01 will later assert the kill switch covers every entry, not a hand-written list).
 */
import { readOnlyProblem } from "./ro";

export interface Env {
  DB: D1Database;
  GIT_SHA: string;
  BUILT_AT: string;
  RO_TOKEN?: string; // secret: `wrangler secret put RO_TOKEN`
}

type Handler = (req: Request, env: Env, url: URL) => Promise<Response>;

const json = (body: unknown, status = 200, extra: Record<string, string> = {}) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", ...extra },
  });

export const SCHEMA_VERSION = 0;

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
};

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    const handler = ROUTES[url.pathname];
    if (!handler) return json({ error: "not found" }, 404);
    return handler(req, env, url);
  },
} satisfies ExportedHandler<Env>;
