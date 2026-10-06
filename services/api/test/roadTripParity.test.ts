/**
 * The TS half of the shared road-trip fixture (T-0268 R6). Tests/Fixtures/t0268/trips.json is read here AND by
 * Tests/ScenicKitTests/RoadTripParityTests.swift; both assert every case's WHOLE outcome by full equality against
 * the same recorded answer (T-0249 R8, carried by hand in make-trips.mjs). Two green suites over one file = the
 * Worker's port and the Swift original give identical day plans.
 */
import { describe, expect, it } from "vitest";
import { budgetSeconds, planRoadTrip, type RoadTripEdge, type RoadTripPlace } from "../src/roadTrip";
import tripsRaw from "../../../Tests/Fixtures/t0268/trips.json?raw";

interface SharedTrips {
  route: { start: [number, number]; end: [number, number]; seconds: number; meters: number }[];
  places: { name: string; kind: "stop" | "lodging"; score: number; coordinate: [number, number] }[];
  cases: { name: string; days: number; max_drive_s: number; max_m: number; fastest_s: number; expected: unknown }[];
}

const trips = JSON.parse(tripsRaw) as SharedTrips;
const at = ([lat, lon]: [number, number]) => ({ lat, lon });
const edgesOf = (route: SharedTrips["route"]): RoadTripEdge[] =>
  route.map((e) => ({ start: at(e.start), end: at(e.end), seconds: e.seconds, meters: e.meters }));
const placesOf = (list: SharedTrips["places"]): RoadTripPlace[] =>
  list.map((p) => ({ name: p.name, kind: p.kind, score: p.score, coordinate: at(p.coordinate) }));
const edges = edgesOf(trips.route);
const places = placesOf(trips.places);

describe("the shared road-trip fixture (T-0268 R6)", () => {
  it("carries the T-0249 route, its places and every outcome kind", () => {
    expect([edges.length, places.length, trips.cases.length, trips.synthetic.length]).toEqual([21, 20, 9, 2]);
    const kinds = trips.cases.map((c) => Object.keys(c.expected as object)[0]);
    expect([...new Set(kinds)].sort()).toEqual(["over_budget", "plan", "too_few_days"]);
  });

  it("every shared case gives the recorded day plan, whole, from the Worker's port", () => {
    const actual = trips.cases.map((c) => [c.name, planRoadTrip(edges, places, c.fastest_s,
      { days: c.days, maxDriveSeconds: c.max_drive_s, maxMeters: c.max_m })]);
    expect(actual).toEqual(trips.cases.map((c) => [c.name, c.expected]));
  });

  it("every synthetic case gives the recorded day plan, whole, from the Worker's port", () => {
    const actual = trips.synthetic.map((c) => [c.name, planRoadTrip(edgesOf(c.route), placesOf(c.places), c.fastest_s,
      { days: c.days, maxDriveSeconds: c.max_drive_s, maxMeters: c.max_m })]);
    expect(actual).toEqual(trips.synthetic.map((c) => [c.name, c.expected]));
  });

  it("the port's default percent is the plan's +40%: the A case without a percent is the A case", () => {
    const a = trips.cases[0]!;
    expect(planRoadTrip(edges, places, a.fastest_s, { days: a.days, maxDriveSeconds: a.max_drive_s, maxMeters: a.max_m }))
      .toEqual(a.expected);
    expect([budgetSeconds(20_411), budgetSeconds(20_410), budgetSeconds(20_411, 39), budgetSeconds(99, 40)])
      .toEqual([8_164, 8_164, 7_960, 39]);
  });

  it("the port's percent (R2, TS only): 39 floors 20_411 x 39 / 100 to 7_960; 0 makes the fastest the ceiling", () => {
    const a = trips.cases[0]!;
    const limits = { days: a.days, maxDriveSeconds: a.max_drive_s, maxMeters: a.max_m };
    expect([planRoadTrip(edges, places, 20_411, limits, 39), planRoadTrip(edges, places, 28_575, limits, 0),
      planRoadTrip(edges, places, 28_574, limits, 0)]).toEqual([{ over_budget: { route_s: 28_575, ceiling_s: 28_371 } },
      a.expected, { over_budget: { route_s: 28_575, ceiling_s: 28_574 } }]);
  });

  it("an empty route is an empty plan, and an over-budget route is refused before the days are looked at", () => {
    expect(planRoadTrip([], places, 1, { days: 0, maxDriveSeconds: 0, maxMeters: 0 })).toEqual({ plan: [] });
    expect(planRoadTrip(edges, places, 1, { days: 0, maxDriveSeconds: 0, maxMeters: 0 }))
      .toEqual({ over_budget: { route_s: 28_575, ceiling_s: 1 } });
  });
});
