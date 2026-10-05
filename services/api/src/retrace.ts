/**
 * How much of a loop is the same road driven twice, in opposite directions - a byte-faithful port of
 * Sources/ScenicKit/Loop/RetraceDetector.swift and the two Geo functions it calls (T-0252 R6).
 *
 * The parameters are the plan's: a 25 m radius measured by haversine, a 50 m index grid searched 3x3 to find
 * candidates, heading delta > 150 degrees, and a loop acceptable at retrace <= 0.15 (inclusive, as the Swift
 * rules). Same constants, same order of floating-point operations, so the shared fixture
 * (Tests/Fixtures/t0252/loops.json) holds the TS fraction and the Swift fraction to the same IEEE-754 bits.
 * Swift's `.rounded(.down)` is Math.floor, `.rounded(.up)` is Math.ceil, `truncatingRemainder` is `%`.
 *
 * One addition the Swift lacks: `retraceScan` also returns the retraced SAMPLES, which /loop's third attempt
 * turns into `areas`. The fraction is the same accumulator either way.
 */
import type { LatLon } from "./latLon";

export const EARTH_RADIUS_METERS = 6_371_008.8;
export const RETRACE_RADIUS_METERS = 25.0;
export const INDEX_CELL_METERS = 2 * RETRACE_RADIUS_METERS;
export const OPPOSITE_HEADING_DEGREES = 150.0;
export const MAX_RETRACE_FRACTION = 0.15;
export const SAMPLES_PER_CELL = 2.0;
export const METERS_PER_DEGREE_LATITUDE = 111_132.0;

const radians = (degrees: number) => (degrees * Math.PI) / 180;
const degrees = (radians: number) => (radians * 180) / Math.PI;

/** Geo.distanceMeters: haversine on EARTH_RADIUS_METERS. */
export function distanceMeters(a: LatLon, b: LatLon): number {
  const lat1 = radians(a.lat);
  const lat2 = radians(b.lat);
  const dLat = radians(b.lat - a.lat);
  const dLon = radians(b.lon - a.lon);
  const h = Math.sin(dLat / 2) * Math.sin(dLat / 2) + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
  return 2 * EARTH_RADIUS_METERS * Math.asin(Math.min(1, Math.sqrt(h)));
}

/** Geo.initialBearingDegrees, in [0, 360). */
export function initialBearingDegrees(a: LatLon, b: LatLon): number {
  const lat1 = radians(a.lat);
  const lat2 = radians(b.lat);
  const dLon = radians(b.lon - a.lon);
  const y = Math.sin(dLon) * Math.cos(lat2);
  const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLon);
  const deg = degrees(Math.atan2(y, x));
  return (deg + 360) % 360;
}

export function metersPerDegreeLongitude(latitude: number): number {
  return 111_320.0 * Math.cos((latitude * Math.PI) / 180);
}

/** The smaller angle between two compass headings, in 0...180 - the wrap-aware form. */
export function angularDifference(a: number, b: number): number {
  const d = Math.abs(a - b) % 360;
  return d > 180 ? 360 - d : d;
}

export function isAcceptable(fraction: number): boolean {
  return fraction <= MAX_RETRACE_FRACTION;
}

const NEIGHBOURHOOD: [number, number][] = [[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 0], [0, 1], [1, -1], [1, 0], [1, 1]];

interface Sample {
  point: LatLon;
  heading: number;
}

export interface RetraceScan {
  fraction: number;
  /** The samples that were counted as retrace, in route order. */
  retraced: LatLon[];
}

/** The fraction and the retraced samples, or null for a route with no length or a point that is not one. */
export function retraceScan(points: LatLon[]): RetraceScan | null {
  if (points.length < 2) return null;
  for (const p of points) if (!(Number.isFinite(p.lat) && Number.isFinite(p.lon))) return null;
  for (const p of points) if (!(p.lat >= -90 && p.lat <= 90) || !(p.lon >= -180 && p.lon <= 180)) return null;

  // The anchor and the longitude scale come from the BOUNDING BOX (RetraceDetector's order-independence).
  let minLat = points[0]!.lat;
  let maxLat = points[0]!.lat;
  let minLon = points[0]!.lon;
  for (const p of points) {
    if (p.lat < minLat) minLat = p.lat;
    if (p.lat > maxLat) maxLat = p.lat;
    if (p.lon < minLon) minLon = p.lon;
  }
  const mPerLon = metersPerDegreeLongitude((minLat + maxLat) / 2);
  if (!(mPerLon > 1)) return null;
  const anchor = { lat: minLat, lon: minLon };

  const byCell = new Map<string, Sample[]>();
  const key = (x: number, y: number) => `${x},${y}`;
  let total = 0.0;
  let retraced = 0.0;
  const retracedSamples: LatLon[] = [];

  for (let s = 0; s + 1 < points.length; s += 1) {
    const a = points[s]!;
    const b = points[s + 1]!;
    const length = distanceMeters(a, b);
    if (!(Number.isFinite(length) && length > 0)) continue;
    total += length;
    const heading = initialBearingDegrees(a, b);

    const steps = Math.max(1, Math.ceil(length / (RETRACE_RADIUS_METERS / SAMPLES_PER_CELL)));
    const share = length / steps;
    for (let i = 0; i < steps; i += 1) {
      const t = (i + 0.5) / steps;
      const here = { lat: a.lat + (b.lat - a.lat) * t, lon: a.lon + (b.lon - a.lon) * t };
      const x = Math.floor(((here.lon - anchor.lon) * mPerLon) / INDEX_CELL_METERS);
      const y = Math.floor(((here.lat - anchor.lat) * METERS_PER_DEGREE_LATITUDE) / INDEX_CELL_METERS);
      // The grid is an INDEX: the nine cells find candidates, the true distance decides.
      const hit = NEIGHBOURHOOD.some(([dx, dy]) => (byCell.get(key(x + dx, y + dy)) ?? []).some((seen) =>
        angularDifference(seen.heading, heading) > OPPOSITE_HEADING_DEGREES
        && distanceMeters(seen.point, here) <= RETRACE_RADIUS_METERS));
      if (hit) {
        retraced += share;
        retracedSamples.push(here);
      }
      const own = byCell.get(key(x, y));
      if (own) own.push({ point: here, heading });
      else byCell.set(key(x, y), [{ point: here, heading }]);
    }
  }

  if (!(total > 0)) return null;
  return { fraction: retraced / total, retraced: retracedSamples };
}

/** RetraceDetector.retraceFraction. */
export function retraceFraction(points: LatLon[]): number | null {
  return retraceScan(points)?.fraction ?? null;
}

/** RetraceDetector.isAcceptableLoop: false for a route with no fraction. */
export function isAcceptableLoop(points: LatLon[]): boolean {
  const f = retraceFraction(points);
  return f === null ? false : isAcceptable(f);
}
