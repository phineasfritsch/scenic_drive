/**
 * Photon's GeoJSON answer -> /search's {results: [{label, lat, lon}]} (T-0359 R6), FAIL-CLOSED: one feature that is not
 * a Point at a finite in-range [lon, lat] with a property bag that yields a non-empty label refuses the WHOLE answer
 * (null), because a half-read answer shown as a full one is a wrong destination offered to a driver.
 */
import { SEARCH_LIMIT } from "./searchRequest";

export interface SearchResult {
  label: string;
  lat: number;
  lon: number;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** A non-empty trimmed string property, or null. */
function part(properties: Record<string, unknown>, key: string): string | null {
  const value = properties[key];
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

/** [name, "housenumber street" (or street), city, state]; a part equal to the one before it is dropped; ", ". */
export function searchLabel(properties: Record<string, unknown>): string {
  const street = part(properties, "street");
  const number = part(properties, "housenumber");
  const road = street === null ? null : number === null ? street : `${number} ${street}`;
  const parts: string[] = [];
  for (const piece of [part(properties, "name"), road, part(properties, "city"), part(properties, "state")]) {
    if (piece !== null && piece !== parts[parts.length - 1]) parts.push(piece);
  }
  return parts.join(", ");
}

function inRange(value: unknown, limit: number): value is number {
  return typeof value === "number" && Number.isFinite(value) && value >= -limit && value <= limit;
}

function result(feature: unknown): SearchResult | null {
  if (!isObject(feature) || !isObject(feature.geometry) || !isObject(feature.properties)) return null;
  const { geometry } = feature;
  if (geometry.type !== "Point" || !Array.isArray(geometry.coordinates) || geometry.coordinates.length !== 2) return null;
  const [lon, lat] = geometry.coordinates as unknown[];
  if (!inRange(lat, 90) || !inRange(lon, 180)) return null;
  const label = searchLabel(feature.properties);
  return label.length > 0 ? { label, lat, lon } : null;
}

/** The results of a Photon answer body, at most SEARCH_LIMIT of them, or null when any of it cannot be read. */
export function readPhotonAnswer(body: unknown): SearchResult[] | null {
  if (!isObject(body) || !Array.isArray(body.features)) return null;
  const results: SearchResult[] = [];
  for (const feature of body.features) {
    const read = result(feature);
    if (read === null) return null;
    results.push(read);
  }
  return results.slice(0, SEARCH_LIMIT);
}
