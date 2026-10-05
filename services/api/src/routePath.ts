/**
 * One routed path, decoded from GraphHopper's `points_encoded=false` body - the port of
 * Sources/ScenicKit/Plan/RoutePath.swift, plus RouteDifference's Jaccard over OSM way ids.
 *
 * `paths[0]` with `time` in MILLISECONDS (an integer), `distance` in metres, `points` a GeoJSON LineString of
 * [lon, lat] pairs, `details` a map from encoded-value name to [from, to, value] runs. A body missing any of
 * them is refused by name, never partly decoded: a guessed `time` is an invented ETA on a screen.
 */

export type DetailValue = string | number | null;

export interface DetailRun {
  from: number;
  to: number;
  value: DetailValue;
}

export interface RoutePath {
  timeMs: number;
  distanceM: number;
  /** [lon, lat], GeoJSON order, as the router sent them. */
  coordinates: [number, number][];
  details: Record<string, DetailRun[]>;
}

export type RouteRefusal = "router_refused" | "malformed_response";

export class RouteError extends Error {
  readonly reason: RouteRefusal;

  constructor(reason: RouteRefusal, message: string) {
    super(message);
    this.reason = reason;
    this.name = "RouteError";
  }
}

/** RouteDifference.maximumOverlap: a scenic route may share less than this of its ways with the fastest. */
export const MAXIMUM_OVERLAP = 0.6;
export const WAY_ID_DETAIL = "osm_way_id";

const malformed = (message: string) => new RouteError("malformed_response", message);

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function position(raw: unknown): [number, number] {
  if (!Array.isArray(raw) || raw.length < 2 || typeof raw[0] !== "number" || typeof raw[1] !== "number") {
    throw malformed("a point is not a [lon, lat] pair");
  }
  return [raw[0], raw[1]];
}

function runs(raw: unknown): Record<string, DetailRun[]> {
  if (raw === undefined || raw === null) return {};
  if (!isRecord(raw)) throw malformed("paths[0].details is not a map of runs");
  const decoded: Record<string, DetailRun[]> = {};
  for (const [key, entries] of Object.entries(raw)) {
    if (!Array.isArray(entries)) throw malformed("paths[0].details is not a map of runs");
    decoded[key] = entries.map((entry) => {
      if (!Array.isArray(entry) || entry.length !== 3 || !Number.isInteger(entry[0]) || !Number.isInteger(entry[1])) {
        throw malformed(`a ${key} run is not [from, to, value]`);
      }
      const value = entry[2];
      return { from: entry[0], to: entry[1], value: typeof value === "string" || typeof value === "number" ? value : null };
    });
  }
  return decoded;
}

export function decodeRoutePath(text: string): RoutePath {
  let root: unknown;
  try {
    root = JSON.parse(text);
  } catch {
    throw malformed("the router's body is not JSON");
  }
  if (!isRecord(root)) throw malformed("the response body is not a JSON object");
  if (typeof root.message === "string" && root.paths === undefined) {
    throw new RouteError("router_refused", root.message);
  }
  const path = Array.isArray(root.paths) ? root.paths[0] : undefined;
  if (!isRecord(path)) throw malformed("the response carries no paths[0]");
  if (!Number.isInteger(path.time)) throw malformed("paths[0].time is not an integer count of milliseconds");
  if (typeof path.distance !== "number" || !Number.isFinite(path.distance)) {
    throw malformed("paths[0].distance is not a number of metres");
  }
  const points = path.points;
  if (!isRecord(points) || !Array.isArray(points.coordinates)) {
    throw malformed("paths[0].points is not a GeoJSON LineString - request points_encoded=false");
  }
  return {
    timeMs: path.time as number,
    distanceM: path.distance,
    coordinates: points.coordinates.map(position),
    details: runs(path.details),
  };
}

/** Seconds, which is what every duration in the planner is. */
export function durationSeconds(path: RoutePath): number {
  return path.timeMs / 1000;
}

/** RouteDifference.wayIds: the numeric osm_way_id values, truncated as Swift's Int(Double) truncates. */
export function wayIds(path: RoutePath): Set<number> {
  const ids = new Set<number>();
  for (const run of path.details[WAY_ID_DETAIL] ?? []) {
    if (typeof run.value === "number") ids.add(Math.trunc(run.value));
  }
  return ids;
}

/** Jaccard |A n B| / |A u B|; two empty sets score 1.0 - knowing nothing is not a difference. */
export function overlap(a: Set<number>, b: Set<number>): number {
  const union = new Set<number>([...a, ...b]);
  if (union.size === 0) return 1;
  let shared = 0;
  for (const id of a) if (b.has(id)) shared += 1;
  return shared / union.size;
}
