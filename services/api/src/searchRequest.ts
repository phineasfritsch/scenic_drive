/**
 * POST /search's body whitelist and the ONE Photon request it becomes (T-0359 R3, R4; P-PRIV-05).
 *
 * The body is exactly {q} or {q, near: {lat, lon}}: the typed text and, at most, one bias coordinate already at two
 * decimals - the device rounds it (CLAUDE.md: never more than one coordinate per action, never more than 2 dp). The
 * Photon request carries that text, the fixed California bbox (CALIFORNIA, a constant, not the user's) and the bias
 * only when one was sent. Nothing else about the caller is forwarded.
 */
import type { LatLon } from "./latLon";
import { atMostTwoDecimals, ORIGIN_DECIMALS } from "./planRequest";

/** The longest query accepted, in UTF-16 code units (JavaScript's String length). */
export const SEARCH_MAX_QUERY = 100;
/** The most results asked of Photon and the most /search ever answers. */
export const SEARCH_LIMIT = 8;
/** The one language asked of Photon (`lang`); the US db carries English names. */
export const SEARCH_LANG = "en";
/** California's extent (T-0359 R2): no California Photon extract exists, so the US db is searched inside this box. */
export const CALIFORNIA = { min_lon: -124.48, min_lat: 32.53, max_lon: -114.13, max_lat: 42.01 } as const;
/** minLon,minLat,maxLon,maxLat - Photon's bbox order (docs/api-v1.md@1.3.0). */
export const SEARCH_BBOX = [CALIFORNIA.min_lon, CALIFORNIA.min_lat, CALIFORNIA.max_lon, CALIFORNIA.max_lat].join(",");

export interface SearchRequest {
  q: string;
  near: LatLon | null;
}

export type SearchParse = { ok: true; request: SearchRequest } | { ok: false; problem: string };

const BODY_KEYS = ["q", "near"];
const NEAR_KEYS = ["lat", "lon"];
// C0 controls and DEL: nothing a person types into a search field, and everything a log line should never hold.
const CONTROL = /[\u0000-\u001f\u007f]/;

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function extraKey(value: Record<string, unknown>, allowed: string[]): string | undefined {
  return Object.keys(value).find((k) => !allowed.includes(k));
}

function queryProblem(q: unknown): string | null {
  if (typeof q !== "string") return "q is not a string";
  if (q.length < 1 || q.length > SEARCH_MAX_QUERY) return `q is not 1 to ${SEARCH_MAX_QUERY} characters`;
  if (q.trim().length === 0) return "q is only whitespace";
  if (CONTROL.test(q)) return "q holds a control character";
  return null;
}

function axisProblem(value: unknown, name: string, limit: number): string | null {
  if (typeof value !== "number" || !Number.isFinite(value)) return `near.${name} is not a finite number`;
  if (value < -limit || value > limit) return `near.${name} is outside [-${limit}, ${limit}]`;
  if (!atMostTwoDecimals(value)) return `near.${name} has more than ${ORIGIN_DECIMALS} decimals; round it on the device`;
  return null;
}

export function parseSearchRequest(raw: unknown): SearchParse {
  if (!isObject(raw)) return { ok: false, problem: "the body is not an object" };
  const extra = extraKey(raw, BODY_KEYS);
  if (extra !== undefined) return { ok: false, problem: `unknown key ${JSON.stringify(extra)}` };
  const q = queryProblem(raw.q);
  if (q !== null) return { ok: false, problem: q };
  if (!("near" in raw)) return { ok: true, request: { q: raw.q as string, near: null } };
  const near = raw.near;
  if (!isObject(near)) return { ok: false, problem: "near is not an object" };
  const nearExtra = extraKey(near, NEAR_KEYS);
  if (nearExtra !== undefined) return { ok: false, problem: `unknown key near.${JSON.stringify(nearExtra)}` };
  const problem = axisProblem(near.lat, "lat", 90) ?? axisProblem(near.lon, "lon", 180);
  if (problem !== null) return { ok: false, problem };
  return { ok: true, request: { q: raw.q as string, near: { lat: near.lat as number, lon: near.lon as number } } };
}

/** The one Photon request: `${base}/api?q&limit&lang&bbox[&lat&lon]`, in that key order (R4). */
export function photonUrl(base: string, request: SearchRequest): string {
  const params = new URLSearchParams();
  params.set("q", request.q);
  params.set("limit", String(SEARCH_LIMIT));
  params.set("lang", SEARCH_LANG);
  params.set("bbox", SEARCH_BBOX);
  if (request.near !== null) {
    params.set("lat", request.near.lat.toFixed(ORIGIN_DECIMALS));
    params.set("lon", request.near.lon.toFixed(ORIGIN_DECIMALS));
  }
  return `${base}/api?${params.toString()}`;
}
