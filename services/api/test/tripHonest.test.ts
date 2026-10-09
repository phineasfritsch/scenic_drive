/**
 * T-0335 A1 through handleTrip - the handler ROUTES["/trip"] calls: a road trip whose chosen route scores below
 * RouteScore's 0.45 (or cannot be scored) is refused with nothing_pretty BEFORE any day leg, never shipped as a 200.
 * The road is tripHarness's 40 edges; the scenic answer carries one scenic_score per edge, read by T-0332's oracle
 * (Tests/Fixtures/t0332/oracle.py): every edge 2 -> 0.020000, 5 -> 0.425000, 6 -> 0.510000.
 */
import { FRESH_EMPTY, TEST_VERSION } from "./closuresFake";
import { describe, expect, it } from "vitest";
import type { ClosureSnapshot } from "../src/closuresStore";
import type { Tier } from "../src/quota";
import { handleTrip, type TripDeps } from "../src/trip";
import { BIG_SUR, EDGE_M, EDGES, expectedTrip, FAST_EDGE_MS, NOW, ROAD, ROUTER, SCENIC_EDGE_MS, TRIP_BODY, tripCounters, tripPath,
  tripRequest, tripRouter } from "./tripHarness";

const runs = (value: number) => Array.from({ length: EDGES }, (_, i) => [i, i + 1, value]);

/** The scenic A->B answer over `points` with every edge scored `score`, or no scenic_score detail when null. */
function scenic(score: number | null, points: [number, number][] = ROAD): string {
  const details: Record<string, unknown> = { time: runs(SCENIC_EDGE_MS), distance: runs(EDGE_M) };
  if (score !== null) details.scenic_score = runs(score);
  return tripPath(points, SCENIC_EDGE_MS, details);
}

function harness(tier: Tier, answer: string) {
  const events: string[] = [];
  const { counters } = tripCounters(events);
  const router = tripRouter({ scenic: answer, onFetch: () => events.push("fetch") });
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
    const response = await handleTrip(tripRequest(TRIP_BODY), {}, deps);
    return { status: response.status, json: (await response.json()) as Record<string, unknown>, requests: router.sent.length };
  };
  return { run };
}

const REFUSED = { status: 422, json: { error: "nothing_pretty", days: 5, extra_budget_pct: 40 }, requests: 7 };

describe("POST /trip honest failure (T-0335 A1, P-SAFE-04)", () => {
  it("a preview trip whose chosen route scores 0.02 answers nothing_pretty, never a 200 trip", async () => {
    expect(await harness("free", scenic(2)).run()).toEqual(REFUSED);
  });

  it("a full trip whose chosen route scores 0.02 is refused before any day leg is requested", async () => {
    expect(await harness("paid", scenic(2)).run()).toEqual(REFUSED);
  });

  it("every edge 5 (0.425, the encoding below 0.45) is refused; every edge 6 (0.51, above) is the whole 200 trip", async () => {
    expect(await harness("free", scenic(5)).run()).toEqual(REFUSED);
    const shipped = await harness("free", scenic(6)).run();
    expect(shipped).toEqual({ status: 200, requests: 7,
      json: expectedTrip({ days: 5, edgeMs: SCENIC_EDGE_MS, lambda: 7.75, full: false }) });
  });

  it("a chosen route with no scenic_score detail is refused (T-0332 R3, fail closed)", async () => {
    expect(await harness("free", scenic(null)).run()).toEqual(REFUSED);
    expect(await harness("paid", scenic(null)).run()).toEqual(REFUSED);
  });
});

/** closuresCrossingTrip's search detour: road vertex 20 moved 0.3 degrees north-east, X on the edge 19 -> 20', and 50
 *  squares due south of the origin nearer the corridor than X - so X is stored but not sent, and the chosen detour
 *  crosses it: one re-request carrying X is made (8 <= 12) and answered with the straight road. */
type Feature = { type: "Feature"; properties: { lcs_index: string }; geometry: { type: "Polygon"; coordinates: number[][][] } };
function square(name: string, lon: number, lat: number, half = 0.0005): Feature {
  const ring = [[lon - half, lat - half], [lon + half, lat - half], [lon + half, lat + half], [lon - half, lat + half], [lon - half, lat - half]];
  return { type: "Feature", properties: { lcs_index: name }, geometry: { type: "Polygon", coordinates: [ring] } };
}
const D20: [number, number] = [ROAD[20]![0] + 0.3, ROAD[20]![1] + 0.3];
const DETOUR = ROAD.map((p, i) => (i === 20 ? D20 : p));
const X = square("x", (ROAD[19]![0] + D20[0]) / 2, (ROAD[19]![1] + D20[1]) / 2);
const SOUTH = Array.from({ length: 50 }, (_, i) => square(`o-${i + 1}`, ROAD[0]![0], ROAD[0]![1] - 0.01 - (i + 1) * 0.002));
const SNAPSHOT: ClosureSnapshot = { version: TEST_VERSION, closures: { type: "FeatureCollection", features: [...SOUTH, X] },
  hazard: null, fetchedAt: NOW.toISOString() };

/** The search answers the detour scored `first`; the closure re-request (the request carrying X) the road scored `again`. */
async function crossing(first: number, again: number) {
  const sent: Record<string, unknown>[] = [];
  let scenicCount = 0;
  const fetchImpl = async (_input: RequestInfo | URL, init?: RequestInit) => {
    const body = JSON.parse(String(init?.body)) as Record<string, unknown>;
    sent.push(body);
    if (body.profile === "car_fast") return new Response(tripPath(ROAD, FAST_EDGE_MS));
    scenicCount += 1;
    if (scenicCount === 1) return new Response(tripPath(ROAD, FAST_EDGE_MS));
    const carriesX = JSON.stringify((body.custom_model as { areas?: unknown }).areas ?? null).includes(JSON.stringify(X.geometry.coordinates));
    return new Response(carriesX ? scenic(again) : scenic(first, DETOUR));
  };
  const { counters } = tripCounters([]);
  const deps: TripDeps = {
    upstream: { counters, fetchImpl, now: () => NOW, killed: () => false },
    routerBase: ROUTER,
    resolvePlace: async () => ({ lat: BIG_SUR.lat, lon: BIG_SUR.lon }),
    identify: () => ({ userId: "device-1", tier: "free" }),
    closures: async () => SNAPSHOT,
    tripPlaces: async () => {
      throw new Error("this harness has no trip_places table");
    },
  };
  const response = await handleTrip(tripRequest({ ...TRIP_BODY, days: 2 }), {}, deps);
  return { status: response.status, json: await response.json(), requests: sent.length };
}

describe("POST /trip honest failure scores the route that would SHIP - after the closure re-request (T-0335 R2)", () => {
  it("a pretty detour crossing a closure, re-requested to a dull road, is refused", async () => {
    expect(await crossing(8, 2)).toEqual({ status: 422, json: { error: "nothing_pretty", days: 2, extra_budget_pct: 40 }, requests: 8 });
  });

  it("a dull detour crossing a closure, re-requested to a pretty road, ships the road (whole 200)", async () => {
    expect(await crossing(2, 8)).toEqual({ status: 200, requests: 8, json: {
      ...expectedTrip({ days: 2, edgeMs: SCENIC_EDGE_MS, lambda: 7.75, full: false }),
      closures_hazard: { state: "fresh", version: TEST_VERSION, fetched_at: NOW.toISOString(), dropped: 1 } } });
  });
});
