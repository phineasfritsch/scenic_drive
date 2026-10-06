/**
 * Does a returned path cross a closure polygon (T-0286 C1)? The path is the router's points.coordinates, [lon, lat];
 * the polygon is its OUTER ring (holes ignored: a path inside a hole counts - fail closed).
 *
 *   crosses   some path vertex lies inside the ring (crossing number), or some path segment and some ring edge
 *             meet as CLOSED segments - a proper crossing, a touch at a vertex, an endpoint on an edge, a collinear
 *             overlap, a one-point path on the boundary. Collinear on the edge's line but past its ends does not.
 *   plane     computed on raw degrees: T-0276 R4's plane (91961 lon, 110946 lat) is a positive diagonal scaling, and
 *             orientation signs and bounding-box order are invariant under it - the same predicate, one rounding fewer.
 */
type P = readonly number[];

const orient = (o: P, a: P, b: P) => (a[0]! - o[0]!) * (b[1]! - o[1]!) - (a[1]! - o[1]!) * (b[0]! - o[0]!);
const sign = (x: number) => (x > 0 ? 1 : x < 0 ? -1 : 0);
const within = (p: P, a: P, b: P) => Math.min(a[0]!, b[0]!) <= p[0]! && p[0]! <= Math.max(a[0]!, b[0]!)
  && Math.min(a[1]!, b[1]!) <= p[1]! && p[1]! <= Math.max(a[1]!, b[1]!);

/** The closed segments a-b and c-d share at least one point. */
export function segmentsMeet(a: P, b: P, c: P, d: P): boolean {
  const o1 = sign(orient(c, d, a));
  const o2 = sign(orient(c, d, b));
  const o3 = sign(orient(a, b, c));
  const o4 = sign(orient(a, b, d));
  if (o1 * o2 < 0 && o3 * o4 < 0) return true;
  return (o1 === 0 && within(a, c, d)) || (o2 === 0 && within(b, c, d))
    || (o3 === 0 && within(c, a, b)) || (o4 === 0 && within(d, a, b));
}

/** p strictly inside the closed ring by the crossing-number rule (the boundary is segmentsMeet's). */
export function insideRing(p: P, ring: readonly P[]): boolean {
  let hit = false;
  for (let i = 0; i + 1 < ring.length; i += 1) {
    const a = ring[i]!;
    const b = ring[i + 1]!;
    if ((a[1]! > p[1]!) !== (b[1]! > p[1]!) && p[0]! < a[0]! + ((p[1]! - a[1]!) * (b[0]! - a[0]!)) / (b[1]! - a[1]!)) hit = !hit;
  }
  return hit;
}

/** The path crosses the polygon whose outer ring is `ring`. */
export function pathCrossesRing(path: readonly P[], ring: readonly P[]): boolean {
  if (path.length === 0) return false;
  if (path.some((p) => insideRing(p, ring))) return true;
  const last = Math.max(1, path.length - 1);
  for (let s = 0; s < last; s += 1) {
    const a = path[s]!;
    const b = path[Math.min(s + 1, path.length - 1)]!;
    for (let i = 0; i + 1 < ring.length; i += 1) {
      if (segmentsMeet(a, b, ring[i]!, ring[i + 1]!)) return true;
    }
  }
  return false;
}
