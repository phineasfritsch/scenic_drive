/**
 * T-0318 through worker.fetch (src/index.ts's default export): the trip_places read runs AFTER the quota reservation
 * and reads only the route's box (R1-R5). The box oracle below is typed out from R3, never imported from src.
 */
import { liveClosures } from "./closuresFake";
import { env } from "cloudflare:test";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import placesSql from "../migrations/0001_places.sql?raw";
import tripPlacesSql from "../migrations/0009_trip_places.sql?raw";
import latIndexSql from "../migrations/0010_trip_places_lat.sql?raw";
import tripsRaw from "../../../Tests/Fixtures/t0268/trips.json?raw";
import worker, { type Env } from "../src/index";
import { planRoadTrip, type RoadTripPlace } from "../src/roadTrip";
import { fakeQuotaNamespace, type FakeQuota } from "./doFake";
import { BIG_SUR, NOW, ROAD, TRIP_BODY, tripRouter } from "./tripHarness";

const DEVICE = "1f8b6d5e-1a2b-4c3d-8e9f-0123456789ab";
const EARTH_M = 6_371_008.8;
const PAD_M = 16_000;
const rad = (d: number) => (d * Math.PI) / 180;
const deg = (r: number) => (r * 180) / Math.PI;
type LL = { lat: number; lon: number };
type Box = { south: number; north: number; west: number; east: number };

/** R3 typed out: the vertices' extremes padded 16 km, outward on the 0.1 degree grid, clamped / full width. */
function oracle(points: LL[]): Box {
  const lats = points.map((p) => p.lat), lons = points.map((p) => p.lon);
  const padDeg = deg(PAD_M / EARTH_M);
  const south = Math.max(-90, Math.floor((Math.min(...lats) - padDeg) * 10) / 10);
  const north = Math.min(90, Math.ceil((Math.max(...lats) + padDeg) * 10) / 10);
  const ratio = Math.sin(PAD_M / EARTH_M / 2) / Math.cos(rad(Math.max(-south, north)));
  if (!(ratio < 1)) return { south, north, west: -180, east: 180 };
  const lonPad = deg(2 * Math.asin(ratio));
  const west = Math.floor((Math.min(...lons) - lonPad) * 10) / 10;
  const east = Math.ceil((Math.max(...lons) + lonPad) * 10) / 10;
  return west < -180 || east > 180 ? { south, north, west: -180, east: 180 } : { south, north, west, east };
}
const inBox = (b: Box, p: LL) => p.lat >= b.south && p.lat <= b.north && p.lon >= b.west && p.lon <= b.east;
const QUERY = "SELECT name, kind, score, lat, lon FROM trip_places WHERE lat >= ?1 AND lat <= ?2 AND lon >= ?3 AND lon <= ?4";
const LOOKUP = { sql: "SELECT lat, lon FROM places WHERE id = ?1", binds: [BIG_SUR.id] };
const ROAD_LL = ROAD.map(([lon, lat]) => ({ lat, lon }));
const ROAD_BOX = oracle(ROAD_LL);

const F64 = new Float64Array(1);
const I64 = new BigInt64Array(F64.buffer);
/** The next double away from zero (out = true) or toward it. */
const step = (x: number, out: boolean) => { F64[0] = x; I64[0] = I64[0]! + (out ? 1n : -1n); return F64[0]!; };

let quota: FakeQuota;
type Read = { sql: string; binds: unknown[] | null; names?: string[]; rowsRead?: number };
let reads: Read[];

function recordingDb(): D1Database {
  const wrap = (statement: D1PreparedStatement, read: Read): D1PreparedStatement => new Proxy(statement, {
    get(target, key) {
      if (key === "bind") return (...args: unknown[]) => { read.binds = args; return wrap(target.bind(...args), read); };
      if (key === "all") {
        return async () => {
          const result = await target.all<{ name: string }>();
          read.names = result.results.map((r) => r.name).sort();
          read.rowsRead = result.meta.rows_read;
          return result;
        };
      }
      const value = Reflect.get(target, key, target) as unknown;
      return typeof value === "function" ? (value as (...a: unknown[]) => unknown).bind(target) : value;
    },
  });
  return {
    prepare(sql: string) {
      const read: Read = { sql, binds: null };
      reads.push(read);
      return wrap(env.DB.prepare(sql), read);
    },
  } as unknown as D1Database;
}

const shippedEnv = (): Env => ({ DB: recordingDb(), GIT_SHA: "test", BUILT_AT: "test", QUOTA: quota.ns,
  ROUTER_URL: "https://router.test", ROUTER_SECRET: "test-router-secret", CLOSURES: liveClosures() }) as unknown as Env;

async function send() {
  const req = new Request("https://scenic-api.test/trip", {
    method: "POST", headers: { "content-type": "application/json", "x-scenic-device": DEVICE }, body: JSON.stringify(TRIP_BODY),
  });
  const response = await worker.fetch(req, shippedEnv());
  return { status: response.status, json: (await response.json()) as Record<string, unknown> };
}

async function load(rows: { id: string; lat: number; lon: number }[]) {
  await env.DB.prepare("DELETE FROM trip_places").run();
  for (const r of rows) {
    await env.DB.prepare("INSERT INTO trip_places (id, name, kind, score, lat, lon) VALUES (?1, ?1, 'stop', 0, ?2, ?3)")
      .bind(r.id, r.lat, r.lon).run();
  }
}
const tripRead = () => reads.filter((r) => r.sql.includes("trip_places"));

beforeAll(async () => {
  await env.DB.prepare(placesSql).run();
  await env.DB.prepare(`INSERT OR REPLACE INTO places (id, lat, lon) VALUES ('${BIG_SUR.id}', ${BIG_SUR.lat}, ${BIG_SUR.lon})`).run();
});

beforeEach(async () => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  quota = fakeQuotaNamespace();
  reads = [];
  vi.stubGlobal("fetch", tripRouter().fetchImpl);
  await env.DB.prepare("DROP TABLE IF EXISTS trip_places").run();
  await env.DB.prepare(tripPlacesSql).run();
  await env.DB.prepare(latIndexSql).run();
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("the trip_places read follows the quota reservation and reads the route's box (T-0318)", () => {
  it("a quota-refused trip prepares no trip_places statement: its D1 statements are the destination lookup only (P-COST-01)", async () => {
    await load([{ id: "near", lat: ROAD_LL[3]!.lat, lon: ROAD_LL[3]!.lon }]);
    expect((await send()).status).toBe(200);
    reads = [];
    expect(await send()).toEqual({ status: 429, json: { error: "quota_exhausted", resets_at: "2026-10-06T00:00:00.000Z" } });
    expect(reads).toEqual([LOOKUP]);
  });

  it("a served trip's D1 statements are the destination lookup and ONE trip_places read bound to the route's box (P-PRIV-05)", async () => {
    await load([]);
    expect((await send()).status).toBe(200);
    expect(reads.map(({ sql, binds }) => ({ sql, binds }))).toEqual([LOOKUP,
      { sql: QUERY, binds: [ROAD_BOX.south, ROAD_BOX.north, ROAD_BOX.west, ROAD_BOX.east] }]);
    expect(tripRead()[0]!.binds!.every((b) => Number.isInteger(Math.round((b as number) * 10)) &&
      Math.round((b as number) * 10) / 10 === b)).toBe(true);
  });

  it("the route's box is 16 km past every vertex: a point 15 km due N/S/E/W of the extreme vertices is inside", () => {
    const d = 15_000 / EARTH_M;
    const north = ROAD_LL.reduce((a, p) => (p.lat > a.lat ? p : a)), south = ROAD_LL.reduce((a, p) => (p.lat < a.lat ? p : a));
    const east = ROAD_LL.reduce((a, p) => (p.lon > a.lon ? p : a)), west = ROAD_LL.reduce((a, p) => (p.lon < a.lon ? p : a));
    const dLon = (p: LL) => deg(2 * Math.asin(Math.sin(d / 2) / Math.cos(rad(p.lat))));
    const out = [{ lat: north.lat + deg(d), lon: north.lon }, { lat: south.lat - deg(d), lon: south.lon },
      { lat: east.lat, lon: east.lon + dLon(east) }, { lat: west.lat, lon: west.lon - dLon(west) }];
    expect(out.map((p) => inBox(ROAD_BOX, p))).toEqual([true, true, true, true]);
  });

  const centre = { lat: (ROAD_BOX.south + ROAD_BOX.north) / 2, lon: (ROAD_BOX.west + ROAD_BOX.east) / 2 };
  const edges = [
    ["south", (v: number) => ({ lat: v, lon: centre.lon }), ROAD_BOX.south, false],
    ["north", (v: number) => ({ lat: v, lon: centre.lon }), ROAD_BOX.north, true],
    ["west", (v: number) => ({ lat: centre.lat, lon: v }), ROAD_BOX.west, true],
    ["east", (v: number) => ({ lat: centre.lat, lon: v }), ROAD_BOX.east, false],
  ] as const;
  it("every box edge: a row exactly on it is read, the next double outside is not (whole set of rows read)", async () => {
    await load(edges.flatMap(([name, place, bound, away]) => [{ id: `on-${name}`, ...place(bound) },
      { id: `past-${name}`, ...place(step(bound, away)) }]));
    expect((await send()).status).toBe(200);
    expect(tripRead().map((r) => r.names)).toEqual([["on-east", "on-north", "on-south", "on-west"]]);
  });

  it("100 rows outside the box's latitude band cost no rows read with the lat index, and 100 without it", async () => {
    const near = ROAD_LL.slice(0, 5).map((p, i) => ({ id: `near-${i}`, ...p }));
    const far = Array.from({ length: 100 }, (_, i) => ({ id: `far-${i}`, lat: ROAD_BOX.south - 1 - i / 100, lon: centre.lon }));
    const rowsRead = async (rows: typeof near) => {
      await load(rows);
      quota = fakeQuotaNamespace();
      reads = [];
      expect((await send()).status).toBe(200);
      return tripRead()[0]!.rowsRead!;
    };
    const indexed = [await rowsRead(near), await rowsRead([...near, ...far])];
    await env.DB.prepare("DROP INDEX trip_places_lat").run();
    const base = await rowsRead(near);
    expect([indexed[1]! - indexed[0]!, (await rowsRead([...near, ...far])) - base]).toEqual([0, 100]);
  });
});

describe("placesBox over the shared fixtures and at every clamp (T-0318 R3)", () => {
  const box = async () => (await import("../src/tripPlacesBox")).placesBox;
  interface Trips { route: { start: [number, number]; end: [number, number]; seconds: number; meters: number }[]; places: { name: string; kind: "stop" | "lodging";
    score: number; coordinate: [number, number] }[]; cases: { days: number; max_drive_s: number; max_m: number; fastest_s: number }[];
    synthetic: (Trips["cases"][number] & { route: Trips["route"]; places: Trips["places"] })[] }
  const trips = JSON.parse(tripsRaw) as Trips;
  const ll = ([lat, lon]: [number, number]) => ({ lat, lon });

  it("every fixture case plans the same day plan from the box's places as from all places", async () => {
    const placesBox = await box();
    const runs = [...trips.cases.map((c) => ({ ...c, route: trips.route, places: trips.places })), ...trips.synthetic];
    const pairs = runs.map((c) => {
      const edges = c.route.map((e) => ({ start: ll(e.start), end: ll(e.end), seconds: e.seconds, meters: e.meters }));
      const places: RoadTripPlace[] = c.places.map((p) => ({ name: p.name, kind: p.kind, score: p.score, coordinate: ll(p.coordinate) }));
      const b = placesBox([edges[0]!.start, ...edges.map((e) => e.end)]);
      const limits = { days: c.days, maxDriveSeconds: c.max_drive_s, maxMeters: c.max_m };
      return [planRoadTrip(edges, places.filter((p) => inBox(b, p.coordinate)), c.fastest_s, limits),
        planRoadTrip(edges, places, c.fastest_s, limits)];
    });
    expect(pairs.map(([a]) => a)).toEqual(pairs.map(([, b]) => b));
  });

  const padDeg = deg(PAD_M / EARTH_M);
  const rows: [string, LL[], Partial<Box>][] = [
    ["the shipped road", ROAD_LL, {}],
    ["south lands exactly on -90 (kept, whole longitude)", [{ lat: -90 + padDeg + 0.05, lon: 10 }], { south: -90, west: -180, east: 180 }],
    ["south one grid step past -90 (clamped to -90)", [{ lat: -90 + padDeg - 0.05, lon: 10 }], { south: -90, west: -180, east: 180 }],
    ["north lands exactly on 90 (kept, whole longitude)", [{ lat: 90 - padDeg - 0.05, lon: 10 }], { north: 90, west: -180, east: 180 }],
    ["north one grid step past 90 (clamped to 90)", [{ lat: 90 - padDeg + 0.05, lon: 10 }], { north: 90, west: -180, east: 180 }],
    ["a band reaching 89.9 keeps a finite longitude range", [{ lat: 89.9 - padDeg - 0.05, lon: 10 }], { north: 89.9 }],
    ["west exactly -180 is kept", [{ lat: 0, lon: -180 + deg(2 * Math.asin(Math.sin(PAD_M / EARTH_M / 2) / Math.cos(rad(0.2)))) + 0.05 }], { west: -180 }],
    ["west one grid step past -180 is the whole range", [{ lat: 0, lon: -180 + deg(2 * Math.asin(Math.sin(PAD_M / EARTH_M / 2) / Math.cos(rad(0.2)))) - 0.05 }], { west: -180, east: 180 }],
    ["east exactly 180 is kept", [{ lat: 0, lon: 180 - deg(2 * Math.asin(Math.sin(PAD_M / EARTH_M / 2) / Math.cos(rad(0.2)))) - 0.05 }], { east: 180 }],
    ["east one grid step past 180 is the whole range", [{ lat: 0, lon: 180 - deg(2 * Math.asin(Math.sin(PAD_M / EARTH_M / 2) / Math.cos(rad(0.2)))) + 0.05 }], { west: -180, east: 180 }],
  ];
  /** The pad's exact edge per side: the last vertex whose padded extreme stays on a grid line, and the next double. */
  const flip = (f: (x: number) => boolean, lo: number, hi: number): [number, number] => {
    for (;;) { const mid = (lo + hi) / 2; if (mid === lo || mid === hi) return [lo, hi]; if (f(mid)) hi = mid; else lo = mid; }
  };
  const lat = (x: number) => [{ lat: x, lon: -118 }], lon = (x: number) => [{ lat: 35, lon: x }];
  const [s0, s1] = flip((x) => oracle(lat(x)).south >= 34, 34, 34.5);
  const [n0, n1] = flip((x) => oracle(lat(x)).north > 36, 35.5, 36);
  const [w0, w1] = flip((x) => oracle(lon(x)).west >= -118, -118, -117.5);
  const [e0, e1] = flip((x) => oracle(lon(x)).east > -118, -118.5, -118);
  rows.push(["south: the pad lands exactly on 34.0", lat(s1), { south: 34 }], ["south: the next double out is 33.9", lat(s0), { south: 33.9 }],
    ["north: the pad lands exactly on 36.0", lat(n0), { north: 36 }], ["north: the next double out is 36.1", lat(n1), { north: 36.1 }],
    ["west: the pad lands exactly on -118.0", lon(w1), { west: -118 }], ["west: the next double out is -118.1", lon(w0), { west: -118.1 }],
    ["east: the pad lands exactly on -118.0", lon(e0), { east: -118 }], ["east: the next double out is -117.9", lon(e1), { east: -117.9 }]);
  for (const [name, points, literal] of rows) {
    it(`placesBox: ${name} (whole box)`, async () => {
      const got = (await box())(points);
      expect(got).toEqual(oracle(points));
      expect(got).toMatchObject(literal);
    });
  }
  it("the clamp rows are not vacuous: the kept rows' east/west are finite, the past rows' are the whole range", () => {
    expect([oracle(rows[6]![1]).east < 180, oracle(rows[8]![1]).west > -180, oracle(rows[5]![1]).east < 180]).toEqual([true, true, true]);
    expect([Math.floor((rows[2]![1][0]!.lat - padDeg) * 10) / 10, Math.ceil((rows[4]![1][0]!.lat + padDeg) * 10) / 10]).toEqual([-90.1, 90.1]);
  });
});
