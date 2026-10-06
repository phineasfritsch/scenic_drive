/**
 * The closures one driven request carries (T-0282 N3-N6): the record holds every active closure, a request's custom
 * model may carry at most MAX_CLOSURE_POLYGONS, so each request takes the ones nearest ITS OWN corridor.
 *
 *   corridor   the straight segment from -> to (a point when they are equal), on R4's literal plane.
 *   distance   squared metres to a polygon: 0 when `from` lies inside a ring or the corridor properly crosses an
 *              edge, else the least point-to-segment distance among the endpoints of each (corridor, edge) pair.
 *              + - * / only, so Tests/Fixtures/t0276/nearest.py recomputes it bit-identically.
 *   closure    a run of consecutive features sharing a string properties.lcs_index (the cron writes one on every
 *              feature); a feature without one stands alone. Its distance is the least over its polygons.
 *   selection  closures by distance, ties by stored position; kept is the LONGEST PREFIX whose polygons fit - the
 *              first that does not fit stops the fill - so no dropped closure is nearer than a kept one. The kept
 *              features go out in STORED order: a set that fits is sent unchanged.
 */
import { MAX_CLOSURE_POLYGONS, type ClosureCollection, type ClosurePolygon } from "./customModel";
import { METERS_PER_DEGREE_LAT, METERS_PER_DEGREE_LON } from "./lcsFeed";
import type { LatLon } from "./latLon";
import { pathCrossesRing } from "./closuresCrossing";

type P = readonly [number, number];
export type ClosuresFor = (from: LatLon, to: LatLon) => ClosureCollection | null;

export interface ClosurePicker {
  pick: ClosuresFor;
  /** The most closures any one pick left out. */
  dropped(): number;
  /** T-0286 C3-C5: hold a returned path to every stored closure; at most one re-request, `retry` null when capped. */
  returned: PathGuard;
  /** T-0286 C6: the closures the returned paths still cross, in stored order, by id. */
  crosses(): string[];
}

/** A re-request with the closures replaced: the path it returned, or null when it fails the route's own guards. */
export type Retry<T> = (closures: ClosureCollection | null) => Promise<T | null>;
export type PathGuard = <T>(value: T, coordinates: (value: T) => readonly (readonly number[])[], from: LatLon, to: LatLon,
  retry: Retry<T> | null) => Promise<T>;

const plane = (lon: number, lat: number): P => [lon * METERS_PER_DEGREE_LON, lat * METERS_PER_DEGREE_LAT];

function pointSegment2(p: P, a: P, b: P): number {
  const vx = b[0] - a[0];
  const vy = b[1] - a[1];
  const wx = p[0] - a[0];
  const wy = p[1] - a[1];
  const vv = vx * vx + vy * vy;
  let t = vv === 0 ? 0 : (wx * vx + wy * vy) / vv;
  t = t < 0 ? 0 : t > 1 ? 1 : t;
  const dx = a[0] + t * vx - p[0];
  const dy = a[1] + t * vy - p[1];
  return dx * dx + dy * dy;
}

const cross = (o: P, a: P, b: P) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
const opposite = (x: number, y: number) => (x > 0 && y < 0) || (x < 0 && y > 0);
const crosses = (a: P, b: P, c: P, d: P) => opposite(cross(c, d, a), cross(c, d, b)) && opposite(cross(a, b, c), cross(a, b, d));

function inside(p: P, ring: P[]): boolean {
  let hit = false;
  for (let i = 0; i + 1 < ring.length; i += 1) {
    const a = ring[i]!;
    const b = ring[i + 1]!;
    if ((a[1] > p[1]) !== (b[1] > p[1]) && p[0] < a[0] + ((p[1] - a[1]) * (b[0] - a[0])) / (b[1] - a[1])) hit = !hit;
  }
  return hit;
}

/** Squared planar metres from the corridor o -> d to one polygon's outer ring. */
export function polygonDistance2(o: P, d: P, feature: ClosurePolygon): number {
  const ring = feature.geometry.coordinates[0]!.map(([lon, lat]) => plane(lon!, lat!));
  if (inside(o, ring)) return 0;
  let best = Infinity;
  for (let i = 0; i + 1 < ring.length; i += 1) {
    const a = ring[i]!;
    const b = ring[i + 1]!;
    if (crosses(o, d, a, b)) return 0;
    best = Math.min(best, pointSegment2(o, a, b), pointSegment2(d, a, b), pointSegment2(a, o, d), pointSegment2(b, o, d));
  }
  return best;
}

interface Group { at: number; features: ClosurePolygon[]; distance: number }

function groups(features: ClosurePolygon[]): ClosurePolygon[][] {
  const out: ClosurePolygon[][] = [];
  let last: unknown = null;
  for (const feature of features) {
    const index = (feature.properties as { lcs_index?: unknown } | null | undefined)?.lcs_index;
    if (typeof index === "string" && index === last) out[out.length - 1]!.push(feature);
    else out.push([feature]);
    last = typeof index === "string" ? index : null;
  }
  return out;
}

/** N3's order: closures by squared distance to the corridor from -> to, ties by stored position. */
function rank(set: ClosureCollection, from: LatLon, to: LatLon): Group[] {
  const o = plane(from.lon, from.lat);
  const d = plane(to.lon, to.lat);
  const ranked: Group[] = groups(set.features).map((features, at) =>
    ({ at, features, distance: Math.min(...features.map((f) => polygonDistance2(o, d, f))) }));
  ranked.sort((x, y) => x.distance - y.distance || x.at - y.at);
  return ranked;
}

/** The closures nearest the corridor from -> to, at most MAX_CLOSURE_POLYGONS polygons, and how many were left out. */
export function nearestClosures(set: ClosureCollection | null, from: LatLon, to: LatLon): { closures: ClosureCollection | null; dropped: number } {
  if (set === null || set.features.length <= MAX_CLOSURE_POLYGONS) return { closures: set, dropped: 0 };
  const ranked = rank(set, from, to);
  const kept = new Set<number>();
  let used = 0;
  for (const group of ranked) {
    if (used + group.features.length > MAX_CLOSURE_POLYGONS) break;
    used += group.features.length;
    kept.add(group.at);
  }
  const features = ranked.filter((g) => kept.has(g.at)).sort((x, y) => x.at - y.at).flatMap((g) => g.features);
  return { closures: { type: "FeatureCollection", features }, dropped: ranked.length - kept.size };
}

/** One request's picker over the snapshot's set: every pick its own selection; dropped() the most any one left out. */
export function closurePicker(set: ClosureCollection | null): ClosurePicker {
  let most = 0;
  const all = set === null ? [] : groups(set.features);
  const ids = idsOf(all);
  const left = new Set<number>();
  const crossed = (path: readonly (readonly number[])[]) => new Set(all.flatMap((features, at) =>
    (features.some((f) => pathCrossesRing(path, f.geometry.coordinates[0]!)) ? [at] : [])));
  return {
    pick: (from, to) => {
      const picked = nearestClosures(set, from, to);
      most = Math.max(most, picked.dropped);
      return picked.closures;
    },
    dropped: () => most,
    returned: async (value, coordinates, from, to, retry) => {
      const first = crossed(coordinates(value));
      const sent = new Set(nearestClosures(set, from, to).closures?.features ?? []);
      // C4: re-request only when the swap carries a crossed closure the request did not send - never a futile one.
      const swap = first.size === 0 || retry === null ? null : swappedClosures(set!, from, to, first);
      if (swap === null || swap.closures.features.every((f) => sent.has(f))) {
        first.forEach((at) => left.add(at));
        return value;
      }
      most = Math.max(most, swap.dropped);
      const again = await retry!(swap.closures);
      const kept = again === null ? first : crossed(coordinates(again));
      kept.forEach((at) => left.add(at));
      return again === null ? value : again;
    },
    crosses: () => [...left].sort((a, b) => a - b).map((at) => ids[at]!),
  };
}

/** C2: a closure's id - its lcs_index, or "#<stored position of its first feature>" without one. */
function idsOf(all: ClosurePolygon[][]): string[] {
  let position = 0;
  return all.map((features) => {
    const index = (features[0]!.properties as { lcs_index?: unknown } | null | undefined)?.lcs_index;
    const id = typeof index === "string" ? index : `#${position}`;
    position += features.length;
    return id;
  });
}

/** C4: the crossed closures first (the longest ranked prefix that fits), then the nearest others in the room left. */
export function swappedClosures(set: ClosureCollection, from: LatLon, to: LatLon, crossed: ReadonlySet<number>):
  { closures: ClosureCollection; dropped: number } {
  const ranked = rank(set, from, to);
  const kept = new Set<number>();
  let room = MAX_CLOSURE_POLYGONS;
  for (const pass of [ranked.filter((g) => crossed.has(g.at)), ranked.filter((g) => !crossed.has(g.at))]) {
    for (const group of pass) {
      if (group.features.length > room) break;
      room -= group.features.length;
      kept.add(group.at);
    }
  }
  const features = groups(set.features).filter((_, at) => kept.has(at)).flat();
  return { closures: { type: "FeatureCollection", features }, dropped: ranked.length - kept.size };
}
