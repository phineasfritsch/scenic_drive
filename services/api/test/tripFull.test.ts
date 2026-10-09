/**
 * T-0268 R3/R5/R7 through handleTrip - the handler ROUTES["/trip"] calls - with injected deps, because no shipped
 * identity reaches the paid tier until /attest (T-0256 R3). paid = the FULL itinerary: one car_scenic leg per day at
 * the winning lambda, 1 + 6 + days <= 12 requests; free = the preview. Every fetch is counted against the reserve.
 */
import { FRESH_EMPTY } from "./closuresFake";
import { describe, expect, it } from "vitest";
import { buildCustomModel } from "../src/customModel";
import type { Tier } from "../src/quota";
import { handleTrip, TRIP_UPSTREAM_COST, type TripDeps } from "../src/trip";
import { guardedPlan, PlanBudgetExceeded } from "../src/upstream";
import { BIG_SUR, PRETTY_RUNS, EDGE_M, EDGES, expectedTrip, NOW, ROAD, ROUTER, SCENIC_EDGE_MS, TRIP_BODY, tripCounters, tripPath,
  tripRequest, tripRouter, type RouterOptions } from "./tripHarness";

const LEG = { points_encoded: false, instructions: false, "ch.disable": true, details: ["time", "distance", "scenic_score", "surface", "road_access"] };

function harness(tier: Tier, options: RouterOptions = {}) {
  const events: string[] = [];
  const { counters, reserved } = tripCounters(events);
  const router = tripRouter({ ...options, onFetch: () => events.push("fetch") });
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
  const run = async (body: unknown = TRIP_BODY) => {
    const response = await handleTrip(tripRequest(body), {}, deps);
    return { status: response.status, json: (await response.json()) as Record<string, unknown> };
  };
  return { run, events, reserved, sent: router.sent };
}

describe("the full itinerary (paid, R3/R5)", () => {
  it("a 5-day trip is exactly 12 requests, reserved first: the whole answer, and each day ONE leg at the winning lambda", async () => {
    const h = harness("paid");
    expect(await h.run()).toEqual({ status: 200, json: expectedTrip({ days: 5, edgeMs: SCENIC_EDGE_MS, lambda: 7.75, full: true }) });
    expect([h.events, h.reserved]).toEqual([["reserve", ...Array(TRIP_UPSTREAM_COST).fill("fetch")], [["device-1", 12, "trip", "paid"]]]);
    expect(h.sent.slice(7).map((s) => s.body)).toEqual([0, 8, 16, 24, 32].map((v) => ({ ...LEG,
      points: [ROAD[v], ROAD[v + 8]], profile: "car_scenic", custom_model: buildCustomModel(7.75, null) })));
  });

  it("days 1 to 5 make 7 + days requests, never more than 12", async () => {
    const counts = [];
    for (const days of [1, 2, 3, 4, 5]) {
      const h = harness("paid");
      const r = await h.run({ ...TRIP_BODY, days });
      counts.push([days, r.status, h.sent.length, h.reserved]);
    }
    expect(counts).toEqual([1, 2, 3, 4, 5].map((days) => [days, 200, 7 + days, [["device-1", 12, "trip", "paid"]]]));
  });

  it("free is the preview: no legs, 7 requests, the free tier reserved under trip", async () => {
    const h = harness("free");
    expect(await h.run()).toEqual({ status: 200, json: expectedTrip({ days: 5, edgeMs: SCENIC_EDGE_MS, lambda: 7.75, full: false }) });
    expect([h.sent.length, h.reserved]).toEqual([7, [["device-1", 12, "trip", "free"]]]);
  });
});

describe("the ceiling per day and for the trip (R7)", () => {
  // Day 3 drives 8 edges, 3_600_000 ms; its ceiling is floor(20_160_000 x 3_600_000 / 18_000_000) = 4_032_000.
  const day3 = (ms: number) => (leg: number, from: number, to: number) => (leg === 3 ? ms : (to - from) * SCENIC_EDGE_MS);

  it("a leg of exactly its day ceiling plans; one millisecond more refuses the whole trip after that leg", async () => {
    const exact = harness("paid", { legMs: day3(4_032_000) });
    expect(await exact.run()).toEqual({ status: 200,
      json: expectedTrip({ days: 5, edgeMs: SCENIC_EDGE_MS, lambda: 7.75, full: true, legMs: day3(4_032_000) }) });
    const over = harness("paid", { legMs: day3(4_032_001) });
    expect(await over.run()).toEqual({ status: 422, json: { error: "ceiling_breached",
      detail: "day 3 leg takes 4032001 ms against its ceiling of 4032000 ms" } });
    expect(over.sent.length).toBe(10);
  });

  it("every leg at its day ceiling: the trip takes exactly fastest + budget, never more", async () => {
    const h = harness("paid", { legMs: () => 4_032_000 });
    const r = await h.run();
    expect([r.status, r.json.eta_s, r.json.ceiling_s]).toEqual([200, 20_160, 20_160]);
  });

  // A share that does NOT divide (T-0268 pre-review survivor day-ceiling-ceil): edge 0 takes 450_001 ms, so the route
  // is 18_000_001 ms and days are 3_600_001 + 4 x 3_600_000. floor(20_160_000 x day / 18_000_001) = 4_032_000 and
  // 4 x 4_031_999 (sum 20_159_996 <= 20_160_000); rounded UP they would be 4_032_001 + 4 x 4_032_000 = 20_160_001.
  const UNEVEN = [450_001, ...Array<number>(EDGES - 1).fill(SCENIC_EDGE_MS)];
  const unevenScenic = tripPath(ROAD, 0, { time: UNEVEN.map((ms, i) => [i, i + 1, ms]),
    distance: UNEVEN.map((_, i) => [i, i + 1, EDGE_M]), scenic_score: PRETTY_RUNS }, 18_000_001);
  const FLOORS = [4_032_000, 4_031_999, 4_031_999, 4_031_999, 4_031_999];

  it("an uneven share floors each day ceiling: the whole answer, and the day ceilings sum to <= the trip ceiling", async () => {
    const h = harness("paid", { scenic: unevenScenic });
    const r = await h.run();
    expect(r).toEqual({ status: 200,
      json: expectedTrip({ days: 5, edgeMs: SCENIC_EDGE_MS, lambda: 7.75, full: true, edgesMs: UNEVEN }) });
    const ceilings = (r.json.days as { ceiling_s: number }[]).map((d) => Math.round(d.ceiling_s * 1000));
    expect([ceilings, ceilings.reduce((a, b) => a + b, 0) <= 20_160_000]).toEqual([FLOORS, true]);
  });

  it("an uneven share, each day at its floored ceiling plans; one millisecond more refuses with that floor", async () => {
    const answered = [];
    for (const [i, floor] of FLOORS.entries()) {
      for (const ms of [floor, floor + 1]) {
        const legMs = (leg: number, from: number, to: number) => (leg === i + 1 ? ms : (to - from) * SCENIC_EDGE_MS);
        const r = await harness("paid", { scenic: unevenScenic, legMs }).run();
        answered.push([i + 1, ms, r.status, r.json.error ?? null, r.json.detail ?? null]);
      }
    }
    expect(answered).toEqual(FLOORS.flatMap((floor, i) => [[i + 1, floor, 200, null, null],
      [i + 1, floor + 1, 422, "ceiling_breached", `day ${i + 1} leg takes ${floor + 1} ms against its ceiling of ${floor} ms`]]));
  });

  it("an uneven share, every leg at its floored ceiling: the trip ETA is the floors' sum, never past fastest + budget", async () => {
    const h = harness("paid", { scenic: unevenScenic, legMs: (leg) => FLOORS[leg - 1]! });
    const r = await h.run();
    expect([r.status, r.json.eta_s, r.json.ceiling_s]).toEqual([200, 20_159.996, 20_160]);
  });
});

describe("the cap (P-COST-04)", () => {
  it("guardedPlan at TRIP_UPSTREAM_COST refuses a 13th request before fetch", async () => {
    const events: string[] = [];
    const { counters } = tripCounters(events);
    let fetched = 0;
    const upstream = { counters, fetchImpl: async () => { fetched += 1; return new Response("{}"); }, now: () => NOW, killed: () => false };
    const refused = guardedPlan(upstream, { userId: "device-1", tier: "paid", kind: "trip" }, async (call) => {
      for (let i = 0; i < TRIP_UPSTREAM_COST; i++) await call(`${ROUTER}/route`);
      return call(`${ROUTER}/route`);
    }, TRIP_UPSTREAM_COST);
    await expect(refused).rejects.toBeInstanceOf(PlanBudgetExceeded);
    expect([fetched, events[0]]).toEqual([12, "reserve"]);
  });
});

describe("a scenic body the splitter cannot read is 502 no_route, never partly split (R3)", () => {
  const runs = (n: number, value: unknown, shift = 0) => Array.from({ length: n }, (_, i) => [i + shift, i + 1 + shift, value]);
  const CASES: [string, Record<string, unknown>, string][] = [
    ["no time runs", { distance: runs(EDGES, EDGE_M) }, "the route carries no per-edge time and distance runs"],
    ["fewer distance runs", { time: runs(EDGES, 450_000), distance: runs(EDGES - 1, EDGE_M) }, "the route carries no per-edge time and distance runs"],
    ["a gap at the start", { time: runs(EDGES, 450_000, 1), distance: runs(EDGES, EDGE_M, 1) }, "the time and distance runs do not tile the route at point 0"],
    ["an empty run", { time: [[0, 0, 1], ...runs(EDGES, 450_000)], distance: [[0, 0, 1], ...runs(EDGES, EDGE_M)] }, "the time and distance runs do not tile the route at point 0"],
    ["distance runs on other edges", { time: runs(EDGES, 450_000), distance: [[0, 2, EDGE_M], ...runs(EDGES - 1, EDGE_M, 1)] }, "the time and distance runs do not tile the route at point 0"],
    ["a fractional millisecond", { time: runs(EDGES, 450_000.5), distance: runs(EDGES, EDGE_M) }, "edge 0 has no whole-millisecond time and finite distance"],
    ["a negative time", { time: runs(EDGES, -1), distance: runs(EDGES, EDGE_M) }, "edge 0 has no whole-millisecond time and finite distance"],
    ["a negative distance", { time: runs(EDGES, 450_000), distance: runs(EDGES, -1) }, "edge 0 has no whole-millisecond time and finite distance"],
    ["a string distance", { time: runs(EDGES, 450_000), distance: runs(EDGES, "far") }, "edge 0 has no whole-millisecond time and finite distance"],
    ["runs short of the end", { time: runs(EDGES - 1, 450_000), distance: runs(EDGES - 1, EDGE_M) }, "the runs end at point 39, not the route's last point 40"],
    ["no time at all", { time: runs(EDGES, 0), distance: runs(EDGES, EDGE_M) }, "the route takes no time"],
  ];

  it("each malformed body has its own detail", async () => {
    const answered = [];
    for (const [name, details] of CASES) {
      const h = harness("free", { scenic: tripPath(ROAD, 0, details, 18_000_000) });
      answered.push([name, await h.run()]);
    }
    expect(answered).toEqual(CASES.map(([name, , detail]) => [name, { status: 502, json: { error: "no_route", detail } }]));
  });
});

// Per-day ceilings at EVERY extra_budget_pct bound (rv1-t0268), with NON-exact division: the fastest is 14_400_037 ms,
// the chosen route 360_001 + 39 x 360_000 = 14_400_001 ms, days 2_880_001 + 4 x 2_880_000, and ceiling x day mod total
// is non-zero for every pct and day (python, quoted in the Log). Each day's leg at its floor plans; one ms more refuses.
describe("the per-day ceiling at every extra_budget_pct bound, non-exact shares (P-SAFE-04)", () => {
  const FASTEST = 14_400_037;
  const ROUTE = [360_001, ...Array<number>(EDGES - 1).fill(360_000)];
  const routeBody = tripPath(ROAD, 0, { time: ROUTE.map((ms, i) => [i, i + 1, ms]), distance: ROUTE.map((_, i) => [i, i + 1, EDGE_M]),
    scenic_score: PRETTY_RUNS }, FASTEST);
  const FLOORS: [number, number[]][] = [
    [0, [2_880_008, 2_880_007, 2_880_007, 2_880_007, 2_880_007]],
    [1, [2_908_808, 2_908_807, 2_908_807, 2_908_807, 2_908_807]],
    [10, [3_168_008, 3_168_007, 3_168_007, 3_168_007, 3_168_007]],
    [39, [4_003_211, 4_003_209, 4_003_209, 4_003_209, 4_003_209]],
    [40, [4_032_011, 4_032_009, 4_032_009, 4_032_009, 4_032_009]],
  ];

  it("each day's leg at floor(ceiling x day / total) plans (whole answer); one ms more is 422 (whole body)", async () => {
    const answered = [];
    const expected = [];
    for (const [pct, floors] of FLOORS) {
      for (const [i, floor] of floors.entries()) {
        for (const ms of [floor, floor + 1]) {
          const legMs = (leg: number, from: number, to: number) => (leg === i + 1 ? ms : (to - from) * 360_000);
          const r = await harness("paid", { fastestMs: FASTEST, scenic: routeBody, legMs }).run({ ...TRIP_BODY, extra_budget_pct: pct });
          answered.push([pct, i + 1, ms, r]);
          expected.push([pct, i + 1, ms, ms === floor
            ? { status: 200, json: expectedTrip({ days: 5, pct, edgeMs: 0, lambda: 7.75, full: true, fastestMs: FASTEST, edgesMs: ROUTE, legMs }) }
            : { status: 422, json: { error: "ceiling_breached", detail: `day ${i + 1} leg takes ${ms} ms against its ceiling of ${floor} ms` } }]);
        }
      }
    }
    expect(answered).toEqual(expected);
  });
});
