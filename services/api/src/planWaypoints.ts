/**
 * The Apple Maps pins - a port of Sources/ScenicKit/Plan/PlanTable.swift's row cutting and
 * PlanWaypoints.decisionPoints.
 *
 * A row is a maximal stretch over which way id, road class and scenic score stay the same: the point list is
 * cut at every boundary any of those three details declares, and neighbours carrying the same three values are
 * merged. A pin goes where the route CHANGES ROAD, and with more changes than pins the changes onto the
 * LONGEST stretches are kept - then put back in route order. Origin and destination are never pins.
 */
import type { LatLon } from "./latLon";
import type { DetailRun, DetailValue, RoutePath } from "./routePath";

/** PlanWaypoints.maximum, and AppleMapsDirections.maxWaypoints. */
export const MAX_WAYPOINTS = 9;
/** Geo.earthRadiusMeters - the mean radius the Swift haversine uses. */
export const EARTH_RADIUS_METERS = 6_371_008.8;

export interface TableRow {
  wayId: number | null;
  highway: string | null;
  scenicScore: number | null;
  fromIndex: number;
  toIndex: number;
  meters: number;
}

const radians = (degrees: number) => (degrees * Math.PI) / 180;

/** Geo.distanceMeters over two [lon, lat] positions. */
export function haversineMeters(a: [number, number], b: [number, number]): number {
  const lat1 = radians(a[1]);
  const lat2 = radians(b[1]);
  const dLat = radians(b[1] - a[1]);
  const dLon = radians(b[0] - a[0]);
  const h = Math.sin(dLat / 2) * Math.sin(dLat / 2) + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
  return 2 * EARTH_RADIUS_METERS * Math.asin(Math.min(1, Math.sqrt(h)));
}

/** The run whose half-open [from, to) contains `index`: the first point of a run is the one that names it. */
function covering(runs: DetailRun[], index: number): DetailValue | undefined {
  for (const run of runs) if (run.from <= index && index < run.to) return run.value;
  return undefined;
}

const whole = (value: DetailValue | undefined) => (typeof value === "number" ? Math.trunc(value) : null);
const text = (value: DetailValue | undefined) =>
  typeof value === "string" ? value : typeof value === "number" ? String(value) : null;

export function tableRows(path: RoutePath): TableRow[] {
  const points = path.coordinates;
  if (points.length < 2) return [];
  const last = points.length - 1;
  const wayIds = path.details.osm_way_id ?? [];
  const highways = path.details.road_class ?? [];
  const scores = path.details.scenic_score ?? [];

  const cuts = new Set<number>([0, last]);
  for (const run of [...wayIds, ...highways, ...scores]) {
    cuts.add(Math.min(Math.max(run.from, 0), last));
    cuts.add(Math.min(Math.max(run.to, 0), last));
  }
  const bounds = [...cuts].sort((a, b) => a - b);

  const merged: TableRow[] = [];
  for (let index = 0; index < bounds.length - 1; index += 1) {
    const from = bounds[index]!;
    const to = bounds[index + 1]!;
    const wayId = whole(covering(wayIds, from));
    const highway = text(covering(highways, from));
    const scenicScore = whole(covering(scores, from));
    let meters = 0;
    for (let at = from; at < to; at += 1) meters += haversineMeters(points[at]!, points[at + 1]!);
    const previous = merged[merged.length - 1];
    if (previous && previous.wayId === wayId && previous.highway === highway && previous.scenicScore === scenicScore) {
      previous.toIndex = to;
      previous.meters += meters;
    } else {
      merged.push({ wayId, highway, scenicScore, fromIndex: from, toIndex: to, meters });
    }
  }
  return merged;
}

/** Up to `limit` decision points, in route order, as {lat, lon}. */
export function decisionPoints(path: RoutePath, limit = MAX_WAYPOINTS): LatLon[] {
  if (limit <= 0 || path.coordinates.length <= 2) return [];
  const last = path.coordinates.length - 1;
  const kept = tableRows(path)
    .slice(1)
    .filter((row) => row.fromIndex > 0 && row.fromIndex < last)
    .sort((a, b) => (a.meters === b.meters ? a.fromIndex - b.fromIndex : b.meters - a.meters))
    .slice(0, limit)
    .map((row) => row.fromIndex)
    .sort((a, b) => a - b);
  return kept.map((index) => ({ lat: path.coordinates[index]![1], lon: path.coordinates[index]![0] }));
}
