/**
 * The daily reach cache (T-0262 R6). Key = (start at 2 dp, the one-way minutes bucket L, the UTC day, the graph
 * version); only the buckets are stored. Production is the Workers Cache API (caches.default) - no resource to
 * create - each entry living until the next UTC midnight; the day in the key bounds it either way.
 */
import type { ReachBucket } from "./isochronePlanner";
import type { LatLon } from "./latLon";
import { dayKey, nextReset } from "./quota";

/** The graph version when GRAPH_VERSION is unset: nothing in the tree versions the graph yet (R6). */
export const UNVERSIONED_GRAPH = "unversioned";
const CACHE_ORIGIN = "https://reach-cache.invalid";

export interface ReachCache {
  get(key: string): Promise<ReachBucket[] | null>;
  put(key: string, buckets: ReachBucket[], now: Date): Promise<void>;
}

export function reachCacheKey(start: LatLon, limit: number, now: Date, graphVersion: string, closuresVersion: string): string {
  return `${start.lat.toFixed(2)},${start.lon.toFixed(2)}|${limit}|${dayKey(now)}|${graphVersion}|${closuresVersion}`;
}

/** Seconds from `now` to the next UTC midnight, at least 1. */
export function secondsToNextDay(now: Date): number {
  return Math.max(1, Math.ceil((Date.parse(nextReset(now)) - now.getTime()) / 1000));
}

export function cacheApiReachCache(cache: Cache): ReachCache {
  const url = (key: string) => `${CACHE_ORIGIN}/isochrone/${encodeURIComponent(key)}`;
  return {
    async get(key) {
      const hit = await cache.match(url(key));
      return hit ? ((await hit.json()) as ReachBucket[]) : null;
    },
    async put(key, buckets, now) {
      await cache.put(url(key), new Response(JSON.stringify(buckets), {
        headers: { "content-type": "application/json", "cache-control": `max-age=${secondsToNextDay(now)}` },
      }));
    },
  };
}
