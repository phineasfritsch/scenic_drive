/**
 * T-0340 A1/A2: /trip and /loop answers carry the route's hazard runs, through the shipping handlers, compared WHOLE.
 *
 * The expected runs are written out here by hand (R1): a preview day reads the chosen route's runs clipped to the
 * day's point span, indexed into route.coordinates; a full day reads its own leg's runs, indexed into the leg.
 */
import { describe, expect, it } from "vitest";
import { FRESH_EMPTY } from "./closuresFake";
import { handleLoop } from "../src/loop";
import type { Tier } from "../src/quota";
import { ROUTE_DETAILS } from "../src/scenicPlanner";
import { handleTrip, type TripDeps } from "../src/trip";
import { BIG_SUR, EDGE_M, EDGES, expectedTrip, NOW, ROAD, ROUTER, SCENIC_EDGE_MS, TRIP_BODY, tripCounters, tripPath,
  tripRequest, tripRouter } from "./tripHarness";
import { LOOP_BODY, loopHarness, loopRequest, squareLoop } from "./loopHarness";

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
