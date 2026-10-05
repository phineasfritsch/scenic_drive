/**
 * The Apple Maps handoff URL - a port of Sources/Handoff/AppleMapsDirections.swift (T-0248 R7).
 *
 * `https://maps.apple.com/directions?source=..&destination=..&waypoint=..(repeated, in route order)&mode=driving`.
 * Coordinates at 5 decimals built by INTEGER arithmetic, rounding half away from zero as Swift's `rounded()`
 * does (Math.round rounds -0.5 to -0, which would spell a different coordinate than ops/plan prints). Five
 * decimals here is not the two-decimal rule: this URL is the user handing their own route to Apple.
 */
import type { LatLon } from "./latLon";
import { MAX_WAYPOINTS } from "./planWaypoints";

export const COORDINATE_DECIMALS = 5;

export class HandoffError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "HandoffError";
  }
}

function decimal(value: number): string {
  let scale = 1;
  for (let i = 0; i < COORDINATE_DECIMALS; i += 1) scale *= 10;
  const product = value * scale;
  const scaled = Math.sign(product) * Math.round(Math.abs(product));
  const negative = scaled < 0;
  const magnitude = Math.abs(scaled);
  const whole = Math.floor(magnitude / scale);
  let digits = String(magnitude % scale);
  while (digits.length < COORDINATE_DECIMALS) digits = `0${digits}`;
  return `${negative ? "-" : ""}${whole}.${digits}`;
}

/** `lat,lon` at 5 decimals, or a refusal for anything that is not a position. */
export function coordinateText(c: LatLon): string {
  if (!Number.isFinite(c.lat) || !Number.isFinite(c.lon) || c.lat < -90 || c.lat > 90 || c.lon < -180 || c.lon > 180) {
    throw new HandoffError(`not a coordinate: ${c.lat},${c.lon}`);
  }
  return `${decimal(c.lat)},${decimal(c.lon)}`;
}

export function appleMapsUrl(source: LatLon, destination: LatLon, waypoints: LatLon[]): string {
  if (waypoints.length > MAX_WAYPOINTS) {
    throw new HandoffError(`${waypoints.length} waypoints is more than the ${MAX_WAYPOINTS} a handoff carries`);
  }
  const items = [`source=${coordinateText(source)}`, `destination=${coordinateText(destination)}`];
  for (const waypoint of waypoints) items.push(`waypoint=${coordinateText(waypoint)}`);
  items.push("mode=driving");
  return `https://maps.apple.com/directions?${items.join("&")}`;
}
