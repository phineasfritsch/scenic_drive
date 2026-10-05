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

const fixture = {
  source: "Tests/Fixtures/roadtrip/{route,places}.tsv (T-0249 R7); expected = T-0249 R8 by hand (T-0268 R6)",
  unit: "coordinates [lat, lon] degrees; seconds; metres",
  route, places, cases,
};
writeFileSync(join(HERE, "trips.json"), `${JSON.stringify(fixture, null, 1)}\n`);
console.log(`trips.json: ${route.length} edges, ${places.length} places, ${cases.length} cases`);
