/**
 * GET and POST /ledger (T-0302): the Surprise places a signed-in device was shown, kept 90 days so the no-repeat
 * survives a reinstall. The user is the verified session JWT's sub and nothing else (R1): no usable SESSION_JWT_SECRET
 * is 503 auth_unavailable, no verified Bearer is 401. A row is (user_id, place_id, cell, day) - a corpus place id, an
 * H3 resolution-5 cell and the UTC day; never a coordinate, never an instant finer than a day (R2, P-PRIV-05).
 * POST takes exactly {place_id, cell}, deletes every user's rows older than the window and records one row per
 * (user, place, day) (R3, R4). GET answers the caller's rows of the last 90 UTC days, newest day first (R5). D1 only:
 * outside the quota and the kill switch by ruling, as /waitlist (R7). T-0304: a POST is admitted only while the caller
 * holds fewer than LEDGER_DAILY_CAP rows dated today or already holds this place today; otherwise 429 and nothing is
 * written. The admission, the purge and the insert are one D1 batch, each guarded by the same predicate (R2, R3).
 */
import { isResolution5Cell } from "./h3Res5";
import { DAILY_SURPRISE_QUOTA } from "./quota";
import { AUTHORIZATION_HEADER, BEARER } from "./sessionIdentity";
import { sessionSecret, verifySession } from "./sessionJwt";

/** A row dated this many UTC days before today is the oldest one kept and returned. */
export const LEDGER_WINDOW_DAYS = 90;
/** segid.py place_id: fnv1a64 masked to 63 bits, 0 replaced by 1, so a corpus id is 1 ... 2^63 - 1. */
export const MAX_PLACE_ID = 9223372036854775807n;
const PLACE_ID = /^[1-9][0-9]{0,18}$/;
const BODY_KEYS = ["cell", "place_id"];
const DAY_MS = 86_400_000;
/** T-0304 R1: the most rows one user adds per UTC day - the paid Surprise allowance BY REFERENCE, never a literal. */
export const LEDGER_DAILY_CAP = DAILY_SURPRISE_QUOTA.paid;

/** ?1 user, ?2 place, ?3 today, ?4 the cap: under the cap today, or this place already held today (T-0304 R2). */
const ADMITTED = "((SELECT count(*) FROM surprise_ledger WHERE user_id = ?1 AND day = ?3) < ?4 "
  + "OR EXISTS (SELECT 1 FROM surprise_ledger WHERE user_id = ?1 AND place_id = ?2 AND day = ?3))";
export const ADMIT_LEDGER = `SELECT ${ADMITTED} AS admitted`;
/** ?5 the window's first day. */
export const PURGE_LEDGER = `DELETE FROM surprise_ledger WHERE day < ?5 AND ${ADMITTED}`;
/** ?6 the cell; WHERE also settles SQLite's INSERT ... SELECT ... ON CONFLICT parse. */
export const INSERT_LEDGER = `INSERT INTO surprise_ledger (user_id, place_id, cell, day) SELECT ?1, ?2, ?6, ?3 WHERE ${ADMITTED} `
  + "ON CONFLICT (user_id, place_id, day) DO NOTHING";
export const READ_LEDGER = "SELECT place_id, cell, day FROM surprise_ledger WHERE user_id = ?1 AND day >= ?2 "
  + "ORDER BY day DESC, place_id ASC";

export interface LedgerDeps {
  db: D1Database | undefined;
  /** sessionSecret(SESSION_JWT_SECRET): null when unbound or shorter than MIN_SECRET_LENGTH. */
  secret: string | null;
  now(): Date;
}

export function ledgerDepsFromEnv(env: { DB?: D1Database; SESSION_JWT_SECRET?: string }): LedgerDeps {
  return { db: env.DB, secret: sessionSecret(env.SESSION_JWT_SECRET), now: () => new Date() };
}

const json = (body: unknown, status: number) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });

const UNAVAILABLE = () => json({ error: "ledger_unavailable" }, 503);

/** The window's first UTC day, YYYY-MM-DD: `now` less LEDGER_WINDOW_DAYS whole days (a UTC day has no DST). */
export function windowStart(now: Date): string {
  return new Date(now.getTime() - LEDGER_WINDOW_DAYS * DAY_MS).toISOString().slice(0, 10);
}

/** The verified session's sub, or null: the ONE read of the Authorization header. */
async function caller(req: Request, secret: string, nowMs: number): Promise<string | null> {
  const match = BEARER.exec(req.headers.get(AUTHORIZATION_HEADER) ?? "");
  return match === null ? null : ((await verifySession(secret, match[1]!, nowMs))?.sub ?? null);
}

/** The one entry the body carries, or the sentence that refuses it (R3). */
function parseEntry(raw: unknown): { placeId: string; cell: string } | { problem: string } {
  if (raw === null || typeof raw !== "object" || Array.isArray(raw)) return { problem: "the body must be a JSON object" };
  if (Object.keys(raw).sort().join() !== BODY_KEYS.join()) return { problem: "the body must be exactly {place_id, cell}" };
  const { place_id: placeId, cell } = raw as { place_id: unknown; cell: unknown };
  if (typeof placeId !== "string" || !PLACE_ID.test(placeId) || BigInt(placeId) > MAX_PLACE_ID) {
    return { problem: "place_id is not a corpus place id" };
  }
  if (typeof cell !== "string" || !isResolution5Cell(cell)) return { problem: "cell is not an H3 resolution-5 cell" };
  return { placeId, cell };
}

async function readLedger(db: D1Database | undefined, user: string, first: string): Promise<Response> {
  try {
    const { results } = await (db as D1Database).prepare(READ_LEDGER).bind(user, first)
      .all<{ place_id: string; cell: string; day: string }>();
    return json({ places: results.map((r) => ({ place_id: r.place_id, cell: r.cell, day: r.day })) }, 200);
  } catch {
    return UNAVAILABLE();
  }
}

export async function handleLedger(req: Request, deps: LedgerDeps): Promise<Response> {
  if (req.method !== "GET" && req.method !== "POST") return json({ error: "GET or POST only" }, 405);
  if (deps.secret === null) return json({ error: "auth_unavailable" }, 503);
  const now = deps.now();
  const user = await caller(req, deps.secret, now.getTime());
  if (user === null) return json({ error: "unauthorized" }, 401);
  const first = windowStart(now);
  if (req.method === "GET") return readLedger(deps.db, user, first);

  let raw: unknown;
  try {
    raw = await req.json();
  } catch {
    return json({ error: "invalid_request", detail: "the body is not JSON" }, 400);
  }
  const parsed = parseEntry(raw);
  if ("problem" in parsed) return json({ error: "invalid_request", detail: parsed.problem }, 400);
  const today = now.toISOString().slice(0, 10);
  let admitted: unknown;
  try {
    const db = deps.db as D1Database;
    const [admit] = await db.batch<{ admitted: number }>([
      db.prepare(ADMIT_LEDGER).bind(user, parsed.placeId, today, LEDGER_DAILY_CAP),
      db.prepare(PURGE_LEDGER).bind(user, parsed.placeId, today, LEDGER_DAILY_CAP, first),
      db.prepare(INSERT_LEDGER).bind(user, parsed.placeId, today, LEDGER_DAILY_CAP, first, parsed.cell),
    ]);
    admitted = admit?.results[0]?.admitted;
  } catch {
    return UNAVAILABLE();
  }
  return admitted === 1 ? json({ recorded: true }, 200) : json({ error: "ledger_daily_cap" }, 429);
}
