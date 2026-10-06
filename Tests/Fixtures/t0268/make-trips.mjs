#!/usr/bin/env node
/**
 * Writes trips.json, the shared road-trip parity fixture (T-0268 R6), from Tests/Fixtures/roadtrip/*.tsv (T-0249 R7)
 * and the cases below. The EXPECTED outcomes are T-0249 R8's hand-derived plans (the literals of
 * Tests/ScenicKitTests/RoadTrip/RoadTripPlanTests.swift), carried here by hand - never computed by either port - plus
 * a days-0 case. Every case runs at the plan's +40% (the Swift original's fixed budget); the port's percent parameter
 * (R2) is held by the TS suite alone. Both suites read trips.json and assert full equality:
 *   Tests/ScenicKitTests/RoadTripParityTests.swift  (the Swift original)
 *   services/api/test/roadTripParity.test.ts        (the Worker's port)
 *
 *   node Tests/Fixtures/t0268/make-trips.mjs
 */
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const tsv = (name) => readFileSync(join(HERE, "..", "roadtrip", name), "utf8").split("\n")
  .filter((line) => line.length > 0 && !line.startsWith("#")).map((line) => line.replace(/\r$/, "").split("\t"));

const route = tsv("route.tsv").map((f) => ({ from: f[0], to: f[1], start: [Number(f[2]), Number(f[3])],
  end: [Number(f[4]), Number(f[5])], seconds: Number(f[6]), meters: Number(f[7]) }));
const places = tsv("places.tsv").map((f) => ({ name: f[0], kind: f[1], score: Number(f[2]),
  coordinate: [Number(f[3]), Number(f[4])] }));

const day = (n, s, e, seconds, meters, stops, overnight) =>
  ({ day: n, start_vertex: s, end_vertex: e, seconds, meters, stops, overnight });
const lodging = (name, meters) => ({ lodging: { name, meters } });

const planA = [
  day(1, 0, 9, 10_543, 219_014, ["Malibu Lagoon", "Point Mugu Rock", "Carpinteria Bluffs", "Stearns Wharf"], "no_lodging"),
  day(2, 9, 16, 8_881, 192_169, ["Solvang", "Pismo Pier", "Morro Rock", "Moonstone Beach"], lodging("Cambria Pines Lodge", 946)),
  day(3, 16, 21, 9_151, 128_092, ["Elephant Seal Vista", "Limekiln Falls"], null),
];
const planB = [
  day(1, 0, 6, 7_263, 137_008, ["Malibu Lagoon", "Point Mugu Rock", "Ventura Pier", "Carpinteria Bluffs"], lodging("Summerland Inn", 14_405)),
  day(2, 6, 12, 6_276, 156_896, ["Stearns Wharf", "Gaviota Overlook", "Solvang"], "no_lodging"),
  day(3, 12, 18, 8_811, 158_240, ["Pismo Pier", "Morro Rock", "Moonstone Beach", "Elephant Seal Vista"], "no_lodging"),
  day(4, 18, 21, 6_225, 87_131, ["Limekiln Falls"], null),
];
const shortened = [
  planB[0], planB[1],
  day(3, 12, 17, 7_059, 133_710, ["Pismo Pier", "Morro Rock", "Moonstone Beach", "Elephant Seal Vista"], lodging("San Simeon Motel", 0)),
  day(4, 17, 21, 7_977, 111_661, ["Limekiln Falls"], null),
];

const c = (name, days, max_drive_s, max_m, fastest_s, expected) => ({ name, days, max_drive_s, max_m, fastest_s, expected });
const cases = [
  c("A: 3 days at 4 h and 200 mi", 3, 14_400, 321_869, 20_411, { plan: planA }),
  c("B: 4 days at 2.5 h and 100 mi, miles binding", 4, 9_000, 160_934, 20_411, { plan: planB }),
  c("C: 3 days at 2.5 h is too few, stopped at Lucia", 3, 9_000, 321_869, 20_411, { too_few_days: { days: 3, reached_vertex: 20 } }),
  c("budget: fastest 20_410 is over the ceiling 28_574", 3, 14_400, 321_869, 20_410, { over_budget: { route_s: 28_575, ceiling_s: 28_574 } }),
  c("metres inclusive: B at exactly 158_240 m is B", 4, 9_000, 158_240, 20_411, { plan: planB }),
  c("metres inclusive: 158_239 m ends day 3 at San Simeon", 4, 9_000, 158_239, 20_411, { plan: shortened }),
  c("seconds inclusive: B at exactly 8_811 s is B", 4, 8_811, 160_934, 20_411, { plan: planB }),
  c("seconds inclusive: 8_810 s ends day 3 at San Simeon", 4, 8_810, 160_934, 20_411, { plan: shortened }),
  c("days 0 reach nothing", 0, 14_400, 321_869, 20_411, { too_few_days: { days: 0, reached_vertex: 0 } }),
];

// SYNTHETIC routes for the rules the T-0249 route never reaches (T-0268 mutation run at 441c274: corridor 4_000,
// share-empty-day, nearest-ties-high and day1-no-v0 were MISSED). Equator vertices 0.5 deg (~55.6 km) apart; expected
// derived by hand from T-0249 R4/R5/R6.
const edge = (a, b, seconds, meters) => ({ start: a, end: b, seconds, meters });
const v = (lon) => [0, lon];
const stop = (name, score, coordinate) => ({ name, kind: "stop", score, coordinate });
const synthetic = [
  { name: "uneven edges: day 2 starts past its share and still drives an edge; v0 belongs to day 1; 4.5 km is corridor",
    // total 120 s, 3 days: day 1 takes 10 (30 < 120), then 100 (330 >= 120); day 2 starts at cumulative 110 (330 >=
    // 240) but holds no edge yet, so it takes the last; day 3 has nothing left. Near V1 is ~4_503 m north of v1.
    route: [edge(v(0), v(0.5), 10, 1_000), edge(v(0.5), v(1), 100, 1_000), edge(v(1), v(1.5), 10, 1_000)],
    places: [stop("At Start", 50, v(0)), stop("Near V1", 40, [0.0405, 0.5])],
    days: 3, max_drive_s: 1_000, max_m: 100_000, fastest_s: 120,
    expected: { plan: [day(1, 0, 2, 110, 2_000, ["At Start", "Near V1"], "no_lodging"), day(2, 2, 3, 10, 1_000, [], null)] } },
  { name: "a stop equidistant from two vertices is the lower vertex's: it stays on day 1",
    // v1 and v2 are one point (a zero-length edge). Total 40 s, 2 days: day 1 ends after its first edge (40 >= 40).
    route: [edge(v(0), v(0.5), 20, 1_000), edge(v(0.5), v(0.5), 10, 0), edge(v(0.5), v(1), 10, 1_000)],
    places: [stop("Twin", 10, v(0.5))],
    days: 2, max_drive_s: 1_000, max_m: 100_000, fastest_s: 40,
    expected: { plan: [day(1, 0, 1, 20, 1_000, ["Twin"], "no_lodging"), day(2, 1, 3, 20, 1_000, [], null)] } },
  { name: "one unit short of the even share is short: day 1 at cumulative x days = day x total - 1 takes the next edge",
    // T-0268 pre-review survivor share-tie-lookahead (>= day x total - 1). Total 3_999 ms, 2 days: after the first
    // edge 1_999 x 2 = 3_998 = 1 x 3_999 - 1 < 3_999, so day 1 drives on; after the second 2_999 x 2 >= 3_999 ends it.
    route: [edge(v(0), v(0.5), 1_999, 1_000), edge(v(0.5), v(1), 1_000, 1_000), edge(v(1), v(1.5), 1_000, 1_000)],
    places: [],
    days: 2, max_drive_s: 100_000, max_m: 100_000, fastest_s: 3_999,
    expected: { plan: [day(1, 0, 2, 2_999, 2_000, [], "no_lodging"), day(2, 2, 3, 1_000, 1_000, [], null)] } },
];

const fixture = {
  source: "Tests/Fixtures/roadtrip/{route,places}.tsv (T-0249 R7); expected = T-0249 R8 by hand (T-0268 R6)",
  unit: "coordinates [lat, lon] degrees; seconds; metres",
  route, places, cases, synthetic,
};
writeFileSync(join(HERE, "trips.json"), `${JSON.stringify(fixture, null, 1)}\n`);
console.log(`trips.json: ${route.length} edges, ${places.length} places, ${cases.length} cases, ${synthetic.length} synthetic`);
