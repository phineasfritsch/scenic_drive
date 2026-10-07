/**
 * POST /waitlist {cell} - interest from outside the served region, counted per H3 resolution-5 cell (T-0293 R8, R9).
 *
 * The body is exactly one key, `cell`, the h3ToString form of a resolution-5 cell (h3Res5.ts, the rule /telemetry
 * holds). The table keeps the cell, a count and the UTC day the count last moved - never a person, a device, an
 * instant or a coordinate (P-PRIV-06). No identity is read and nothing upstream is called, so the route is outside
 * the quota and the kill switch by ruling, as /asn is.
 */
import { isResolution5Cell } from "./h3Res5";

export const UPSERT_WAITLIST = "INSERT INTO waitlist (cell, count, updated_at) VALUES (?1, 1, ?2) "
  + "ON CONFLICT (cell) DO UPDATE SET count = count + 1, updated_at = excluded.updated_at";

export interface WaitlistDeps {
  db: D1Database | undefined;
  now(): Date;
}

const json = (body: unknown, status: number) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });

export function waitlistDepsFromEnv(env: { DB?: D1Database }): WaitlistDeps {
  return { db: env.DB, now: () => new Date() };
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

  try {
    await deps.db.prepare(UPSERT_WAITLIST).bind(parsed.cell, deps.now().toISOString().slice(0, 10)).run();
  } catch {
    return json({ error: "waitlist_unavailable" }, 503);
  }
  return json({ waitlisted: true }, 200);
}
