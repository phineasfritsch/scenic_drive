/**
 * T-0286 C5 on a PAID trip (full view, through handleTrip with paid deps - no shipped identity reaches paid): the
 * search's chosen route and each day leg are held to every stored closure, and a re-request is made only inside
 * TRIP_UPSTREAM_COST (12) - the search reserves `days` legs, a leg the legs after it. The search makes 1 fastest + 6
 * scenic requests (measured, T-0282), so a re-request fits exactly when 1 + 6 + 1 + days <= 12, i.e. days <= 4; two
 * fit when days <= 3. Rows: where the path crosses the dropped X (the search's detour / the last leg / both) x days
 * 2..5, the router honouring X (a request carrying X is answered clear). Every expectation is a function of its row.
 */
import { describe, expect, it } from "vitest";
import type { ClosureSnapshot } from "../src/closuresStore";
import type { ClosureCollection } from "../src/customModel";
import { handleTrip } from "../src/trip";
import { TEST_VERSION } from "./closuresFake";
import { BIG_SUR, FAST_EDGE_MS, NOW, ORIGIN, ROAD, ROUTER, SCENIC_EDGE_MS, TRIP_BODY, tripCounters, tripPath, tripRequest } from "./tripHarness";

type Pt = { lat: number; lon: number };
type Feature = { type: "Feature"; properties: { lcs_index: string }; geometry: { type: "Polygon"; coordinates: number[][][] } };
function square(name: string, c: Pt, half = 0.0005): Feature {
  const ring = [[c.lon - half, c.lat - half], [c.lon + half, c.lat - half], [c.lon + half, c.lat + half],
    [c.lon - half, c.lat + half], [c.lon - half, c.lat - half]];
  return { type: "Feature", properties: { lcs_index: name }, geometry: { type: "Polygon", coordinates: [ring] } };
}
const south = (tag: string, c: Pt) => Array.from({ length: 50 }, (_, i) => square(`${tag}-${i + 1}`, { lat: c.lat - 0.01 - (i + 1) * 0.002, lon: c.lon }));
const at = (i: number): Pt => ({ lon: ROAD[i]![0], lat: ROAD[i]![1] });
/** The search's detour: road vertex 20 moved 0.3 degrees north-east; X_SEARCH sits on the middle of the edge 19 -> 20'. */
const D20: [number, number] = [ROAD[20]![0] + 0.3, ROAD[20]![1] + 0.3];
const DETOUR = ROAD.map((p, i) => (i === 20 ? D20 : p));
const X_SEARCH = square("x", { lon: (ROAD[19]![0] + D20[0]) / 2, lat: (ROAD[19]![1] + D20[1]) / 2 });
/** The last leg's detour runs through X_LEG's centre, 0.3 degrees north-east of road vertex 36. */
const X_LEG_C: [number, number] = [ROAD[36]![0] + 0.3, ROAD[36]![1] + 0.3];
const X_LEG = square("x", { lon: X_LEG_C[0], lat: X_LEG_C[1] });
/** 100 squares far nearer every corridor than X: 50 due south of the origin, 50 due south of road vertex 36. */
const NEAR = [...south("o", at(0)), ...south("l", at(36))];
/** 101 single closures stored, 50 sent: 51 left out (102 and 52 when both Xs are stored). */
const dropped = (where: Where) => (where === "both" ? 52 : 51);

type Where = "search" | "last leg" | "both";
const WHERE: Where[] = ["search", "last leg", "both"];
/** From 2: a one-day leg IS the search chord (origin -> destination) and this router tells them apart by chord. */
const DAYS = [2, 3, 4, 5];
const carries = (body: Record<string, unknown>, x: Feature) =>
  JSON.stringify((body.custom_model as { areas?: unknown } | undefined)?.areas ?? null).includes(JSON.stringify(x.geometry.coordinates));

async function run(where: Where, days: number) {
  const xs = where === "search" ? [X_SEARCH] : where === "last leg" ? [X_LEG] : [X_SEARCH, { ...X_LEG, properties: { lcs_index: "x-leg" } }];
  const snapshot: ClosureSnapshot = { version: TEST_VERSION, closures: { type: "FeatureCollection", features: [...NEAR, ...xs] } as ClosureCollection,
    hazard: null, fetchedAt: NOW.toISOString() };
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
      return new Response(tripPath(where !== "last leg" && !carries(body, X_SEARCH) ? DETOUR : ROAD, SCENIC_EDGE_MS));
    }
    const last = JSON.stringify(points[1]) === JSON.stringify(ROAD[40]);
    const through = where !== "search" && last && !carries(body, xs.at(-1)!);
    return new Response(tripPath(through ? [points[0]!, X_LEG_C, points[1]!] : [points[0]!, points[1]!], 1000));
  };
  const deps = {
    upstream: { counters: tripCounters([]).counters, fetchImpl, now: () => NOW, killed: () => false },
    routerBase: ROUTER,
    resolvePlace: async (id: string) => (id === BIG_SUR.id ? { lat: BIG_SUR.lat, lon: BIG_SUR.lon } : null),
    identify: () => ({ userId: "device-1", tier: "paid" as const }),
    closures: async () => snapshot,
  };
  const response = await handleTrip(tripRequest({ ...TRIP_BODY, origin: ORIGIN, days }), {}, deps);
  const body = (await response.json()) as { closures_hazard?: unknown; route?: { coordinates: unknown }; days?: { leg: { coordinates: unknown[] } }[] };
  return { status: response.status, requests: sent.length, route: body.route?.coordinates, lastLeg: body.days?.at(-1)?.leg.coordinates.length,
    hazard: body.closures_hazard, eighthCarriesX: carries(sent[7]!, X_SEARCH), lastCarriesX: carries(sent.at(-1)!, xs.at(-1)!) };
}

function expected(where: Where, days: number) {
  const searchRe = where !== "last leg" && days <= 4;
  const legRe = where !== "search" && days <= (where === "both" ? 3 : 4);
  const crosses = [...(where !== "last leg" && !searchRe ? ["x"] : []), ...(where !== "search" && !legRe ? [where === "both" ? "x-leg" : "x"] : [])];
  return { status: 200, requests: 1 + 6 + days + (searchRe ? 1 : 0) + (legRe ? 1 : 0), route: where !== "last leg" && !searchRe ? DETOUR : ROAD,
    lastLeg: where !== "search" && !legRe ? 3 : 2, eighthCarriesX: where !== "last leg" && searchRe, lastCarriesX: where !== "search" && legRe,
    hazard: { state: "fresh", version: TEST_VERSION, fetched_at: NOW.toISOString(), dropped: dropped(where), ...(crosses.length > 0 ? { crosses } : {}) } };
}

describe("a paid trip re-requests the search and its legs only inside TRIP_UPSTREAM_COST (T-0286 C5, P-COST-04, P-SAFE-08)", () => {
  for (const where of WHERE) {
    for (const days of DAYS) {
      it(`/trip paid, crossing the dropped X on the ${where}, ${days} day(s): requests, route, last leg and hazard equal the row's`, async () => {
        expect(await run(where, days)).toEqual(expected(where, days));
      });
    }
  }
});

describe("meta: no trip cap row ignores its variant (T-0286)", () => {
  it("for each crossing, the four day counts expect four different answers; for each day count, the three crossings differ", () => {
    for (const where of WHERE) expect(new Set(DAYS.map((d) => JSON.stringify(expected(where, d)))).size).toEqual(4);
    for (const d of DAYS) expect(new Set(WHERE.map((w) => JSON.stringify(expected(w, d)))).size).toEqual(3);
  });
  it("the cap is reached, never passed: the most requests any row expects is 12", () => {
    expect(Math.max(...WHERE.flatMap((w) => DAYS.map((d) => expected(w, d).requests)))).toEqual(12);
  });
});
