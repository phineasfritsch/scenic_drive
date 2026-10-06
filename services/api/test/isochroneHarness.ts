/**
 * The shipped /isochrone under test (T-0262): ROUTES["/isochrone"] with deps built from env over the QuotaCounter fake
 * and caches.default, and a recording GraphHopper standing in for the global fetch. Not a test file.
 *
 * The router's answer is RULED SYNTHETIC (R3: no recorded /isochrone answer exists): GraphHopper 11.0's shape exactly,
 * `{polygons: [Feature {properties: {bucket}, geometry: Polygon}], info}`, nested squares around the asked point, listed
 * in REVERSE bucket order so a reader trusting array order is wrong.
 */
import { liveClosures } from "./closuresFake";
import { env } from "cloudflare:test";
import { ROUTES, type Env } from "../src/index";
import type { FakeQuota } from "./doFake";

export const SECRET = "test-router-secret";
export const DEVICE = "0f8b6d5e-1a2b-4c3d-8e9f-0123456789ab";
export const NOW = new Date("2026-10-05T12:00:00Z");
export const START = { lat: 34.07, lon: -118.45 };
export const REACH_BODY = { start: START, minutes: 120 };

/** A closed square ring of half-side `half` degrees around (lat, lon), GeoJSON [lon, lat]. */
export function square(lat: number, lon: number, half: number): [number, number][] {
  return [[lon - half, lat - half], [lon + half, lat - half], [lon + half, lat + half], [lon - half, lat + half], [lon - half, lat - half]];
}

/** GraphHopper's answer to `point=<lat>,<lon>&buckets=<n>`: bucket i a square of half-side 0.05 * (i + 1). */
export function isochroneAnswer(lat: number, lon: number, count: number): unknown {
  const polygons = Array.from({ length: count }, (_, i) => ({
    type: "Feature", properties: { bucket: i },
    geometry: { type: "Polygon", coordinates: [square(lat, lon, 0.05 * (i + 1))] },
  })).reverse();
  return { polygons, info: { copyrights: ["GraphHopper", "OpenStreetMap contributors"], took: 7 } };
}

export interface IsochroneCall {
  url: string;
  method: string;
  headers: [string, string][];
}

/** Answers every /isochrone GET from its own query; `answer` overrides the body (or the whole Response). */
export function isochroneRouter(onFetch: () => void = () => {}, answer?: (url: URL) => unknown) {
  const calls: IsochroneCall[] = [];
  const fetchImpl = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
    onFetch();
    const url = new URL(String(input));
    calls.push({ url: String(input), method: init?.method ?? "GET", headers: [...new Headers(init?.headers)] });
    if (answer) {
      const body = answer(url);
      return body instanceof Response ? body : new Response(JSON.stringify(body));
    }
    const [lat, lon] = (url.searchParams.get("point") ?? "").split(",").map(Number);
    return new Response(JSON.stringify(isochroneAnswer(lat!, lon!, Number(url.searchParams.get("buckets")))));
  };
  return { calls, fetchImpl };
}

let version = 0;

/** A fresh graph version per call, so every test starts with an empty reach cache. */
export function freshGraph(): string {
  version += 1;
  return `test-graph-${version}`;
}

export function reachEnv(quota: FakeQuota, over: Record<string, unknown> = {}): Env {
  const e: Record<string, unknown> = {
    DB: env.DB, GIT_SHA: "test", BUILT_AT: "test", QUOTA: quota.ns, ROUTER_URL: "https://router.test",
    ROUTER_SECRET: SECRET, GRAPH_VERSION: freshGraph(), CLOSURES: liveClosures(), ...over,
  };
  for (const [key, value] of Object.entries(e)) if (value === undefined) delete e[key];
  return e as unknown as Env;
}

/** POST (or `method`) to the SHIPPED route: ROUTES["/isochrone"], deps from env. A GET carries no body. */
export async function reach(e: Env, body: unknown = REACH_BODY, device: string | null = DEVICE, method = "POST") {
  const headers: Record<string, string> = { "content-type": "application/json" };
  if (device !== null) headers["x-scenic-device"] = device;
  const req = new Request("https://scenic-api.test/isochrone", {
    method, headers, body: method === "GET" ? undefined : typeof body === "string" ? body : JSON.stringify(body),
  });
  const response = await ROUTES["/isochrone"]!(req, e, new URL(req.url));
  return { status: response.status, json: (await response.json()) as Record<string, unknown> };
}

/** The whole expected 200 body for `minutes` around START, recomputed from the synthetic answer (R7). */
export function expectedReach(minutes: number, buckets: number, center = START) {
  return {
    minutes,
    buckets: Array.from({ length: buckets }, (_, i) => ({
      minutes: 15 * (i + 1), round_trip_minutes: 30 * (i + 1),
      polygon: { type: "Polygon", coordinates: [square(center.lat, center.lon, 0.05 * (i + 1))] },
    })),
  };
}

export const wire = (lat: string, lon: string, seconds: number, buckets: number) =>
  `https://router.test/isochrone?point=${lat}%2C${lon}&profile=car_fast&time_limit=${seconds}&buckets=${buckets}&reverse_flow=false`;
