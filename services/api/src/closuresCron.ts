/**
 * The closures cron (T-0276 R6): every 15 minutes, the Caltrans LCS D7 feed -> at most CLOSURES_STORED_MAX_POLYGONS
 * polygons (T-0282 N1; each request sends its own nearest 50) -> KV.
 *
 * Writes {version, fetched_at, geojson, stats} under CLOSURES_KEY, or NOTHING - the last good record stays and
 * ages into stale (closuresStore.ts) - when the binding is absent (no fetch either), the answer is not 200, has no
 * parseable Last-Modified, is not JSON, carries no non-empty `data` array, or refuses more than half its Full rows.
 * fetched_at is the FEED's age: min(Last-Modified, now). No key, no secret: the feed is public.
 */
import { CLOSURES_KEY } from "./closuresStore";
import type { ClosureCollection } from "./customModel";
import { capClosures, LCS_D7_FEED, parseLcsFeed } from "./lcsFeed";

export const CLOSURES_CRON = "*/15 * * * *";

export interface ClosuresRecord {
  version: string;
  fetched_at: string;
  geojson: ClosureCollection;
  stats: { rows: number; full: number; active: number; refused: number; kept: number; dropped: number };
}

export interface ClosuresCronDeps {
  fetchImpl: (url: string) => Promise<Response>;
  kv: Pick<KVNamespace, "put"> | undefined;
  now: () => Date;
}

export type CronOutcome =
  | { written: true; record: ClosuresRecord }
  | { written: false; reason: "unbound" | "not_ok" | "no_last_modified" | "not_json" | "no_data" | "too_many_refused" };

/** "lcs-d7-" + the first 16 hex of SHA-256 over the geojson as JSON: the same set keeps its version. */
export async function closuresVersion(geojson: ClosureCollection): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(JSON.stringify(geojson)));
  const hex = [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
  return `lcs-d7-${hex.slice(0, 16)}`;
}

export async function runClosuresCron(deps: ClosuresCronDeps): Promise<CronOutcome> {
  if (!deps.kv) return { written: false, reason: "unbound" };
  let response: Response;
  try {
    response = await deps.fetchImpl(LCS_D7_FEED);
  } catch {
    return { written: false, reason: "not_ok" };
  }
  if (response.status !== 200) return { written: false, reason: "not_ok" };
  const lastModified = Date.parse(response.headers.get("last-modified") ?? "");
  if (!Number.isFinite(lastModified)) return { written: false, reason: "no_last_modified" };
  let feed: unknown;
  try {
    feed = await response.json();
  } catch {
    return { written: false, reason: "not_json" };
  }
  const data = (feed as { data?: unknown } | null)?.data;
  if (!Array.isArray(data) || data.length === 0) return { written: false, reason: "no_data" };

  const nowMs = deps.now().getTime();
  const parsed = parseLcsFeed(data, Math.floor(nowMs / 1000));
  if (parsed.refused.length * 2 > parsed.full) return { written: false, reason: "too_many_refused" };
  const capped = capClosures(parsed.closures);
  const record: ClosuresRecord = {
    version: await closuresVersion(capped.geojson),
    fetched_at: new Date(Math.min(lastModified, nowMs)).toISOString(),
    geojson: capped.geojson,
    stats: { rows: parsed.rows, full: parsed.full, active: parsed.active, refused: parsed.refused.length,
      kept: capped.kept, dropped: capped.dropped },
  };
  await deps.kv.put(CLOSURES_KEY, JSON.stringify(record));
  return { written: true, record };
}
