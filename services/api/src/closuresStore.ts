/**
 * The closures a request routes around, read from KV once per request (T-0276 R7, P-SAFE-08).
 *
 *   fresh        0 <= now - fetched_at <= CLOSURES_MAX_AGE_MS: the record's set, no hazard.
 *   stale        older, or fetched_at after now: the record's set - the LAST GOOD one - and a hazard.
 *   unavailable  no CLOSURES binding, a get that throws, no record, or a record that does not read (its version,
 *                its fetched_at, or a geojson buildCustomModel refuses): no closures, and a hazard.
 * Never a refusal to route, never silent: a 200 body carries closures_hazard whenever the state is not fresh.
 */
import { buildCustomModel, LAMBDA_MIN, MAX_CLOSURE_POLYGONS, type ClosureCollection } from "./customModel";

export const CLOSURES_KEY = "closures/lcs-d7";
export const CLOSURES_MAX_AGE_MS = 30 * 60 * 1000;
/** T-0282 N1: the record holds every active closure up to this many polygons; each request sends <= 50 of them. */
export const CLOSURES_STORED_MAX_POLYGONS = 2000;
/** The version of "no set": the cache key of an unavailable read. */
export const NO_CLOSURES_VERSION = "none";
export const CLOSURES_VERSION = /^lcs-d7-[0-9a-f]{16}$/;
const ISO_INSTANT = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z$/;

export interface ClosuresHazard {
  state: "fresh" | "stale" | "unavailable";
  version: string;
  fetched_at: string | null;
  /** T-0282 N6: the most closures one driven request of the answer did not carry; present only when > 0. */
  dropped?: number;
}

export interface ClosureSnapshot {
  version: string;
  closures: ClosureCollection | null;
  hazard: ClosuresHazard | null;
  fetchedAt: string | null;
}

const UNAVAILABLE: ClosureSnapshot = {
  version: NO_CLOSURES_VERSION,
  closures: null,
  hazard: { state: "unavailable", version: NO_CLOSURES_VERSION, fetched_at: null },
  fetchedAt: null,
};

function record(raw: string): { version: string; fetchedAt: string; ms: number; geojson: ClosureCollection } | null {
  let value: unknown;
  try {
    value = JSON.parse(raw);
  } catch {
    return null;
  }
  const r = value as { version?: unknown; fetched_at?: unknown; geojson?: unknown } | null;
  if (r === null || typeof r !== "object") return null;
  if (typeof r.version !== "string" || !CLOSURES_VERSION.test(r.version)) return null;
  if (typeof r.fetched_at !== "string" || !ISO_INSTANT.test(r.fetched_at)) return null;
  const ms = Date.parse(r.fetched_at);
  if (!Number.isFinite(ms)) return null;
  const g = r.geojson as { type?: unknown; features?: unknown } | null;
  if (g === null || typeof g !== "object" || g.type !== "FeatureCollection" || !Array.isArray(g.features)) return null;
  if (g.features.length > CLOSURES_STORED_MAX_POLYGONS) return null;
  try {
    for (let at = 0; at === 0 || at < g.features.length; at += MAX_CLOSURE_POLYGONS) {
      buildCustomModel(LAMBDA_MIN, { type: "FeatureCollection", features: g.features.slice(at, at + MAX_CLOSURE_POLYGONS) });
    }
  } catch {
    return null;
  }
  return { version: r.version, fetchedAt: r.fetched_at, ms, geojson: r.geojson as ClosureCollection };
}

export async function readClosures(kv: Pick<KVNamespace, "get"> | undefined, nowMs: number): Promise<ClosureSnapshot> {
  if (!kv) return UNAVAILABLE;
  let raw: string | null;
  try {
    raw = await kv.get(CLOSURES_KEY);
  } catch {
    return UNAVAILABLE;
  }
  const r = raw === null ? null : record(raw);
  if (r === null) return UNAVAILABLE;
  const age = nowMs - r.ms;
  const fresh = age >= 0 && age <= CLOSURES_MAX_AGE_MS;
  return {
    version: r.version,
    closures: r.geojson,
    hazard: fresh ? null : { state: "stale", version: r.version, fetched_at: r.fetchedAt },
    fetchedAt: r.fetchedAt,
  };
}

/** The 200 body, with closures_hazard when the snapshot is not fresh (R7) or a driven request left closures out (N6). */
export function withClosuresHazard<T extends object>(answer: T, snapshot: ClosureSnapshot,
  dropped = 0): T | (T & { closures_hazard: ClosuresHazard }) {
  if (dropped === 0) return snapshot.hazard === null ? answer : { ...answer, closures_hazard: snapshot.hazard };
  const hazard = snapshot.hazard ?? { state: "fresh" as const, version: snapshot.version, fetched_at: snapshot.fetchedAt };
  return { ...answer, closures_hazard: { ...hazard, dropped } };
}

/** The feed's polygons first, then `extra` (a loop's retrace squares), at most MAX_CLOSURE_POLYGONS (R8). */
export function mergeClosures(feed: ClosureCollection | null, extra: ClosureCollection | null): ClosureCollection | null {
  const features = [...(feed?.features ?? []), ...(extra?.features ?? [])].slice(0, MAX_CLOSURE_POLYGONS);
  return features.length === 0 ? null : { type: "FeatureCollection", features };
}
