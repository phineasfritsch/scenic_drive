/**
 * T-0282 through the SHIPPED ROUTES: the record holds every active closure (<= 2000 polygons, N1-N2) and each driven
 * request carries the <= 50 nearest ITS OWN corridor (N3-N5), sent in stored order; a closure ON the straight
 * corridor is never dropped while a farther one is kept; closures_hazard reports `dropped` when > 0 (N6).
 * Rows are a cross product of route x set variant (empty / one / fifty / over 50 / a 51-way tie / over 50 stale),
 * each expectation a function of its variant, held by full equality of every model's areas and of the hazard.
 */
import { env } from "cloudflare:test";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import placesSql from "../migrations/0001_places.sql?raw";
import type { ClosureSnapshot } from "../src/closuresStore";
import { buildCustomModel, type ClosureCollection } from "../src/customModel";
import { ROUTES, type Env } from "../src/index";
import { handleTrip } from "../src/trip";
import { closuresAt, TEST_VERSION } from "./closuresFake";
import { fakeQuotaNamespace } from "./doFake";
import { LOOP_BODY, loopPath, squareLoop } from "./loopHarness";
import { SANTA_MONICA_TOPANGA_BODY, syntheticPath } from "./planHarness";
import { BIG_SUR, NOW as TRIP_NOW, ORIGIN, ROUTER, TRIP_BODY, tripCounters, tripRequest, tripRouter } from "./tripHarness";

const NOW = new Date("2026-10-05T12:00:00Z");
/** P-SAFE-08's 30 minutes and the plan's 50 per request, ruled - literals, never the modules' own constants. */
const MAX_AGE_MS = 1_800_000;
const DEVICE = "0f8b6d5e-1a2b-4c3d-8e9f-0123456789ab";
const TOPANGA = { lat: 34.0676, lon: -118.5957 };

type Pt = { lat: number; lon: number };
type Feature = { type: "Feature"; properties: { lcs_index: string }; geometry: { type: "Polygon"; coordinates: number[][][] } };
const fc = (features: Feature[]) => ({ type: "FeatureCollection" as const, features });

/** A square of half-side `half` degrees around `c`, its own lcs_index. */
function square(name: string, c: Pt, half = 0.0005): Feature {
  const ring = [[c.lon - half, c.lat - half], [c.lon + half, c.lat - half], [c.lon + half, c.lat + half],
    [c.lon - half, c.lat + half], [c.lon - half, c.lat - half]];
  return { type: "Feature", properties: { lcs_index: name }, geometry: { type: "Polygon", coordinates: [ring] } };
}
/** far(i): due south of `c` (a corridor's midpoint), 0.01 + 0.002 i degrees - farther from the corridor with i. */
const far = (o: Pt, n: number) => Array.from({ length: n }, (_, i) => square(`far-${i + 1}`, { lat: o.lat - 0.01 - (i + 1) * 0.002, lon: o.lon }));
/** on(k): centred ON the straight corridor at k/11 of the way (a loop's corridor is its start: nested squares). */
const on = (o: Pt, d: Pt) => Array.from({ length: 10 }, (_, k) => square(`on-${k + 1}`,
  { lat: o.lat + ((k + 1) / 11) * (d.lat - o.lat), lon: o.lon + ((k + 1) / 11) * (d.lon - o.lon) }, 0.0005 + k * 0.00001));
/** tie(k): 51 squares all holding the origin - distance 0 for every one; the stored order decides. */
const tie = (o: Pt) => Array.from({ length: 51 }, (_, k) => square(`tie-${k + 1}`, o, 0.0005 + k * 0.00001));

type Path = "/plan" | "/loop" | "/trip";
const BODIES: Record<Path, unknown> = { "/plan": SANTA_MONICA_TOPANGA_BODY, "/loop": LOOP_BODY, "/trip": TRIP_BODY };
const CORRIDOR: Record<Path, [Pt, Pt]> = {
  "/plan": [SANTA_MONICA_TOPANGA_BODY.origin, TOPANGA],
  "/loop": [LOOP_BODY.start, LOOP_BODY.start],
  "/trip": [ORIGIN, { lat: BIG_SUR.lat, lon: BIG_SUR.lon }],
};
const mid = (o: Pt, d: Pt): Pt => ({ lat: (o.lat + d.lat) / 2, lon: (o.lon + d.lon) / 2 });
const fresh = (dropped: number) => ({ state: "fresh", version: TEST_VERSION, fetched_at: NOW.toISOString(), dropped });
const STALE_AT = new Date(NOW.getTime() - MAX_AGE_MS - 1);

interface Variant { name: string; set: (o: Pt, d: Pt) => Feature[]; at: Date; sent: (o: Pt, d: Pt) => Feature[] | null; hazard: unknown }
const VARIANTS: Variant[] = [
  { name: "empty", set: () => [], at: NOW, sent: () => null, hazard: undefined },
  { name: "one closure", set: (o, d) => far(mid(o, d), 1), at: NOW, sent: (o, d) => far(mid(o, d), 1), hazard: undefined },
  { name: "fifty", set: (o, d) => far(mid(o, d), 50), at: NOW, sent: (o, d) => far(mid(o, d), 50), hazard: undefined },
  { name: "over 50, the on-corridor ten stored last", set: (o, d) => [...far(mid(o, d), 50), ...on(o, d)], at: NOW,
    sent: (o, d) => [...far(mid(o, d), 40), ...on(o, d)], hazard: fresh(10) },
  { name: "a 51-way tie at distance 0", set: (o) => tie(o), at: NOW, sent: (o) => tie(o).slice(0, 50), hazard: fresh(1) },
  { name: "over 50, stale", set: (o, d) => [...far(mid(o, d), 50), ...on(o, d)], at: STALE_AT, sent: (o, d) => [...far(mid(o, d), 40), ...on(o, d)],
    hazard: { state: "stale", version: TEST_VERSION, fetched_at: STALE_AT.toISOString(), dropped: 10 } },
];
const areasOf = (features: Feature[] | null) => (features === null ? undefined : buildCustomModel(0, fc(features) as ClosureCollection).areas);

let sent: { url: string; body: Record<string, unknown> }[];
let graph = 0;

beforeAll(async () => {
  await env.DB.prepare(placesSql).run();
  await env.DB.prepare("INSERT OR REPLACE INTO places (id, lat, lon) VALUES ('la:topanga', 34.0676, -118.5957), ('la:big-sur', 36.27, -121.81)").run();
});

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  sent = [];
  const trip = tripRouter();
  vi.stubGlobal("fetch", async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input instanceof Request ? input.url : input);
    const body = JSON.parse(String(init?.body)) as Record<string, unknown>;
    sent.push({ url, body });
    if (body.algorithm === "round_trip") return new Response(loopPath(squareLoop()));
    if (JSON.stringify(body.points).includes("-121.81")) return trip.fetchImpl(input, init);
    return new Response(body.profile === "car_fast" ? syntheticPath(1_000_000, [1, 2, 3]) : syntheticPath(1_200_000, [4, 5, 6]));
  });
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

function shipped(closures: KVNamespace): Env {
  graph += 1;
  return { DB: env.DB, GIT_SHA: "test", BUILT_AT: "test", QUOTA: fakeQuotaNamespace().ns, ROUTER_URL: "https://router.test",
    ROUTER_SECRET: "s", GRAPH_VERSION: `nearest-graph-${graph}`, CLOSURES: closures } as unknown as Env;
}

async function send(path: Path, set: Feature[], at: Date) {
  const req = new Request(`https://scenic-api.test${path}`, { method: "POST",
    headers: { "content-type": "application/json", "x-scenic-device": DEVICE }, body: JSON.stringify(BODIES[path]) });
  const response = await ROUTES[path]!(req, shipped(closuresAt(at, fc(set)).kv), new URL(req.url));
  const json = (await response.json()) as Record<string, unknown>;
  const areas = sent.flatMap((s) => (s.body.custom_model === undefined ? [] : [(s.body.custom_model as { areas?: unknown }).areas]));
  return { status: response.status, hazard: json.closures_hazard, areas };
}

describe("each driven request carries the <= 50 closures nearest its own corridor (N3-N6, P-SAFE-08)", () => {
  for (const path of Object.keys(BODIES) as Path[]) {
    const [o, d] = CORRIDOR[path];
    for (const v of VARIANTS) {
      it(`${path}, ${v.name}: every model's areas and the hazard equal the variant's selection`, async () => {
        const r = await send(path, v.set(o, d), v.at);
        const expected = areasOf(v.sent(o, d));
        expect([r.status, r.hazard, r.areas.length > 0, r.areas]).toEqual([200, v.hazard, true, r.areas.map(() => expected)]);
      });
    }
  }
});

describe("meta: every row is a function of its variant", () => {
  for (const path of Object.keys(BODIES) as Path[]) {
    it(`${path}: the six variants expect six different (areas, hazard) pairs`, () => {
      const [o, d] = CORRIDOR[path];
      const keys = VARIANTS.map((v) => JSON.stringify([areasOf(v.sent(o, d)), v.hazard ?? null]));
      expect(new Set(keys).size).toEqual(VARIANTS.length);
    });
  }
  it("over 50, every on-corridor closure is sent and every dropped one is a far closure", () => {
    for (const path of Object.keys(BODIES) as Path[]) {
      const [o, d] = CORRIDOR[path];
      const v = VARIANTS[3]!;
      const names = v.sent(o, d)!.map((f) => f.properties.lcs_index);
      expect([names.length, on(o, d).every((f) => names.includes(f.properties.lcs_index)),
        v.set(o, d).filter((f) => !names.includes(f.properties.lcs_index)).every((f) => f.properties.lcs_index.startsWith("far-"))])
        .toEqual([50, true, true]);
    }
  });
});

describe("the stored set's bound (N1, N2)", () => {
  it("/plan, 2000 polygons stored: fresh, the 50 nearest sent, 1950 dropped", async () => {
    const m = mid(...CORRIDOR["/plan"]);
    const r = await send("/plan", far(m, 2000), NOW);
    expect([r.status, r.hazard, r.areas]).toEqual([200, fresh(1950), r.areas.map(() => areasOf(far(m, 50)))]);
  });

  it("/plan, 2001 polygons stored: unavailable, no areas, never silent", async () => {
    const m = mid(...CORRIDOR["/plan"]);
    const r = await send("/plan", far(m, 2001), NOW);
    expect([r.status, r.hazard, r.areas]).toEqual([200, { state: "unavailable", version: "none", fetched_at: null }, r.areas.map(() => undefined)]);
  });

  it("/plan, 60 polygons stored, the 60th's ring not closed: unavailable - every feature is read, not the first 50", async () => {
    const set = far(mid(...CORRIDOR["/plan"]), 60);
    set[59]!.geometry.coordinates[0]!.pop();
    const r = await send("/plan", set, NOW);
    expect([r.status, r.hazard, r.areas]).toEqual([200, { state: "unavailable", version: "none", fetched_at: null }, r.areas.map(() => undefined)]);
  });
});

describe("a paid trip's day legs each carry the closures nearest the leg (N5)", () => {
  it("the search and legs 3-5 carry Big Sur and the 49 nearest of the origin's 50; legs 1-2 the origin's 50", async () => {
    const F = far(ORIGIN, 50);
    const B = square("big-sur", { lat: BIG_SUR.lat, lon: BIG_SUR.lon });
    const snapshot: ClosureSnapshot = { version: TEST_VERSION, closures: fc([...F, B]) as ClosureCollection, hazard: null,
      fetchedAt: TRIP_NOW.toISOString() };
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
    const scenic = router.sent.filter((s) => s.body.profile === "car_scenic").map((s) => (s.body.custom_model as { areas?: unknown }).areas);
    const withBigSur = areasOf([...F.slice(0, 49), B]);
    const origin50 = areasOf(F);
    expect([response.status, body.closures_hazard, scenic])
      .toEqual([200, { state: "fresh", version: TEST_VERSION, fetched_at: TRIP_NOW.toISOString(), dropped: 1 },
        [...Array(6).fill(withBigSur), origin50, origin50, withBigSur, withBigSur, withBigSur]]);
  });
});
