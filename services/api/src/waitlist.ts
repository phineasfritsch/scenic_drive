/**
 * POST /waitlist {cell} - interest from outside the served region, counted per H3 resolution-5 cell (T-0293 R8, R9),
 * one device once per cell per UTC day (T-0296).
 *
 * The body is exactly one key, `cell`, the h3ToString form of a resolution-5 cell (h3Res5.ts, the rule /telemetry
 * holds). The table keeps the cell, a count and the UTC day the count last moved - never a person, a device, an
 * instant or a coordinate (P-PRIV-06). Nothing upstream is called, so the route is outside the quota and the kill
 * switch by ruling, as /asn is.
 *
 * The dedupe (T-0296 R1-R4): who is identifyCaller's bucket, the one the quota and /telemetry use. The row that says
 * "already counted" is a tag, HMAC(dayKey, who + "\n" + cell) with dayKey = HMAC(SESSION_JWT_SECRET, prefix + day),
 * computed per request and never stored. waitlist_seen keeps (tag, day) only, and every write purges other days first.
 * Without a usable secret the route is 503 - never an unlimited count.
 */
import { isResolution5Cell } from "./h3Res5";
import { deviceIdentity } from "./routerDeps";
import { AUTHORIZATION_HEADER, identifyCaller, type SessionEnv } from "./sessionIdentity";
import { sessionSecret } from "./sessionJwt";

export const UPSERT_WAITLIST = "INSERT INTO waitlist (cell, count, updated_at) VALUES (?1, 1, ?2) "
  + "ON CONFLICT (cell) DO UPDATE SET count = count + 1, updated_at = excluded.updated_at";
export const PURGE_SEEN = "DELETE FROM waitlist_seen WHERE day <> ?1";
export const INSERT_SEEN = "INSERT INTO waitlist_seen (tag, day) VALUES (?1, ?2) ON CONFLICT (tag) DO NOTHING";
/** The domain of the daily key: HMAC under SESSION_JWT_SECRET of this prefix + the UTC day (R2). */
export const DEDUPE_KEY_PREFIX = "scenic-waitlist/v1/";

export interface WaitlistDeps {
  db: D1Database | undefined;
  /** sessionSecret(SESSION_JWT_SECRET): null when unbound or shorter than MIN_SECRET_LENGTH (R3). */
  secret: string | null;
  now(): Date;
  /** identifyCaller's bucket for this request (R1); the tier is never read. */
  identify(req: Request): Promise<string>;
}

const json = (body: unknown, status: number) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });

export function waitlistDepsFromEnv(env: { DB?: D1Database } & SessionEnv): WaitlistDeps {
  const now = () => new Date();
  return {
    db: env.DB,
    secret: sessionSecret(env.SESSION_JWT_SECRET),
    now,
    identify: async (req) =>
      (await identifyCaller(req.headers.get(AUTHORIZATION_HEADER), env, now().getTime(), async () => deviceIdentity(req))).userId,
  };
}

const utf8 = (text: string) => new TextEncoder().encode(text);

async function hmac(key: Uint8Array, message: string): Promise<Uint8Array> {
  const imported = await crypto.subtle.importKey("raw", key, { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return new Uint8Array(await crypto.subtle.sign("HMAC", imported, utf8(message)));
}

/** The dedupe tag of one (who, cell) on one UTC day, lowercase hex (R2). */
export async function dedupeTag(secret: string, who: string, cell: string, day: string): Promise<string> {
  const dayKey = await hmac(utf8(secret), DEDUPE_KEY_PREFIX + day);
  return Array.from(await hmac(dayKey, `${who}\n${cell}`), (b) => b.toString(16).padStart(2, "0")).join("");
}

/** The one cell the body carries, or the sentence that refuses it. */
function parseCell(raw: unknown): { cell: string } | { problem: string } {
  if (raw === null || typeof raw !== "object" || Array.isArray(raw)) return { problem: "the body must be a JSON object" };
  const keys = Object.keys(raw);
  if (keys.length !== 1 || keys[0] !== "cell") return { problem: "the body must be exactly {cell}" };
  const cell: unknown = (raw as { cell: unknown }).cell;
  if (typeof cell !== "string" || !isResolution5Cell(cell)) return { problem: "cell is not an H3 resolution-5 cell" };
  return { cell };
}

export async function handleWaitlist(req: Request, deps: WaitlistDeps): Promise<Response> {
  if (req.method !== "POST") return json({ error: "POST only" }, 405);

  let raw: unknown;
  try {
    raw = await req.json();
  } catch {
    return json({ error: "invalid_request", detail: "the body is not JSON" }, 400);
  }
  const parsed = parseCell(raw);
  if ("problem" in parsed) return json({ error: "invalid_request", detail: parsed.problem }, 400);
  if (!deps.db) return json({ error: "waitlist_unavailable" }, 503);
  if (deps.secret === null) return json({ error: "waitlist_unavailable" }, 503);

  const day = deps.now().toISOString().slice(0, 10);
  try {
    const tag = await dedupeTag(deps.secret, await deps.identify(req), parsed.cell, day);
    await deps.db.prepare(PURGE_SEEN).bind(day).run();
    const seen = await deps.db.prepare(INSERT_SEEN).bind(tag, day).run();
    if (seen.meta.changes === 1) await deps.db.prepare(UPSERT_WAITLIST).bind(parsed.cell, day).run();
  } catch {
    return json({ error: "waitlist_unavailable" }, 503);
  }
  return json({ waitlisted: true }, 200);
}
