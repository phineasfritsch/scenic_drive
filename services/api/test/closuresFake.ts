/**
 * T-0276: a CLOSURES KV for the tests - a table of values, every get and put recorded, or a get that throws - and
 * the record the cron writes. EMPTY_CLOSURES is the fresh set of no polygons: buildCustomModel(l, EMPTY_CLOSURES)
 * is buildCustomModel(l, null), so the routes' earlier tests keep their bodies with a fresh binding.
 */
import { CLOSURES_KEY, type ClosureSnapshot } from "../src/closuresStore";
import type { ClosureCollection } from "../src/customModel";

export const TEST_VERSION = "lcs-d7-00000000000000aa";
export const EMPTY_CLOSURES: ClosureCollection = { type: "FeatureCollection", features: [] };
export const FRESH_EMPTY: ClosureSnapshot = { version: TEST_VERSION, closures: EMPTY_CLOSURES, hazard: null };

export interface ClosuresKv {
  kv: KVNamespace;
  gets: string[];
  puts: [string, string][];
}

export function closuresKv(values: Record<string, string>, fail = false): ClosuresKv {
  const gets: string[] = [];
  const puts: [string, string][] = [];
  const kv = {
    get: async (key: string) => {
      gets.push(key);
      if (fail) throw new Error("kv unavailable");
      return values[key] ?? null;
    },
    put: async (key: string, value: string) => {
      puts.push([key, value]);
    },
  } as unknown as KVNamespace;
  return { kv, gets, puts };
}

export function closuresRecord(fetchedAt: Date | string, geojson: unknown = EMPTY_CLOSURES, version = TEST_VERSION): string {
  const at = typeof fetchedAt === "string" ? fetchedAt : fetchedAt.toISOString();
  return JSON.stringify({ version, fetched_at: at, geojson, stats: {} });
}

/** A KV whose record is always fetched NOW (whatever the fake clock says): the fresh empty set. */
export function liveClosures(): KVNamespace {
  return { get: async (key: string) => (key === CLOSURES_KEY ? closuresRecord(new Date()) : null) } as unknown as KVNamespace;
}

/** A KV holding one record fetched at `fetchedAt`. */
export const closuresAt = (fetchedAt: Date | string, geojson: unknown = EMPTY_CLOSURES, version = TEST_VERSION) =>
  closuresKv({ [CLOSURES_KEY]: closuresRecord(fetchedAt, geojson, version) });

/** One square closure polygon of half-side `half` degrees around (lon, lat). */
export function squareClosure(lon: number, lat: number, half = 0.001) {
  const ring = [[lon - half, lat - half], [lon + half, lat - half], [lon + half, lat + half], [lon - half, lat + half],
    [lon - half, lat - half]];
  return { type: "Feature", properties: { lcs_index: `sq-${lon},${lat}` }, geometry: { type: "Polygon", coordinates: [ring] } };
}

export const TWO_CLOSURES = { type: "FeatureCollection", features: [squareClosure(-118.6, 34.05), squareClosure(-118.55, 34.1)] };
