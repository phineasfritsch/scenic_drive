/**
 * T-0286 through the SHIPPED ROUTES: every path an answer returns is held to EVERY stored closure (C1-C3), not only
 * the <= 50 sent; a crossing of a closure the request did not send buys ONE re-request with the crossers swapped in
 * for the farthest sent (C4, C5), and a crossing that survives is named in closures_hazard.crosses (C6) - never silent.
 * The stored set is the T-0276 recorded D7 fixture (173 polygons, 163 closures); X is its single-polygon closure
 * FARTHEST from the route's corridor, so over 50 it is dropped. Rows are the cross product route x set (empty / X alone
 * / the fixture) x shape (clear, vertex, edge, inside, through - built from X's own ring) x router (honours: a request
 * whose areas carry X is answered with the clear path; ignores: always the shape), each expectation a function of
 * its row, held by full equality of the request count, every request's areas, the returned coordinates and the hazard.
 */
import { env } from "cloudflare:test";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import expectedRaw from "../../../Tests/Fixtures/t0276/expected.json?raw";
import placesSql from "../migrations/0001_places.sql?raw";
import { nearestClosures, polygonDistance2 } from "../src/closuresNearest";
import { buildCustomModel, type ClosureCollection } from "../src/customModel";
import { ROUTES, type Env } from "../src/index";
import { closuresAt, TEST_VERSION } from "./closuresFake";
import { fakeQuotaNamespace } from "./doFake";
import { LOOP_BODY, loopPath, outAndBack } from "./loopHarness";
import { mergeClosures } from "../src/closuresStore";
import { retracedAreas } from "../src/loopPlanner";
import { retraceScan } from "../src/retrace";
import { ROUTE_DETAILS } from "../src/scenicPlanner";
import { SANTA_MONICA_TOPANGA_BODY, syntheticPath } from "./planHarness";
import { BIG_SUR, FAST_EDGE_MS, ORIGIN, ROAD, TRIP_BODY, tripPath } from "./tripHarness";

const NOW = new Date("2026-10-05T12:00:00Z");
const DEVICE = "0f8b6d5e-1a2b-4c3d-8e9f-0123456789ab";
/** Measured on the fixture (T-0276, T-0282): 163 closures; each request carries <= 50 polygons. */
const STORED_CLOSURES = 163;
const PER_REQUEST = 50;

type Pt = { lat: number; lon: number };
type Pos = number[];
type Feature = { type: "Feature"; properties: { lcs_index: string }; geometry: { type: "Polygon"; coordinates: Pos[][] } };
const fc = (features: Feature[]) => ({ type: "FeatureCollection" as const, features });
const STORED = (JSON.parse(expectedRaw) as { cap: { geojson: { features: Feature[] } } }).cap.geojson.features;

export type Route = "/plan" | "/loop" | "/trip" | "/plan reroute";
export const ROUTE_NAMES: Route[] = ["/plan", "/loop", "/trip", "/plan reroute"];
/** T-0319: a reroute is /plan carrying a usable token - ROUTES["/plan"] runs with PLANS remembering REMEMBERED. */
const HANDLER: Record<Route, "/plan" | "/loop" | "/trip"> = { "/plan": "/plan", "/loop": "/loop", "/trip": "/trip", "/plan reroute": "/plan" };
const TOKEN = "0f1e2d3c-4b5a-4968-8776-655443322110"; const REMEMBERED = { device: DEVICE, place: "la:topanga", pins: [{ lat: 34.03, lon: -118.52 }, { lat: 34.05, lon: -118.56 }], lambda: 7.75 };
const plansKv = () => ({ get: async (k: string) => (k === `plan:${TOKEN}` ? JSON.stringify(REMEMBERED) : null), put: async () => {} });
const BODIES: Record<Route, unknown> = { "/plan": SANTA_MONICA_TOPANGA_BODY, "/loop": LOOP_BODY, "/trip": { ...TRIP_BODY, days: 1 },
  "/plan reroute": { ...SANTA_MONICA_TOPANGA_BODY, reroute: { token: TOKEN, first_pin: 0 } } };
const CORRIDOR: Record<Route, [Pt, Pt]> = {
  "/plan": [SANTA_MONICA_TOPANGA_BODY.origin, { lat: 34.0676, lon: -118.5957 }],
  "/plan reroute": [SANTA_MONICA_TOPANGA_BODY.origin, { lat: 34.0676, lon: -118.5957 }],
  "/loop": [LOOP_BODY.start, LOOP_BODY.start],
  "/trip": [ORIGIN, { lat: BIG_SUR.lat, lon: BIG_SUR.lon }],
};
/** Measured: the car_scenic requests an answer makes before any re-request (/plan's and /trip's lambda searches). */
const BASE: Record<Route, number> = { "/plan": 6, "/loop": 1, "/trip": 6, "/plan reroute": 1 };

// ---- X and the selections, recomputed here: R4's plane by literal, T-0282's bound selection, C4's swap by REMOVAL.
const plane = (p: Pos) => [p[0]! * 91961, p[1]! * 110946] as const;
const dist = (r: Route, f: Feature) => polygonDistance2(plane([CORRIDOR[r][0].lon, CORRIDOR[r][0].lat]),
  plane([CORRIDOR[r][1].lon, CORRIDOR[r][1].lat]), f);
const centre = (f: Feature) => half(f.geometry.coordinates[0]![0]!, f.geometry.coordinates[0]![2]!);
/** X stands alone: one polygon in its closure (single), and no other stored polygon within 0.01 degrees of its centre. */
const alone = (f: Feature) => STORED.every((g) => g === f || Math.abs(centre(g)[0]! - centre(f)[0]!) > 0.01
  || Math.abs(centre(g)[1]! - centre(f)[1]!) > 0.01);
const single = (f: Feature) => STORED.filter((g) => g.properties.lcs_index === f.properties.lcs_index).length === 1;
export const xOf = (r: Route) => STORED.filter((f) => single(f) && alone(f)).reduce((a, b) => (dist(r, b) > dist(r, a) ? b : a));
const sentOf = (r: Route) => nearestClosures(fc(STORED) as ClosureCollection, ...CORRIDOR[r]).closures!.features as Feature[];
const runsOf = (features: Feature[]) => features.reduce<Feature[][]>((out, f, i) =>
  (i > 0 && features[i - 1]!.properties.lcs_index === f.properties.lcs_index ? (out[out.length - 1]!.push(f), out) : [...out, [f]]), []);
/** C4 by removal: drop the farthest sent closure (ties: the later stored) until X fits; X in; stored order. */
export function swapOf(r: Route): Feature[] {
  const runs = runsOf(sentOf(r)).map((run) => ({ run, d: Math.min(...run.map((f) => dist(r, f))), at: STORED.indexOf(run[0]!) }))
    .sort((a, b) => b.d - a.d || b.at - a.at);
  while (runs.reduce((n, x) => n + x.run.length, 0) + 1 > PER_REQUEST) runs.shift();
  return [...runs.flatMap((x) => x.run), xOf(r)].sort((a, b) => STORED.indexOf(a) - STORED.indexOf(b));
}
export const areasOf = (features: Feature[]) => buildCustomModel(0, fc(features) as ClosureCollection).areas;

// ---- the shapes, from X's ring V0 (SW) V1 (SE) V2 (NE) V3 (NW): exact ring positions where the case turns on 0.
const add = (...ps: Pos[]) => [ps.reduce((s, p) => s + p[0]!, 0), ps.reduce((s, p) => s + p[1]!, 0)];
const sub = (a: Pos, b: Pos) => [a[0]! - b[0]!, a[1]! - b[1]!];
const half = (a: Pos, b: Pos) => [(a[0]! + b[0]!) / 2, (a[1]! + b[1]!) / 2];
export type Shape = "clear" | "vertex" | "edge" | "inside" | "through";
export const SHAPES: Shape[] = ["clear", "vertex", "edge", "inside", "through"];
export function shapeOf(x: Feature, shape: Shape): Pos[] {
  const [v0, v1, v2, v3] = x.geometry.coordinates[0]! as [Pos, Pos, Pos, Pos];
  const e1 = sub(v0, v1);
  const e2 = sub(v0, v3);
  const a = add(v0, e1, e1, e2);
  const b = add(v0, e1, e2, e2);
  const c = half(v0, v2);
  if (shape === "clear") return [a, b];
  if (shape === "vertex") return [a, v0, b];
  if (shape === "edge") return [a, v0, v1, add(v1, sub(v1, v0), sub(v1, v2))];
  if (shape === "inside") return [half(c, v0), half(c, v1), half(c, v2)];
  return [add(c, sub(half(v0, v1), c), sub(half(v0, v1), c)), add(c, sub(half(v2, v3), c), sub(half(v2, v3), c))];
}
/** A router answer over `coords`: per-edge time, distance and way runs, the time split evenly in whole ms. */
export function answer(coords: Pos[], totalMs: number): string {
  const n = coords.length - 1;
  const runs = (v: (i: number) => number) => Array.from({ length: n }, (_, i) => [i, i + 1, v(i)]);
  const edgeMs = totalMs / n;
  return JSON.stringify({ paths: [{ time: edgeMs * n, distance: 10_000 * n, points: { type: "LineString", coordinates: coords },
    details: { time: runs(() => edgeMs), distance: runs(() => 10_000), osm_way_id: runs((i) => 100 + i) } }] });
}
const SCENIC_MS: Record<Route, number> = { "/plan": 1_200_000, "/loop": 2_700_000, "/trip": 14_400_000, "/plan reroute": 1_200_000 };
const PLAN_CEILING_MS = 1_000_000 + SANTA_MONICA_TOPANGA_BODY.budget_minutes * 60_000; // the 1000 s fastest + the budget
const PLAN_PATHS = ROUTE_NAMES.filter((r) => HANDLER[r] === "/plan");

export type SetName = "empty" | "X alone" | "the fixture";
export const SETS: SetName[] = ["empty", "X alone", "the fixture"];
export type Router = "honours" | "ignores";
export const ROUTERS: Router[] = ["honours", "ignores"];
const setOf = (r: Route, s: SetName) => (s === "empty" ? [] : s === "X alone" ? [xOf(r)] : STORED);

export function expectedRow(r: Route, s: SetName, shape: Shape, router: Router) {
  const x = xOf(r);
  const first = s === "the fixture" ? sentOf(r) : setOf(r, s);
  const shown: Shape = router === "honours" && s === "X alone" ? "clear" : shape;
  const re = s === "the fixture" && shown !== "clear";
  const final: Shape = re && router === "honours" ? "clear" : shown;
  const crosses = s !== "empty" && final !== "clear" ? [x.properties.lcs_index] : [];
  const dropped = s !== "the fixture" ? 0
    : Math.max(STORED_CLOSURES - runsOf(first).length, re ? STORED_CLOSURES - runsOf(swapOf(r)).length : 0);
  const hazard = dropped === 0 && crosses.length === 0 ? undefined : { state: "fresh", version: TEST_VERSION, fetched_at: NOW.toISOString(),
    ...(dropped > 0 ? { dropped } : {}), ...(crosses.length > 0 ? { crosses } : {}) };
  const areas = [...Array<unknown>(BASE[r]).fill(areasOf(first)), ...(re ? [areasOf(swapOf(r))] : [])];
  return { status: 200, requests: areas.length, areas, coordinates: shapeOf(x, final), hazard };
}

let graph = 0;
let router: Router = "ignores";
let shape: Shape = "clear";
let script: string[] = [];
let sent: Record<string, unknown>[] = [];
/** When set, the answer to a request carrying X (only the re-request does, over the fixture). */
let reAnswer: ((r: Route, x: Feature) => string) | null = null;

beforeAll(async () => {
  await env.DB.prepare(placesSql).run();
  await env.DB.prepare("INSERT OR REPLACE INTO places (id, lat, lon) VALUES ('la:topanga', 34.0676, -118.5957), ('la:big-sur', 36.27, -121.81)").run();
});
beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  [sent, router, shape] = [[], "ignores", "clear"];
  script = [];
  reAnswer = null;
  vi.stubGlobal("fetch", async (_input: RequestInfo | URL, init?: RequestInit) => {
    const body = JSON.parse(String(init?.body)) as Record<string, unknown>;
    sent.push(body);
    if (body.profile === "car_fast") return new Response(JSON.stringify(body.points).includes("-121.81")
      ? tripPath(ROAD, FAST_EDGE_MS) : syntheticPath(1_000_000, [1, 2, 3]));
    const r: Route = body.algorithm === "round_trip" ? "/loop" : JSON.stringify(body.points).includes("-121.81") ? "/trip" : "/plan";
    const scripted = script.shift();
    if (scripted !== undefined) return new Response(scripted);
    const x = xOf(r);
    const carries = JSON.stringify((body.custom_model as { areas?: unknown }).areas ?? null).includes(JSON.stringify(x.geometry.coordinates));
    if (carries && reAnswer !== null) return new Response(reAnswer(r, x));
    return new Response(answer(shapeOf(x, router === "honours" && carries ? "clear" : shape), SCENIC_MS[r]));
  });
});
afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

let lastAnswer: Record<string, unknown> = {};
export async function drive(r: Route, set: Feature[], body: unknown = BODIES[r]) {
  graph += 1;
  const shipped = { DB: env.DB, GIT_SHA: "test", BUILT_AT: "test", QUOTA: fakeQuotaNamespace().ns, ROUTER_URL: "https://router.test",
    ROUTER_SECRET: "s", GRAPH_VERSION: `crossing-graph-${graph}`, CLOSURES: closuresAt(NOW, fc(set)).kv,
    ...(r === "/plan reroute" ? { PLANS: plansKv() } : {}) } as unknown as Env;
  const req = new Request(`https://scenic-api.test${r}`, { method: "POST",
    headers: { "content-type": "application/json", "x-scenic-device": DEVICE }, body: JSON.stringify(body) });
  const response = await ROUTES[HANDLER[r]]!(req, shipped, new URL(req.url));
  const json = (await response.json()) as { closures_hazard?: unknown; route?: { coordinates: unknown } };
  lastAnswer = json as Record<string, unknown>;
  const modelled = sent.filter((b) => b.custom_model !== undefined);
  return { status: response.status, requests: modelled.length, areas: modelled.map((b) => (b.custom_model as { areas?: unknown }).areas),
    coordinates: json.route?.coordinates, hazard: json.closures_hazard };
}

describe("every returned path is held to every stored closure; one re-request, then the hazard (T-0286, P-SAFE-08)", () => {
  for (const r of ROUTE_NAMES) {
    for (const s of SETS) {
      for (const sh of SHAPES) {
        for (const rt of ROUTERS) {
          it(`${r}, ${s}, ${sh} path, router ${rt}: requests, areas, the returned path and the hazard equal the row's`, async () => {
            router = rt;
            shape = sh;
            expect(await drive(r, setOf(r, s))).toEqual(expectedRow(r, s, sh, rt));
          });
        }
      }
    }
  }
});

describe("meta: no row ignores its variant (T-0286)", () => {
  const key = (r: Route, s: SetName, sh: Shape, rt: Router) => JSON.stringify(expectedRow(r, s, sh, rt));
  for (const r of ROUTE_NAMES) {
    it(`${r}: over every crossing shape and router, the three sets expect three different answers`, () => {
      for (const sh of SHAPES.slice(1)) for (const rt of ROUTERS) expect(new Set(SETS.map((s) => key(r, s, sh, rt))).size).toEqual(3);
    });
    it(`${r}: where the shape is returned, the five shapes expect five different answers; honoured, each crossing differs from clear`, () => {
      for (const s of SETS) expect(new Set(SHAPES.map((sh) => key(r, s, sh, "ignores"))).size).toEqual(5);
      for (const sh of SHAPES.slice(1)) expect(key(r, "the fixture", sh, "honours")).not.toEqual(key(r, "the fixture", "clear", "honours"));
    });
    it(`${r}: X is dropped by the first request, carried by the re-request, which still sends <= 50 polygons`, () => {
      const swap = swapOf(r);
      expect([sentOf(r).includes(xOf(r)), swap.includes(xOf(r)), swap.length <= PER_REQUEST, runsOf(sentOf(r)).length > 0]).toEqual([false, true, true, true]);
    });
  }
});

describe("the loop's cap: a re-request is the 2nd or 3rd attempt, never a 4th (C5, P-COST-04)", () => {
  const DIRTY_POINTS = outAndBack(4000);
  const DIRTY = loopPath(DIRTY_POINTS);
  const S = LOOP_BODY.start;
  const RETRACE = retracedAreas(retraceScan(DIRTY_POINTS.map(([lat, lon]) => ({ lat, lon })))!.retraced, S);
  const ROWS: [string, number][] = [["first attempt clean", 0], ["the reseed clean", 1], ["the retrace attempt clean", 2]];
  for (const [name, dirty] of ROWS) {
    const retries = dirty + 1 < 3;
    it(`/loop, ${name}, crossing the dropped X, router honours: ${retries ? "one re-request, the clear loop" : "no 4th request, crosses named"}`, async () => {
      router = "honours";
      shape = "through";
      script = Array<string>(dirty).fill(DIRTY);
      const r = await drive("/loop", STORED);
      const x = xOf("/loop");
      const sentSet = sentOf("/loop");
      const attempts = Array.from({ length: dirty + 1 }, (_, k) => (k < 2 ? areasOf(sentSet)
        : buildCustomModel(0, mergeClosures(fc(sentSet) as ClosureCollection, RETRACE)).areas));
      const dropped = Math.max(STORED_CLOSURES - runsOf(sentSet).length, retries ? STORED_CLOSURES - runsOf(swapOf("/loop")).length : 0);
      expect(r).toEqual({ status: 200, requests: dirty + 1 + (retries ? 1 : 0),
        areas: [...attempts, ...(retries ? [areasOf(swapOf("/loop"))] : [])], coordinates: shapeOf(x, retries ? "clear" : "through"),
        hazard: { state: "fresh", version: TEST_VERSION, fetched_at: NOW.toISOString(), dropped,
          ...(retries ? {} : { crosses: [x.properties.lcs_index] }) } });
    });
  }
});

describe("a re-requested path that fails its route's own guards is not shown; the original's crossing is named (C5)", () => {
  const ROWS: [string, Route, (r: Route, x: Feature) => string][] = [
    ...PLAN_PATHS.flatMap((p): [string, Route, (r: Route, x: Feature) => string][] => [
      [`${p}, the re-request over the ceiling`, p, (r, x) => answer(shapeOf(x, "clear"), 99_000_000)],
      [`${p}, the re-request one second over the ceiling`, p, (r, x) => answer(shapeOf(x, "clear"), PLAN_CEILING_MS + 1000)]]),
    ["/plan, the re-request on the fastest route's ways", "/plan", () => syntheticPath(1_200_000, [1, 2, 3])],
    ["/loop, the re-request retraced", "/loop", () => loopPath(outAndBack(4000))],
    ["/trip, the re-request over the trip's ceiling", "/trip", (r, x) => answer(shapeOf(x, "clear"), 99_000_000)],
  ];
  for (const [name, r, re] of ROWS) {
    it(`${name}: the crossing path is returned, crosses names X, one re-request made`, async () => {
      router = "honours";
      shape = "through";
      reAnswer = re;
      const got = await drive(r, STORED);
      const row = expectedRow(r, "the fixture", "through", "ignores");
      expect(got).toEqual(row);
    });
  }
});

describe("a re-request exactly at the ceiling is returned: the ceiling is inclusive (T-0319 rv1 B1)", () => {
  for (const p of PLAN_PATHS) {
    it(`${p}, the re-request exactly at the ceiling: the clear path is returned, one re-request made`, async () => {
      [router, shape, reAnswer] = ["honours", "through", (r, x) => answer(shapeOf(x, "clear"), PLAN_CEILING_MS)];
      expect(await drive(p, STORED)).toEqual(expectedRow(p, "the fixture", "through", "honours"));
    });
  }
});

describe("a reroute under a stored closure sends it on its first car_scenic request (T-0319 rv1 B2)", () => {
  it("/plan reroute, X alone, clear path: the whole upstream request list is the fastest, then the pins at the remembered lambda carrying X", async () => {
    await drive("/plan reroute", [xOf("/plan reroute")]);
    const body = (points: number[][], profile: string, model?: unknown) => ({ points, profile, points_encoded: false,
      instructions: false, "ch.disable": true, details: ROUTE_DETAILS, ...(model === undefined ? {} : { custom_model: model }) });
    const [[o, d], ll] = [CORRIDOR["/plan reroute"], (p: Pt) => [p.lon, p.lat]];
    expect(sent).toEqual([body([ll(o), ll(d)], "car_fast"), body([ll(o), ...REMEMBERED.pins.map(ll), ll(d)], "car_scenic",
      buildCustomModel(REMEMBERED.lambda, fc([xOf("/plan reroute")]) as ClosureCollection))]);
  });
});

describe("the re-request is the request that returned the path, its closures swapped and nothing else (C5)", () => {
  for (const r of ROUTE_NAMES) {
    it(`${r}, the fixture, through path, router honours: the re-request's whole body is the first request's at the answer's lambda, areas swapped`, async () => {
      router = "honours";
      shape = "through";
      await drive(r, STORED);
      const modelled = sent.filter((b) => b.custom_model !== undefined);
      const lambda = r === "/loop" ? 2 : (lastAnswer.lambda as number);
      expect(modelled.at(-1)).toEqual({ ...modelled[0]!, custom_model: buildCustomModel(lambda, fc(swapOf(r)) as ClosureCollection) });
    });
  }
  it("/trip preview, five days, crossing the dropped X: a preview makes no legs, so it reserves none - one re-request", async () => {
    router = "honours";
    shape = "through";
    expect(await drive("/trip", STORED, { ...TRIP_BODY, days: 5 })).toEqual(expectedRow("/trip", "the fixture", "through", "honours"));
  });
});
