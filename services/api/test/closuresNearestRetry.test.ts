/**
 * T-0282 N5 past each route's first request: a loop's reseed and retrace attempts, and a paid trip's day legs 3-5,
 * carry the <= 50 closures nearest THEIR OWN corridor - the loop's start, the leg's two vertices - never another
 * corridor's selection. Rows are cross products (loop: attempt shape x set variant, through ROUTES; trip: where the
 * late closure sits x set variant, through handleTrip with paid deps - no shipped identity reaches paid), each
 * expectation a function of its row, held by full equality of every request's areas and the hazard.
 */
import { env } from "cloudflare:test";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { mergeClosures, type ClosureSnapshot } from "../src/closuresStore";
import { buildCustomModel, type ClosureCollection } from "../src/customModel";
import { ROUTES, type Env } from "../src/index";
import { retracedAreas } from "../src/loopPlanner";
import { retraceScan } from "../src/retrace";
import { handleTrip } from "../src/trip";
import { closuresAt, TEST_VERSION } from "./closuresFake";
import { fakeQuotaNamespace } from "./doFake";
import { LOOP_BODY, loopPath, outAndBack, squareLoop } from "./loopHarness";
import { BIG_SUR, NOW as TRIP_NOW, ROAD, ROUTER, TRIP_BODY, tripCounters, tripRequest, tripRouter } from "./tripHarness";

const NOW = new Date("2026-10-05T12:00:00Z");
const STALE_AT = new Date(NOW.getTime() - 1_800_000 - 1);
const DEVICE = "0f8b6d5e-1a2b-4c3d-8e9f-0123456789ab";
type Pt = { lat: number; lon: number };
type Feature = { type: "Feature"; properties: { lcs_index: string }; geometry: { type: "Polygon"; coordinates: number[][][] } };
const fc = (features: Feature[]) => ({ type: "FeatureCollection" as const, features });
function square(name: string, c: Pt, half = 0.0005): Feature {
  const ring = [[c.lon - half, c.lat - half], [c.lon + half, c.lat - half], [c.lon + half, c.lat + half],
    [c.lon - half, c.lat + half], [c.lon - half, c.lat - half]];
  return { type: "Feature", properties: { lcs_index: name }, geometry: { type: "Polygon", coordinates: [ring] } };
}
const areasOf = (features: Feature[] | null) => (features === null ? undefined : buildCustomModel(0, fc(features) as ClosureCollection).areas);

// ---- the loop: its corridor is the start; far(i) due south of it, on(k) nested squares holding it.
const S = LOOP_BODY.start;
const far = (n: number) => Array.from({ length: n }, (_, i) => square(`far-${i + 1}`, { lat: S.lat - 0.01 - (i + 1) * 0.002, lon: S.lon }));
const on = () => Array.from({ length: 10 }, (_, k) => square(`on-${k + 1}`, S, 0.0005 + k * 0.00001));
const tie = () => Array.from({ length: 51 }, (_, k) => square(`tie-${k + 1}`, S, 0.0005 + k * 0.00001));
const fresh = (dropped: number) => ({ state: "fresh", version: TEST_VERSION, fetched_at: NOW.toISOString(), dropped });
interface LoopVariant { name: string; set: Feature[]; at: Date; sent: Feature[] | null; hazard: unknown;
  /** T-0286 C6: the closures holding the start, which every synthetic loop leaves from - all sent, so named, not re-requested. */
  crossed: string[] }
const LOOP_VARIANTS: LoopVariant[] = [
  { name: "empty", set: [], at: NOW, sent: null, hazard: undefined, crossed: [] },
  { name: "one closure", set: far(1), at: NOW, sent: far(1), hazard: undefined, crossed: [] },
  { name: "fifty", set: far(50), at: NOW, sent: far(50), hazard: undefined, crossed: [] },
  { name: "over 50, the start's ten stored last", set: [...far(50), ...on()], at: NOW, sent: [...far(40), ...on()], hazard: fresh(10),
    crossed: Array.from({ length: 10 }, (_, k) => `on-${k + 1}`) },
  { name: "a 51-way tie at distance 0", set: tie(), at: NOW, sent: tie().slice(0, 50), hazard: fresh(1), crossed: Array.from({ length: 51 }, (_, k) => `tie-${k + 1}`) },
  { name: "over 50, stale", set: [...far(50), ...on()], at: STALE_AT, sent: [...far(40), ...on()],
    hazard: { state: "stale", version: TEST_VERSION, fetched_at: STALE_AT.toISOString(), dropped: 10 }, crossed: Array.from({ length: 10 }, (_, k) => `on-${k + 1}`) },
];
const loopHazard = (v: LoopVariant) => (v.crossed.length > 0 ? { ...(v.hazard as object), crosses: v.crossed } : v.hazard);
const DIRTY = outAndBack(4000);
const RETRACE = retracedAreas(retraceScan(DIRTY.map(([lat, lon]) => ({ lat, lon })))!.retraced, S);
/** The attempts a shape drives: first dirty then a clean reseed; or two dirty, then the clean retrace attempt. */
const SHAPES = [
  { name: "first attempt dirty, the reseed clean", answers: [DIRTY, squareLoop()], retrace: false },
  { name: "first two dirty, the retrace attempt clean", answers: [DIRTY, DIRTY, squareLoop()], retrace: true },
];
const loopExpected = (shape: (typeof SHAPES)[number], v: LoopVariant) => {
  const sel = v.sent === null ? null : (fc(v.sent) as ClosureCollection);
  const plain = areasOf(v.sent);
  const third = buildCustomModel(0, mergeClosures(sel, RETRACE)).areas;
  return shape.retrace ? [plain, plain, third] : [plain, plain];
};

let answers: [number, number][][] = [];
let sent: { body: Record<string, unknown> }[] = [];
beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  sent = [];
  vi.stubGlobal("fetch", async (_input: RequestInfo | URL, init?: RequestInit) => {
    const body = JSON.parse(String(init?.body)) as Record<string, unknown>;
    sent.push({ body });
    return new Response(loopPath(answers.shift() ?? squareLoop()));
  });
});
afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

let graph = 0;
async function loop(v: LoopVariant, shape: (typeof SHAPES)[number]) {
  answers = shape.answers.slice();
  graph += 1;
  const shipped = { DB: env.DB, GIT_SHA: "test", BUILT_AT: "test", QUOTA: fakeQuotaNamespace().ns, ROUTER_URL: "https://router.test",
    ROUTER_SECRET: "s", GRAPH_VERSION: `retry-graph-${graph}`, CLOSURES: closuresAt(v.at, fc(v.set)).kv } as unknown as Env;
  const req = new Request("https://scenic-api.test/loop", { method: "POST",
    headers: { "content-type": "application/json", "x-scenic-device": DEVICE }, body: JSON.stringify(LOOP_BODY) });
  const response = await ROUTES["/loop"]!(req, shipped, new URL(req.url));
  const json = (await response.json()) as Record<string, unknown>;
  const rounds = sent.filter((s) => s.body.algorithm === "round_trip");
  return { status: response.status, hazard: json.closures_hazard, areas: rounds.map((s) => (s.body.custom_model as { areas?: unknown }).areas) };
}

describe("a loop's reseed and retrace attempts carry the start's own nearest <= 50 (N5, P-SAFE-08)", () => {
  for (const shape of SHAPES) {
    for (const v of LOOP_VARIANTS) {
      it(`/loop, ${shape.name}, ${v.name}: every attempt's areas and the hazard equal the start's selection`, async () => {
        const r = await loop(v, shape);
        expect([r.status, r.hazard, r.areas]).toEqual([200, loopHazard(v), loopExpected(shape, v)]);
      });
    }
  }
});

// ---- the trip: C, fifty squares ON the road's first edge (distance 0 to the search's chord and to leg 1);
// Z, one square 0.005 degrees north of road vertex z, beside a late leg and off every corridor.
const C = Array.from({ length: 50 }, (_, k) => square(`c-${k + 1}`, {
  lat: ROAD[0]![1] + ((k + 1) / 51) * (ROAD[1]![1] - ROAD[0]![1]), lon: ROAD[0]![0] + ((k + 1) / 51) * (ROAD[1]![0] - ROAD[0]![0]) }));
const zAt = (z: number) => square("z", { lat: ROAD[z]![1] + 0.005, lon: ROAD[z]![0] });
/** Measured: five days split the 40-edge road at vertices 0, 8, 16, 24, 32, 40. */
const LEGS = [[0, 8], [8, 16], [16, 24], [24, 32], [32, 40]];
/** Road vertices beside the middle of legs 3, 4 and 5. */
const ZS = [20, 28, 36];
/** In road edges (the road is straight): a leg's gap to Z against its gap to c-1, the cluster square farthest from it. */
const keepsZ = (a: number, b: number, z: number) => (z >= a && z <= b ? 0 : Math.min(Math.abs(a - z), Math.abs(b - z))) < a;
interface TripVariant { name: string; set: (z: Feature) => Feature[]; search: (z: Feature) => Feature[] | null;
  leg: (z: Feature, keeps: boolean) => Feature[] | null; dropped: number;
  /** T-0286 C6: the C squares stored - ON the road's first edge, so crossed by the search and leg 1, all sent. */
  crossed: number }
const TRIP_VARIANTS: TripVariant[] = [
  { name: "empty", set: () => [], search: () => null, leg: () => null, dropped: 0, crossed: 0 },
  { name: "one closure", set: (z) => [z], search: (z) => [z], leg: (z) => [z], dropped: 0, crossed: 0 },
  { name: "fifty", set: (z) => [...C.slice(0, 49), z], search: (z) => [...C.slice(0, 49), z], leg: (z) => [...C.slice(0, 49), z], dropped: 0,
    crossed: 49 },
  { name: "over 50", set: (z) => [...C, z], search: () => C, leg: (z, keeps) => (keeps ? [...C.slice(1), z] : C), dropped: 1, crossed: 50 },
];
const tripExpected = (v: TripVariant, z: number) => ({
  hazard: v.dropped === 0 && v.crossed === 0 ? undefined : { state: "fresh", version: TEST_VERSION, fetched_at: TRIP_NOW.toISOString(),
    ...(v.dropped > 0 ? { dropped: v.dropped } : {}), ...(v.crossed > 0 ? { crosses: C.slice(0, v.crossed).map((f) => f.properties.lcs_index) } : {}) },
  search: areasOf(v.search(zAt(z))),
  legs: LEGS.map(([a, b]) => ({ vertices: [a, b], areas: areasOf(v.leg(zAt(z), keepsZ(a!, b!, z))) })),
});

async function trip(set: Feature[]) {
  const snapshot: ClosureSnapshot = { version: TEST_VERSION, closures: fc(set) as ClosureCollection, hazard: null, fetchedAt: TRIP_NOW.toISOString() };
  const { counters } = tripCounters([]);
  const router = tripRouter();
  const deps = {
    upstream: { counters, fetchImpl: router.fetchImpl, now: () => TRIP_NOW, killed: () => false },
    routerBase: ROUTER,
    resolvePlace: async (id: string) => (id === BIG_SUR.id ? { lat: BIG_SUR.lat, lon: BIG_SUR.lon } : null),
    identify: () => ({ userId: "device-1", tier: "paid" as const }),
    closures: async () => snapshot,
  };
  const response = await handleTrip(tripRequest(TRIP_BODY), {}, deps);
  const body = (await response.json()) as Record<string, unknown>;
  const scenic = router.sent.filter((s) => s.body.profile === "car_scenic");
  const chord = JSON.stringify(scenic[0]!.body.points);
  const vertex = (p: unknown) => ROAD.findIndex((q) => JSON.stringify(q) === JSON.stringify(p));
  const areas = (s: (typeof scenic)[number]) => (s.body.custom_model as { areas?: unknown }).areas;
  const search = scenic.filter((s) => JSON.stringify(s.body.points) === chord);
  const legs = scenic.filter((s) => JSON.stringify(s.body.points) !== chord)
    .map((s) => ({ vertices: (s.body.points as unknown[]).map(vertex), areas: areas(s) }));
  return { status: response.status, hazard: body.closures_hazard, search: search.map(areas), legs };
}

describe("a paid trip's day legs 3-5 each carry their own nearest <= 50, never the search's (N5, P-SAFE-08)", () => {
  for (const z of ZS) {
    for (const v of TRIP_VARIANTS) {
      it(`/trip, Z beside road vertex ${z}, ${v.name}: the search and every leg carry their own corridor's selection`, async () => {
        const r = await trip(v.set(zAt(z)));
        const e = tripExpected(v, z);
        expect([r.status, r.hazard, r.search.length > 0, r.search, r.legs])
          .toEqual([200, e.hazard, true, r.search.map(() => e.search), e.legs]);
      });
    }
  }
});

describe("meta: every retry row is a function of its row", () => {
  it("the loop's twelve rows expect twelve different (attempts, hazard) lists", () => {
    const keys = SHAPES.flatMap((shape) => LOOP_VARIANTS.map((v) => JSON.stringify([loopExpected(shape, v), v.hazard ?? null])));
    expect(new Set(keys).size).toEqual(SHAPES.length * LOOP_VARIANTS.length);
  });
  it("over 50, the start's selection differs from the 50 nearest a corridor 1 degree south (every far closure first)", () => {
    const v = LOOP_VARIANTS[3]!;
    expect([v.sent!.length, JSON.stringify(v.sent) === JSON.stringify(v.set.slice(0, 50))]).toEqual([50, false]);
  });
  it("the trip: at each Z the four variants differ; the nine rows holding a closure are nine different lists", () => {
    const at = (z: number, vs: TripVariant[]) => vs.map((v) => JSON.stringify(tripExpected(v, z)));
    expect([ZS.map((z) => new Set(at(z, TRIP_VARIANTS)).size), new Set(ZS.flatMap((z) => at(z, TRIP_VARIANTS.slice(1)))).size])
      .toEqual([[4, 4, 4], 9]);
  });
  it("over 50, every Z row's last leg - and for each of legs 3, 4, 5 some row - differs from the search", () => {
    const rows = ZS.map((z) => tripExpected(TRIP_VARIANTS[3]!, z));
    const differs = (e: (typeof rows)[number], leg: number) => JSON.stringify(e.legs[leg]!.areas) !== JSON.stringify(e.search);
    expect([rows.map((e) => differs(e, 4)), [2, 3, 4].map((leg) => rows.some((e) => differs(e, leg)))])
      .toEqual([[true, true, true], [true, true, true]]);
  });
});
