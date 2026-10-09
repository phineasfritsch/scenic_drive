/**
 * T-0340 A1/A2: /trip and /loop answers carry the route's hazard runs, through the shipping handlers, compared WHOLE.
 *
 * The expected runs are written out here by hand (R1): a preview day reads the chosen route's runs clipped to the
 * day's point span, indexed into route.coordinates; a full day reads its own leg's runs, indexed into the leg.
 */
import { describe, expect, it } from "vitest";
import { FRESH_EMPTY, TEST_VERSION } from "./closuresFake";
import type { ClosureSnapshot } from "../src/closuresStore";
import { handleLoop } from "../src/loop";
import type { Tier } from "../src/quota";
import { ROUTE_DETAILS } from "../src/scenicPlanner";
import { handleTrip, type TripDeps } from "../src/trip";
import { BIG_SUR, EDGE_M, EDGES, expectedTrip, FAST_EDGE_MS, NOW, ROAD, ROUTER, SCENIC_EDGE_MS, TRIP_BODY, tripCounters, tripPath,
  tripRequest, tripRouter } from "./tripHarness";
import { LOOP_BODY, loopHarness, loopPath, loopRequest, NOW as LOOP_NOW, outAndBack, squareLoop, START } from "./loopHarness";

type Run = [number, number, string];
const TRIP_DETAILS_SENT = ["time", "distance", "scenic_score", "surface", "road_access"];

/** MIX over the 40-edge road (days 2 cut it at point 20): a first-edge and a last-edge run, a run across the night,
 *  runs ending and starting exactly at the night, an upper-cased value, and whitelisted asphalt / yes / missing. */
const SURFACE: Run[] = [[0, 1, "gravel"], [1, 15, "asphalt"], [15, 25, "COMPACTED"], [25, 39, "missing"], [39, 40, "dirt"]];
const ACCESS: Run[] = [[0, 10, "yes"], [10, 12, "destination"], [12, 18, "missing"], [18, 20, "private"],
  [20, 22, "customers"], [22, 40, "yes"]];

const h = (kind: string, value: string, from: number, to: number) => ({ kind, value, from_index: from, to_index: to });

/** Preview: indices into route.coordinates. */
const PREVIEW_DAYS = [
  [h("surface", "gravel", 0, 1), h("surface", "compacted", 15, 20), h("road_access", "destination", 10, 12),
    h("road_access", "private", 18, 20)],
  [h("surface", "compacted", 20, 25), h("surface", "dirt", 39, 40), h("road_access", "customers", 20, 22)],
];
/** Full: each day's leg is its own path, indexed from its first point. */
const FULL_DAYS = [
  PREVIEW_DAYS[0]!,
  [h("surface", "compacted", 0, 5), h("surface", "dirt", 19, 20), h("road_access", "customers", 0, 2)],
];

const perEdge = (value: number | string) => Array.from({ length: EDGES }, (_, i) => [i, i + 1, value]);

/** The runs a router answer over road points [a, b] carries, re-indexed from a (the leg fake's own path). */
function slice(runs: Run[], a: number, b: number): Run[] {
  return runs.filter(([f, t]) => f < b && t > a).map(([f, t, v]) => [Math.max(f, a) - a, Math.min(t, b) - a, v]);
}

function tripHarness(tier: Tier, hazards: boolean) {
  const details = { time: perEdge(SCENIC_EDGE_MS), distance: perEdge(EDGE_M), scenic_score: perEdge(8),
    ...(hazards ? { surface: SURFACE, road_access: ACCESS } : {}) };
  const legDetails = (a: number, b: number) => (hazards ? { surface: slice(SURFACE, a, b), road_access: slice(ACCESS, a, b) } : {});
  const events: string[] = [];
  const { counters } = tripCounters(events);
  const router = tripRouter({ scenic: tripPath(ROAD, SCENIC_EDGE_MS, details), legDetails });
  const deps: TripDeps = {
    upstream: { counters, fetchImpl: router.fetchImpl, now: () => NOW, killed: () => false },
    routerBase: ROUTER,
    resolvePlace: async (id) => (id === BIG_SUR.id ? { lat: BIG_SUR.lat, lon: BIG_SUR.lon } : null),
    identify: () => ({ userId: "device-1", tier }),
    closures: async () => FRESH_EMPTY,
    tripPlaces: async () => {
      throw new Error("this harness has no trip_places table");
    },
  };
  const run = async () => {
    const response = await handleTrip(tripRequest({ ...TRIP_BODY, days: 2 }), {}, deps);
    return { status: response.status, json: (await response.json()) as Record<string, unknown> };
  };
  return { run, sent: router.sent };
}

describe("T-0340 /trip hazards (A1)", () => {
  it("every trip day carries its own hazard runs, whole", async () => {
    for (const full of [false, true]) {
      for (const hazards of [false, true]) {
        const t = tripHarness(full ? "paid" : "free", hazards);
        const days = hazards ? (full ? FULL_DAYS : PREVIEW_DAYS) : [[], []];
        const label = `full=${full} hazards=${hazards}`;
        expect({ label, ...(await t.run()) }).toEqual({ label, status: 200,
          json: expectedTrip({ days: 2, edgeMs: SCENIC_EDGE_MS, lambda: 7.75, full, hazards: days }) });
        expect({ label, details: t.sent.map((s) => s.body.details) })
          .toEqual({ label, details: t.sent.map(() => TRIP_DETAILS_SENT) });
        expect(t.sent.length).toBe(full ? 9 : 7);
      }
    }
  });
});

describe("T-0340 /loop hazards (A2)", () => {
  it("the loop carries its hazard runs, whole", async () => {
    const square = squareLoop();
    const coordinates = square.map(([lat, lon]) => [lon, lat]);
    const edges = square.length - 1;
    const runs = (value: number | string) => Array.from({ length: edges }, (_, i) => [i, i + 1, value]);
    const surface: Run[] = [[0, 5, "asphalt"], [5, 9, "Gravel"], [9, 30, "missing"], [30, edges, "sand"]];
    const access: Run[] = [[0, 40, "yes"], [40, 44, "destination"], [44, 50, "missing"], [50, edges, "NO"]];
    const expected = [[], [h("surface", "gravel", 5, 9), h("surface", "sand", 30, edges),
      h("road_access", "destination", 40, 44), h("road_access", "no", 50, edges)]];
    for (const [i, hazards] of [false, true].entries()) {
      const details = { osm_way_id: runs(1000), road_class: runs("tertiary"), scenic_score: runs(8),
        ...(hazards ? { surface, road_access: access } : {}) };
      const answer = JSON.stringify({ paths: [{ time: 2_700_000, distance: 4000,
        points: { type: "LineString", coordinates }, details }] });
      const l = loopHarness([answer]);
      const response = await handleLoop(loopRequest(LOOP_BODY), {}, l.deps);
      const json = (await response.json()) as Record<string, unknown>;
      expect({ hazards, status: response.status, got: json.hazards }).toEqual({ hazards, status: 200, got: expected[i] });
      expect(l.sent.map((s) => s.body.details)).toEqual([ROUTE_DETAILS]);
    }
  });
});

/** Attempt k's runs (k = 0, 1, 2) and, written out by hand, the hazards those runs read as - each attempt's differ. */
const ATTEMPT_RUNS: { surface: Run[]; access: Run[] }[] = [
  { surface: [[0, 3, "gravel"], [3, 9, "asphalt"]], access: [[20, 22, "private"]] },
  { surface: [[4, 6, "Dirt"]], access: [[30, 33, "destination"], [33, 40, "yes"]] },
  { surface: [[10, 14, "sand"], [14, 20, "missing"]], access: [[50, 51, "NO"]] },
];
const ATTEMPT_HAZARDS = [
  [h("surface", "gravel", 0, 3), h("road_access", "private", 20, 22)],
  [h("surface", "dirt", 4, 6), h("road_access", "destination", 30, 33)],
  [h("surface", "sand", 10, 14), h("road_access", "no", 50, 51)],
];
function withRuns(body: string, k: number): string {
  const parsed = JSON.parse(body) as { paths: { details: Record<string, unknown> }[] };
  parsed.paths[0]!.details = { ...parsed.paths[0]!.details, surface: ATTEMPT_RUNS[k]!.surface, road_access: ATTEMPT_RUNS[k]!.access };
  return JSON.stringify(parsed);
}

/** The closure re-request (loopHonest's T-0286 fixture): X on the square's east side, stored but not sent, so a pretty
 *  square buys ONE re-request at the same seed, answered with the square mirrored west - clear of X. */
const SQ = squareLoop();
const ring = (lon: number, lat: number, d: number) => [[[lon - d, lat - d], [lon + d, lat - d], [lon + d, lat + d], [lon - d, lat + d], [lon - d, lat - d]]];
const area = (name: string, lon: number, lat: number, d: number) =>
  ({ type: "Feature", properties: { lcs_index: name }, geometry: { type: "Polygon", coordinates: ring(lon, lat, d) } });
const CROSSED: ClosureSnapshot = { version: TEST_VERSION, fetchedAt: LOOP_NOW.toISOString(), hazard: null,
  closures: { type: "FeatureCollection", features: [...Array.from({ length: 50 }, (_, i) =>
    area(`s-${i + 1}`, START.lon, START.lat - 0.001 - i * 0.0001, 0.00004)), area("x", SQ[30]![1], SQ[30]![0], 0.0005)] } as never };
const WEST = SQ.map(([lat, lon]) => [lat, 2 * START.lon - lon] as [number, number]);
const DIRTY = outAndBack(2000);

/** Every planner path to a shipped loop: rows are functions of the attempts, `ships` the one whose route goes out. */
const SHIP_ROWS = [
  { name: "a retrace-dirty first attempt, re-seeded clean", answers: [loopPath(DIRTY), loopPath(SQ)], crossed: false, ships: 1 },
  { name: "two dull loops, the third re-rolled pretty", answers: [loopPath(SQ, 2_700_000, 2), loopPath(SQ, 2_700_000, 2), loopPath(SQ)],
    crossed: false, ships: 2 },
  { name: "two retrace-dirty loops, the retrace-square attempt clean", answers: [loopPath(DIRTY), loopPath(DIRTY), loopPath(SQ)],
    crossed: false, ships: 2 },
  { name: "a pretty loop over a closure, re-requested pretty", answers: [loopPath(SQ), loopPath(WEST)], crossed: true, ships: 1 },
  { name: "a pretty loop over a closure, re-requested dull - the first loop stays", answers: [loopPath(SQ), loopPath(WEST, 2_700_000, 2)],
    crossed: true, ships: 0 },
];

describe("T-0340 /loop hazards come from the SHIPPED attempt (A2)", () => {
  it.each(SHIP_ROWS)("$name: the 200's hazards are the shipped attempt's runs", async ({ answers, crossed, ships }) => {
    const bodies = answers.map(withRuns);
    const l = loopHarness(bodies);
    const response = await handleLoop(loopRequest(LOOP_BODY), {}, crossed ? { ...l.deps, closures: async () => CROSSED } : l.deps);
    const json = (await response.json()) as { route?: { coordinates: unknown }; hazards?: unknown; attempts?: unknown };
    const shipped = (JSON.parse(bodies[ships]!) as { paths: { points: { coordinates: unknown } }[] }).paths[0]!.points.coordinates;
    expect({ status: response.status, attempts: json.attempts, route: json.route?.coordinates, hazards: json.hazards })
      .toEqual({ status: 200, attempts: answers.length, route: shipped, hazards: ATTEMPT_HAZARDS[ships] });
  });

  it("meta: every row ships one attempt and could read another's - no row lets a wrong attempt's runs pass", () => {
    expect(SHIP_ROWS.map((r) => r.answers.length > 1 && r.answers.every((_, k) => k === r.ships
      || JSON.stringify(ATTEMPT_HAZARDS[k]) !== JSON.stringify(ATTEMPT_HAZARDS[r.ships])))).toEqual(SHIP_ROWS.map(() => true));
    expect(SHIP_ROWS.map((r) => r.ships)).toEqual([1, 2, 2, 1, 0]);
  });
});

/** /trip's closure re-requests (closuresCrossingTrip's fixture): 100 stored squares nearer every corridor than X, so X
 *  is dropped from the first request and a path over it buys ONE re-request carrying X. Preview: X on the search's
 *  detour (road vertex 20 moved 0.3 degrees north-east); full: X on the day-2 leg's detour (via vertex 36 + 0.3). */
type Answer = "crossing" | "reRequest" | "refused";
const ne = (i: number): [number, number] => [ROAD[i]![0] + 0.3, ROAD[i]![1] + 0.3];
const DETOUR = ROAD.map((p, i) => (i === 20 ? ne(20) : p));
const NEAR = [0, 36].flatMap((v) => Array.from({ length: 50 }, (_, i) =>
  area(`n${v}-${i + 1}`, ROAD[v]![0], ROAD[v]![1] - 0.01 - (i + 1) * 0.002, 0.0005)));
const X_ROUTE = area("x", (ROAD[19]![0] + ne(20)[0]) / 2, (ROAD[19]![1] + ne(20)[1]) / 2, 0.0005);
const X_LEG = area("x", ne(36)[0], ne(36)[1], 0.0005);
const carries = (body: Record<string, unknown>, x: typeof X_LEG) =>
  JSON.stringify((body.custom_model as { areas?: unknown } | undefined)?.areas ?? null).includes(JSON.stringify(x.geometry.coordinates));

/** Each answer's runs and, by hand, what it reads as: preview per day (clipped at the night - road vertex 20, which is
 *  point 20 of the crossing route, 40 of the re-request cut in two, 60 of the refused one cut in three) or a day-2 leg.
 *  rv2-t0340: every re-request tiles its runs differently from the crossing answer, so the vertex->point map read
 *  from a pre-swap path puts the night at the wrong point. */
const ROUTE_RUNS: Record<Answer, { surface: Run[]; access: Run[]; days: unknown[][] }> = {
  crossing: { surface: [[5, 8, "gravel"]], access: [[30, 32, "PRIVATE"]],
    days: [[h("surface", "gravel", 5, 8)], [h("road_access", "private", 30, 32)]] },
  reRequest: { surface: [[24, 52, "Dirt"], [52, 80, "asphalt"]], access: [[4, 8, "destination"]],
    days: [[h("surface", "dirt", 24, 40), h("road_access", "destination", 4, 8)], [h("surface", "dirt", 40, 52)]] },
  refused: { surface: [[57, 66, "sand"]], access: [], days: [[h("surface", "sand", 57, 60)], [h("surface", "sand", 60, 66)]] },
};
const LEG1 = { surface: [[0, 1, "Gravel"]] as Run[], access: [] as Run[], hazards: [h("surface", "gravel", 0, 1)] };
const LEG2_RUNS: Record<Answer, { surface: Run[]; access: Run[]; hazards: unknown[] }> = {
  crossing: { surface: [], access: [[1, 2, "no"]], hazards: [h("road_access", "no", 1, 2)] },
  reRequest: { surface: [[1, 3, "compacted"]], access: [[0, 1, "customers"]],
    hazards: [h("surface", "compacted", 1, 3), h("road_access", "customers", 0, 1)] },
  refused: { surface: [[1, 3, "ground"]], access: [], hazards: [h("surface", "ground", 1, 3)] },
};
/** `points` with every segment cut into `k` (the k - 1 new points evenly inside it, the old points kept exactly). */
const cut = (points: [number, number][], k: number): [number, number][] => points.flatMap((p, i) => i === 0 ? [p]
  : Array.from({ length: k }, (_, j): [number, number] => j === k - 1 ? p
    : [points[i - 1]![0] + ((p[0] - points[i - 1]![0]) * (j + 1)) / k, points[i - 1]![1] + ((p[1] - points[i - 1]![1]) * (j + 1)) / k]));
/** A router answer over `points` cut `k` ways: one time/distance/scenic_score run per ORIGINAL segment, spanning k. */
function answer(points: [number, number][], edgeMs: number, runs: { surface: Run[]; access: Run[] }, timeMs?: number, k = 1) {
  const per = (v: number) => points.slice(1).map((_, i) => [i * k, (i + 1) * k, v]);
  return tripPath(cut(points, k), edgeMs, { time: per(edgeMs), distance: per(EDGE_M), scenic_score: per(8), surface: runs.surface,
    road_access: runs.access }, timeMs ?? (points.length - 1) * edgeMs);
}
const ROUTE_ANSWER: Record<Answer, string> = {
  crossing: answer(DETOUR, SCENIC_EDGE_MS, ROUTE_RUNS.crossing),
  reRequest: answer(ROAD, SCENIC_EDGE_MS, ROUTE_RUNS.reRequest, undefined, 2),
  refused: answer(ROAD, 10 * SCENIC_EDGE_MS, ROUTE_RUNS.refused, undefined, 3),
};
const LEG2_ANSWER: Record<Answer, string> = {
  crossing: answer([ROAD[20]!, ne(36), ROAD[40]!], 1000, LEG2_RUNS.crossing),
  reRequest: answer([ROAD[20]!, ROAD[40]!], 1000, LEG2_RUNS.reRequest, undefined, 4),
  refused: answer([ROAD[20]!, ROAD[40]!], 1000, LEG2_RUNS.refused, 99_000_000, 3),
};
const coordinatesOf = (body: string) => (JSON.parse(body) as { paths: { points: { coordinates: unknown } }[] }).paths[0]!.points.coordinates;

/** Rows: {preview, full} x the re-request {ships, refused}; `ships` is the answer whose path goes out. */
const TRIP_SHIP_ROWS: { name: string; full: boolean; reply: "reRequest" | "refused"; ships: Answer }[] = [
  { name: "preview, a closure on the chosen route, its re-request ships", full: false, reply: "reRequest", ships: "reRequest" },
  { name: "preview, the route's re-request refused - the crossing route stays", full: false, reply: "refused", ships: "crossing" },
  { name: "full, a closure on the day-2 leg, its re-request ships", full: true, reply: "reRequest", ships: "reRequest" },
  { name: "full, the day-2 leg's re-request refused - the crossing leg stays", full: true, reply: "refused", ships: "crossing" },
];

async function shipTrip(full: boolean, reply: "reRequest" | "refused") {
  const x = full ? X_LEG : X_ROUTE;
  const snapshot: ClosureSnapshot = { version: TEST_VERSION, fetchedAt: NOW.toISOString(), hazard: null,
    closures: { type: "FeatureCollection", features: [...NEAR, x] } as never };
  const sent: Record<string, unknown>[] = [];
  let scenic = 0;
  const fetchImpl = async (_input: RequestInfo | URL, init?: RequestInit) => {
    const body = JSON.parse(String(init?.body)) as Record<string, unknown>;
    sent.push(body);
    if (body.profile === "car_fast") return new Response(tripPath(ROAD, FAST_EDGE_MS));
    const points = body.points as [number, number][];
    if (JSON.stringify(points) === JSON.stringify(sent[0]!.points)) {
      scenic += 1;
      if (scenic === 1) return new Response(tripPath(ROAD, FAST_EDGE_MS));
      if (full) return new Response(answer(ROAD, SCENIC_EDGE_MS, ROUTE_RUNS.crossing));
      return new Response(ROUTE_ANSWER[carries(body, x) ? reply : "crossing"]);
    }
    if (JSON.stringify(points[1]) !== JSON.stringify(ROAD[40])) return new Response(answer(points, 1000, LEG1));
    return new Response(LEG2_ANSWER[carries(body, x) ? reply : "crossing"]);
  };
  const deps: TripDeps = {
    upstream: { counters: tripCounters([]).counters, fetchImpl, now: () => NOW, killed: () => false },
    routerBase: ROUTER,
    resolvePlace: async (id) => (id === BIG_SUR.id ? { lat: BIG_SUR.lat, lon: BIG_SUR.lon } : null),
    identify: () => ({ userId: "device-1", tier: full ? "paid" : "free" }),
    closures: async () => snapshot,
    tripPlaces: async () => {
      throw new Error("this harness has no trip_places table");
    },
  };
  const response = await handleTrip(tripRequest({ ...TRIP_BODY, days: 2 }), {}, deps);
  const json = (await response.json()) as { route?: { coordinates: unknown }; days?: { leg: { coordinates: unknown } | null; hazards: unknown }[] };
  return { status: response.status, reRequested: sent.filter((b) => carries(b, x)).length, route: json.route?.coordinates,
    legs: json.days?.map((d) => d.leg?.coordinates ?? null), hazards: json.days?.map((d) => d.hazards) };
}

describe("T-0340 /trip hazards come from the SHIPPED path (A1)", () => {
  it.each(TRIP_SHIP_ROWS)("$name: the trip's day hazards are the shipped path's runs", async ({ full, reply, ships }) => {
    const legs = [[ROAD[0], ROAD[20]], coordinatesOf(LEG2_ANSWER[ships])];
    expect(await shipTrip(full, reply)).toEqual({ status: 200, reRequested: 1,
      route: full ? ROAD : coordinatesOf(ROUTE_ANSWER[ships]), legs: full ? legs : [null, null],
      hazards: full ? [LEG1.hazards, LEG2_RUNS[ships].hazards] : ROUTE_RUNS[ships].days });
  });

  it("meta: every trip row ships one path whose runs differ from every other answer's - no wrong path's runs pass", () => {
    const read = (full: boolean, a: Answer) => JSON.stringify(full ? LEG2_RUNS[a].hazards : ROUTE_RUNS[a].days);
    const answers: Answer[] = ["crossing", "reRequest", "refused"];
    expect(TRIP_SHIP_ROWS.map((r) => answers.every((a) => a === r.ships || read(r.full, a) !== read(r.full, r.ships))))
      .toEqual(TRIP_SHIP_ROWS.map(() => true));
    // rv2-t0340: each row's answers (the crossing one and the row's reply) tile differently - a different point count
    // and a different vertex->point map - so a map read from a path that did not ship cannot pass for the shipped one.
    const tiling = (full: boolean, a: Answer) => {
      const path = (JSON.parse(full ? LEG2_ANSWER[a] : ROUTE_ANSWER[a]) as { paths: { points: { coordinates: unknown[] };
        details: { time: number[][] } }[] }).paths[0]!;
      return { points: path.points.coordinates.length, map: JSON.stringify([0, ...path.details.time.map((run) => run[1])]) };
    };
    expect(TRIP_SHIP_ROWS.map((r) => (["crossing", r.reply] as Answer[]).every((a) => a === r.ships
      || (tiling(r.full, a).points !== tiling(r.full, r.ships).points && tiling(r.full, a).map !== tiling(r.full, r.ships).map))))
      .toEqual(TRIP_SHIP_ROWS.map(() => true));
    expect(answers.map((a) => [tiling(false, a).points, tiling(true, a).points])).toEqual([[41, 3], [81, 5], [121, 4]]);
    expect(TRIP_SHIP_ROWS.map((r) => [r.full, r.ships])).toEqual([[false, "reRequest"], [false, "crossing"], [true, "reRequest"], [true, "crossing"]]);
  });
});
