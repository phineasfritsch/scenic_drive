/**
 * T-0286 C5 on a PAID trip (full view, through handleTrip with paid deps - no shipped identity reaches paid): the
 * search's chosen route and each day leg are held to every stored closure, and a re-request is made only inside
 * TRIP_UPSTREAM_COST (12) - the search reserves `days` legs, a leg the legs after it. The search makes 1 fastest + 6
 * scenic requests (measured, T-0282), so a re-request fits exactly when 1 + 6 + 1 + days <= 12, i.e. days <= 4; two
 * fit when days <= 3. Rows: where a path crosses a dropped X (the search's detour / the last leg / both the search and
 * the FIRST leg, which must leave room for the legs after it) x days 2..5, the router honouring X (a request carrying
 * X is answered clear). Every expectation is a function of its row; each re-request's areas equal C4's swap for ITS
 * OWN corridor, recomputed here by removal.
 */
import { describe, expect, it } from "vitest";
import { nearestClosures, polygonDistance2 } from "../src/closuresNearest";
import type { ClosureSnapshot } from "../src/closuresStore";
import { buildCustomModel, type ClosureCollection } from "../src/customModel";
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
const ne = (i: number): [number, number] => [ROAD[i]![0] + 0.3, ROAD[i]![1] + 0.3];
/** The search's detour: road vertex 20 moved 0.3 degrees north-east; X_SEARCH sits on the middle of the edge 19 -> 20'. */
const D20 = ne(20);
const DETOUR = ROAD.map((p, i) => (i === 20 ? D20 : p));
const X_SEARCH = square("x", { lon: (ROAD[19]![0] + D20[0]) / 2, lat: (ROAD[19]![1] + D20[1]) / 2 });
/** A leg's detour runs through its X's centre, 0.3 degrees north-east of road vertex 36 (last leg) or 0 (first leg). */
const X_LAST = square("x", { lon: ne(36)[0], lat: ne(36)[1] });
const X_FIRST = square("x-leg", { lon: ne(0)[0], lat: ne(0)[1] });
/** 100 squares far nearer every corridor than any X: 50 due south of the origin, 50 due south of road vertex 36. */
const NEAR = [...south("o", at(0)), ...south("l", at(36))];

type Where = "search" | "last leg" | "both";
const WHERE: Where[] = ["search", "last leg", "both"];
/** From 2: a one-day leg IS the search chord (origin -> destination) and this router tells them apart by chord. */
const DAYS = [2, 3, 4, 5];
const xsOf = (where: Where) => (where === "search" ? [X_SEARCH] : where === "last leg" ? [X_LAST] : [X_SEARCH, X_FIRST]);
const carries = (body: Record<string, unknown>, x: Feature) =>
  JSON.stringify((body.custom_model as { areas?: unknown } | undefined)?.areas ?? null).includes(JSON.stringify(x.geometry.coordinates));
const fc = (features: Feature[]) => ({ type: "FeatureCollection", features }) as ClosureCollection;
const plane = (p: Pt) => [p.lon * 91961, p.lat * 110946] as const;
/** C4 by removal over the stored set, for the corridor from -> to: the farthest sent out until x fits, x in. */
function swapAreas(stored: Feature[], points: number[][], x: Feature) {
  const [from, to] = points.map(([lon, lat]) => ({ lon: lon!, lat: lat! })) as [Pt, Pt];
  const d = (f: Feature) => polygonDistance2(plane(from), plane(to), f);
  const kept = (nearestClosures(fc(stored), from, to).closures!.features as Feature[]).slice()
    .sort((a, b) => d(b) - d(a) || stored.indexOf(b) - stored.indexOf(a));
  while (kept.length + 1 > 50) kept.shift();
  return buildCustomModel(0, fc([...kept, x].sort((a, b) => stored.indexOf(a) - stored.indexOf(b)))).areas;
}

async function run(where: Where, days: number, legReMs = 1000) {
  const xs = xsOf(where);
  const stored = [...NEAR, ...xs];
  const snapshot: ClosureSnapshot = { version: TEST_VERSION, closures: fc(stored), hazard: null, fetchedAt: NOW.toISOString() };
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
    const leg = where === "last leg" ? JSON.stringify(points[1]) === JSON.stringify(ROAD[40])
      : where === "both" && JSON.stringify(points[0]) === JSON.stringify(ROAD[0]);
    if (leg && carries(body, xs.at(-1)!)) return new Response(tripPath([points[0]!, points[1]!], legReMs));
    return new Response(tripPath(leg ? [points[0]!, where === "both" ? ne(0) : ne(36), points[1]!] : [points[0]!, points[1]!], 1000));
  };
  const deps = {
    upstream: { counters: tripCounters([]).counters, fetchImpl, now: () => NOW, killed: () => false },
    routerBase: ROUTER,
    resolvePlace: async (id: string) => (id === BIG_SUR.id ? { lat: BIG_SUR.lat, lon: BIG_SUR.lon } : null),
    identify: () => ({ userId: "device-1", tier: "paid" as const }),
    closures: async () => snapshot,
  };
  const response = await handleTrip(tripRequest({ ...TRIP_BODY, origin: ORIGIN, days }), {}, deps);
  const body = (await response.json()) as { closures_hazard?: unknown; route?: { coordinates: unknown }; days?: { leg: { coordinates: number[][] } }[] };
  const leg = where === "both" ? body.days?.[0]?.leg.coordinates : body.days?.at(-1)?.leg.coordinates;
  const re = sent.flatMap((b, i) => (i > 0 && JSON.stringify(b.points) === JSON.stringify(sent[i - 1]!.points) && xs.some((x) => carries(b, x))
    ? [{ points: b.points as number[][], areas: (b.custom_model as { areas?: unknown }).areas, x: xs.find((x) => carries(b, x))! }] : []));
  return {
    got: { status: response.status, requests: sent.length, route: body.route?.coordinates, legPoints: leg?.length,
      legEnd: where === "both" ? leg?.[0] : leg?.at(-1), hazard: body.closures_hazard,
      reOf: re.map((r) => (JSON.stringify(r.points) === JSON.stringify(sent[0]!.points) ? "search" : "leg")) },
    re: re.map((r) => r.areas), reOracle: re.map((r) => swapAreas(stored, r.points, r.x)), rePoints: re.map((r) => JSON.stringify(r.points)),
  };
}

function expected(where: Where, days: number, legRejected = false) {
  const searchRe = where !== "last leg" && days <= 4;
  const legRe = where !== "search" && days <= (where === "both" ? 3 : 4);
  const legShown = where !== "search" && (!legRe || legRejected);
  const crosses = [...(where !== "last leg" && !searchRe ? ["x"] : []), ...(legShown ? [where === "both" ? "x-leg" : "x"] : [])];
  return { status: 200, requests: 1 + 6 + days + (searchRe ? 1 : 0) + (legRe ? 1 : 0), route: where !== "last leg" && !searchRe ? DETOUR : ROAD,
    legPoints: legShown ? 3 : 2, legEnd: where === "both" ? ROAD[0] : ROAD[40], reOf: [...(searchRe ? ["search"] : []), ...(legRe ? ["leg"] : [])],
    hazard: { state: "fresh", version: TEST_VERSION, fetched_at: NOW.toISOString(), dropped: where === "both" ? 52 : 51,
      ...(crosses.length > 0 ? { crosses } : {}) } };
}

describe("a paid trip re-requests the search and its legs only inside TRIP_UPSTREAM_COST (T-0286 C5, P-COST-04, P-SAFE-08)", () => {
  for (const where of WHERE) {
    for (const days of DAYS) {
      it(`/trip paid, crossing the dropped X on the ${where}, ${days} day(s): requests, route, the leg, hazard and each re-request's swap equal the row's`, async () => {
        const r = await run(where, days);
        expect([r.got, r.re]).toEqual([expected(where, days), r.reOracle]);
        if (where !== "last leg" && days <= 4) expect(r.rePoints[0]).toEqual(JSON.stringify([[ORIGIN.lon, ORIGIN.lat], [BIG_SUR.lon, BIG_SUR.lat]]));
      });
    }
  }
  it("/trip paid, the last leg's re-request over its day ceiling: not shown; the crossing leg returned, X named", async () => {
    const r = await run("last leg", 2, 99_000_000);
    expect([r.got, r.re]).toEqual([expected("last leg", 2, true), r.reOracle]);
  });
});

describe("meta: no trip cap row ignores its variant (T-0286)", () => {
  it("for each crossing, the four day counts expect four different answers; for each day count, the three crossings differ", () => {
    for (const where of WHERE) expect(new Set(DAYS.map((d) => JSON.stringify(expected(where, d)))).size).toEqual(4);
    for (const d of DAYS) expect(new Set(WHERE.map((w) => JSON.stringify(expected(w, d)))).size).toEqual(3);
    expect(JSON.stringify(expected("last leg", 2, true))).not.toEqual(JSON.stringify(expected("last leg", 2)));
  });
  it("the cap is reached, never passed: the most requests any row expects is 12", () => {
    expect(Math.max(...WHERE.flatMap((w) => DAYS.map((d) => expected(w, d).requests)))).toEqual(12);
  });
});
