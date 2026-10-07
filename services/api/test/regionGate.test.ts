/**
 * T-0293 R2-R6, R13 (P-COST-01): every planning route refuses a coordinate outside the served region - the union of the
 * la and sfbay region.json bboxes - with 422 {error: "region_unsupported"}, before any quota touch and with zero router
 * requests, through the shipped worker.fetch. The bounds are TYPED OUT below and held equal to region.json, never read
 * from src. Every row is a function of the route: the route's reference body with only its coordinate replaced.
 */
import { env } from "cloudflare:test";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import worker, { type Env } from "../src/index";
import placesSql from "../migrations/0001_places.sql?raw";
import laRegion from "../../etl/regions/la/region.json";
import sfbayRegion from "../../etl/regions/sfbay/region.json";
import { fakeQuotaNamespace, type FakeQuota } from "./doFake";
import { REACH_BODY } from "./isochroneHarness";
import { LOOP_BODY } from "./loopHarness";
import { NOW, PLACES, SANTA_MONICA_TOPANGA_BODY } from "./planHarness";
import { BIG_SUR, TRIP_BODY } from "./tripHarness";

const DEVICE = "0f8b6d5e-1a2b-4c3d-8e9f-0123456789ab";
type Box = { min_lon: number; min_lat: number; max_lon: number; max_lat: number };
const BOXES: Record<"la" | "sfbay", Box> = {
  la: { min_lon: -119.0, min_lat: 33.7, max_lon: -117.85, max_lat: 34.45 },
  sfbay: { min_lon: -123.62, min_lat: 36.85, max_lon: -121.55, max_lat: 38.92 },
};
const GATED = ["/plan", "/loop", "/isochrone", "/trip"] as const;
type Route = (typeof GATED)[number];
const FIELD: Record<Route, "origin" | "start"> = { "/plan": "origin", "/loop": "start", "/isochrone": "start", "/trip": "origin" };
const REFERENCE: Record<Route, Record<string, unknown>> = {
  "/plan": SANTA_MONICA_TOPANGA_BODY, "/loop": LOOP_BODY, "/isochrone": REACH_BODY, "/trip": TRIP_BODY,
};
const at = (lat: number, lon: number) => (route: Route) => ({ ...REFERENCE[route], [FIELD[route]]: { lat, lon } });
const two = (x: number) => Number(x.toFixed(2));
/** The next double past x, away from zero when `up` has x's sign. */
function nextAfter(x: number, up: boolean): number {
  const view = new DataView(new ArrayBuffer(8));
  view.setFloat64(0, x);
  view.setBigUint64(0, view.getBigUint64(0) + ((x > 0) === up ? 1n : -1n));
  return view.getFloat64(0);
}

interface Row { name: string; lat: number; lon: number }
function rows(): { outside: Row[]; inside: Row[]; ulp: (Row & { axis: "lat" | "lon" })[] } {
  const outside: Row[] = [];
  const inside: Row[] = [];
  const ulp: (Row & { axis: "lat" | "lon" })[] = [];
  for (const [id, b] of Object.entries(BOXES)) {
    const midLat = two((b.min_lat + b.max_lat) / 2);
    const midLon = two((b.min_lon + b.max_lon) / 2);
    outside.push(
      { name: `${id} south edge - 0.01`, lat: two(b.min_lat - 0.01), lon: midLon },
      { name: `${id} north edge + 0.01`, lat: two(b.max_lat + 0.01), lon: midLon },
      { name: `${id} west edge - 0.01`, lat: midLat, lon: two(b.min_lon - 0.01) },
      { name: `${id} east edge + 0.01`, lat: midLat, lon: two(b.max_lon + 0.01) },
      { name: `${id} south-west corner, outside diagonally`, lat: two(b.min_lat - 0.01), lon: two(b.min_lon - 0.01) },
      { name: `${id} north-east corner, outside diagonally`, lat: two(b.max_lat + 0.01), lon: two(b.max_lon + 0.01) },
    );
    inside.push(
      { name: `${id} south edge exactly`, lat: b.min_lat, lon: midLon },
      { name: `${id} north edge exactly`, lat: b.max_lat, lon: midLon },
      { name: `${id} west edge exactly`, lat: midLat, lon: b.min_lon },
      { name: `${id} east edge exactly`, lat: midLat, lon: b.max_lon },
      { name: `${id} south-west corner exactly`, lat: b.min_lat, lon: b.min_lon },
      { name: `${id} north-west corner exactly`, lat: b.max_lat, lon: b.min_lon },
      { name: `${id} south-east corner exactly`, lat: b.min_lat, lon: b.max_lon },
      { name: `${id} north-east corner exactly`, lat: b.max_lat, lon: b.max_lon },
      { name: `${id} centre`, lat: midLat, lon: midLon },
    );
    ulp.push(
      { name: `${id} south edge, one ulp out`, axis: "lat", lat: nextAfter(b.min_lat, false), lon: midLon },
      { name: `${id} north edge, one ulp out`, axis: "lat", lat: nextAfter(b.max_lat, true), lon: midLon },
      { name: `${id} west edge, one ulp out`, axis: "lon", lat: midLat, lon: nextAfter(b.min_lon, false) },
      { name: `${id} east edge, one ulp out`, axis: "lon", lat: midLat, lon: nextAfter(b.max_lon, true) },
    );
  }
  outside.push(
    { name: "between the boxes (Paso Robles)", lat: 35.63, lon: -120.69 },
    { name: "la's longitudes at sfbay's latitudes", lat: 37.88, lon: -118.43 },
    { name: "sfbay's longitudes at la's latitudes", lat: 34.08, lon: -122.59 },
    { name: "New York", lat: 40.71, lon: -74.01 },
    { name: "null island", lat: 0, lon: 0 },
    { name: "the whitelist's own corner", lat: 90, lon: 180 },
  );
  return { outside, inside, ulp };
}

let quota: FakeQuota;
let routerRequests: string[];

beforeEach(async () => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  quota = fakeQuotaNamespace();
  routerRequests = [];
  vi.stubGlobal("fetch", async (input: RequestInfo | URL) => {
    routerRequests.push(String(input instanceof Request ? input.url : input));
    return new Response(JSON.stringify({ message: "the region gate test answers no router request" }), { status: 500 });
  });
  for (const statement of placesSql.split(";").map((s) => s.trim()).filter(Boolean)) await env.DB.prepare(statement).run();
  const topanga = PLACES["la:topanga"]!;
  await env.DB.prepare("INSERT OR REPLACE INTO places (id, lat, lon) VALUES ('la:topanga', ?1, ?2), (?3, ?4, ?5)")
    .bind(topanga.lat, topanga.lon, BIG_SUR.id, BIG_SUR.lat, BIG_SUR.lon).run();
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

const shippedEnv = () => ({
  DB: env.DB, GIT_SHA: "test", BUILT_AT: "test", QUOTA: quota.ns, ROUTER_URL: "https://router.test",
  ROUTER_SECRET: "test-router-secret", GRAPH_VERSION: `region-gate-${Math.random()}`,
}) as unknown as Env;

async function send(route: Route, body: unknown) {
  const req = new Request(`https://scenic-api.test${route}`, {
    method: "POST", headers: { "content-type": "application/json", "x-scenic-device": DEVICE }, body: JSON.stringify(body),
  });
  const response = await worker.fetch(req, shippedEnv());
  return { status: response.status, json: (await response.json()) as unknown };
}

describe("the served-region gate on every planning route (T-0293, P-COST-01)", () => {
  it("the gate's bounds are the la and sfbay region.json bboxes, typed out here", () => {
    expect({ la: laRegion.bbox, sfbay: sfbayRegion.bbox }).toEqual(BOXES);
  });

  it("every row is a function of the route: four distinct bodies, each the route's reference body with only its coordinate replaced", () => {
    const { outside, inside, ulp } = rows();
    expect(outside.length + inside.length + ulp.length).toBe(12 + 18 + 8 + 6);
    for (const row of [...outside, ...inside, ...ulp]) {
      const bodies = GATED.map((route) => at(row.lat, row.lon)(route));
      expect(new Set(bodies.map((b) => JSON.stringify(b))).size).toBe(GATED.length);
      GATED.forEach((route, i) => {
        const { [FIELD[route]]: coordinate, ...rest } = bodies[i]!;
        const { [FIELD[route]]: _reference, ...referenceRest } = REFERENCE[route];
        expect({ coordinate, rest }).toEqual({ coordinate: { lat: row.lat, lon: row.lon }, rest: referenceRest });
      });
    }
  });

  it("a coordinate just outside any edge or corner of either served box is 422 region_unsupported on every route, before any quota touch, with zero router requests", async () => {
    const { outside } = rows();
    const answered: [string, Route, unknown][] = [];
    for (const row of outside) {
      for (const route of GATED) {
        answered.push([row.name, route, await send(route, at(row.lat, row.lon)(route))]);
        expect(routerRequests).toEqual([]);
        expect(quota.state()).toEqual({});
      }
    }
    const refused = { status: 422, json: { error: "region_unsupported" } };
    expect(answered).toEqual(outside.flatMap((row) => GATED.map((route) => [row.name, route, refused])));
  });

  it("a coordinate on any exact edge or corner of either served box passes the gate on every route: the spent quota answers 429 whole, with zero router requests", async () => {
    const { inside } = rows();
    const answered: [string, Route, unknown][] = [];
    for (const row of inside) {
      for (const route of GATED) {
        quota.seed(`device:${DEVICE}`, "daily", { day: "2026-10-05", plan: 1000, loop: 1000, surprise: 1000, trip: 1000 });
        answered.push([row.name, route, await send(route, at(row.lat, row.lon)(route))]);
        expect(routerRequests).toEqual([]);
      }
    }
    const spent = { status: 429, json: { error: "quota_exhausted", resets_at: "2026-10-06T00:00:00.000Z" } };
    expect(answered).toEqual(inside.flatMap((row) => GATED.map((route) => [row.name, route, spent])));
  });

  it("a coordinate one ulp past an edge is the whitelist's 400, never the gate's 422: 0.01 is the gate's granularity", async () => {
    const { ulp } = rows();
    const answered: [string, Route, unknown][] = [];
    for (const row of ulp) for (const route of GATED) answered.push([row.name, route, await send(route, at(row.lat, row.lon)(route))]);
    expect(routerRequests).toEqual([]);
    expect(quota.state()).toEqual({});
    expect(answered).toEqual(ulp.flatMap((row) => GATED.map((route) => [row.name, route, { status: 400, json: {
      error: "invalid_request", detail: `${FIELD[route]}.${row.axis} has more than 2 decimals; round it on the device` } }])));
  });
});
