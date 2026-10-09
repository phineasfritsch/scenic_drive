#!/usr/bin/env node
/**
 * Mutation population for the vehicle key of /plan, /loop and /trip (T-0311 R8) - planMutants.mjs's shape: the
 * enabled-profile whitelist (src/vehicle.ts) and the three parsers that read it. Killers: test/vehicleWire.test.ts and test/requiredKeys.test.ts.
 *
 *   node services/api/test/mutate/vehicleMutants.mjs                  run the population
 *   node services/api/test/mutate/vehicleMutants.mjs --prove-vacuity  every mutant must report MISSED with no tests
 *   node services/api/test/mutate/vehicleMutants.mjs --prove-floor    the floor refuses on its arms; runs no tests
 *   node services/api/test/mutate/vehicleMutants.mjs --only=a,b       run only the named entries (a fix round)
 *
 * WHAT COUNTS. CAUGHT only when vitest's JSON report names a FAILED test. A run that fails with no named
 * failure (a mutant that does not load) is a TRAP and does not count. An anchor that does not occur exactly
 * once is STALE and the run refuses before mutating anything. Pass condition: caught == MUTATIONS.length.
 * THE FLOOR is literal: MIN_MUTATIONS, and every SUBJECT is mutated by at least one entry. EQUIVALENT entries
 * carry a witness - the reason no test CAN tell them apart - and are never run.
 * The tree is checked clean (git status) before the first mutant and every file is restored in `finally`.
 */
import { spawnSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { onlyIds } from "./onlyIds.mjs";

const API = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const OUT = resolve(API, "..", "..", ".build", "mutate-vehicle");

export const MIN_MUTATIONS = 32;
export const SUBJECTS = ["src/vehicle.ts", "src/planRequest.ts", "src/loopRequest.ts", "src/tripRequest.ts"];
const TESTS = ["test/vehicleWire.test.ts", "test/requiredKeys.test.ts"];

const m = (id, file, find, replace) => ({ id, file: `src/${file}`, find, replace });
const CHECKED = "if (vehicle) return refuse(vehicle);";
const MATCH = "ENABLED_VEHICLE_PROFILES.includes(value)) return null;";
/** rv1-t0311 B1: each required key at each level of each parser, dropped from its required list one at a time. */
const LOOP_START = 'keysProblem(start, START_KEYS, START_KEYS, "start")';
const LOOP_TOP = 'REQUIRED_KEYS = ["start", "minutes"];';
const PLAN_TOP = '["origin", "destination", "budget_minutes"], "the body"';
const TRIP_TOP = 'REQUIRED_KEYS = ["origin", "destination", "days"];';
const ORIGIN_LEVEL = 'keysProblem(origin, ORIGIN_KEYS, ORIGIN_KEYS, "origin")';
const PLACE_LEVEL = 'keysProblem(destination, DESTINATION_KEYS, DESTINATION_KEYS, "destination")';
export const MUTATIONS = [
  m("vehicle-enables-rv", "vehicle.ts", '= ["standard"];', '= ["standard", "rv"];'),
  m("vehicle-absent-refused", "vehicle.ts", "if (value === undefined) return null;", "if (value === null) return null;"),
  m("vehicle-case-folded", "vehicle.ts", MATCH, "ENABLED_VEHICLE_PROFILES.includes(value.toLowerCase())) return null;"),
  m("vehicle-trimmed", "vehicle.ts", MATCH, "ENABLED_VEHICLE_PROFILES.includes(value.trim())) return null;"),
  m("vehicle-prefix", "vehicle.ts", MATCH, "ENABLED_VEHICLE_PROFILES.some((p) => value.startsWith(p))) return null;"),
  m("vehicle-detail-one-route", "vehicle.ts", "the only profile ${route} plans for", "the only profile /plan plans for"),
  m("plan-vehicle-unchecked", "planRequest.ts", CHECKED, "if (vehicle && false) return refuse(vehicle);"),
  m("plan-vehicle-key-dropped", "planRequest.ts", '"departs_at", "vehicle"]', '"departs_at"]'),
  m("loop-vehicle-unchecked", "loopRequest.ts", CHECKED, "if (vehicle && false) return refuse(vehicle);"),
  m("loop-vehicle-key-dropped", "loopRequest.ts", '"minutes", "vehicle"]', '"minutes"]'),
  m("loop-vehicle-required", "loopRequest.ts", 'REQUIRED_KEYS = ["start", "minutes"];', 'REQUIRED_KEYS = ["start", "minutes", "vehicle"];'),
  m("loop-vehicle-route", "loopRequest.ts", 'vehicleProblem(body.vehicle, "/loop")', 'vehicleProblem(body.vehicle, "/plan")'),
  m("trip-vehicle-unchecked", "tripRequest.ts", CHECKED, "if (vehicle && false) return refuse(vehicle);"),
  m("trip-vehicle-key-dropped", "tripRequest.ts", '"extra_budget_pct", "vehicle"]', '"extra_budget_pct"]'),
  m("trip-vehicle-route", "tripRequest.ts", 'vehicleProblem(body.vehicle, "/trip")', 'vehicleProblem(body.vehicle, "/loop")'),
  m("loop-start-required-none", "loopRequest.ts", LOOP_START, 'keysProblem(start, START_KEYS, [], "start")'),
  m("loop-start-lat-not-required", "loopRequest.ts", LOOP_START, 'keysProblem(start, START_KEYS, ["lon"], "start")'),
  m("loop-start-lon-not-required", "loopRequest.ts", LOOP_START, 'keysProblem(start, START_KEYS, ["lat"], "start")'),
  m("loop-minutes-not-required", "loopRequest.ts", LOOP_TOP, 'REQUIRED_KEYS = ["start"];'),
  m("loop-start-not-required", "loopRequest.ts", LOOP_TOP, 'REQUIRED_KEYS = ["minutes"];'),
  m("plan-origin-not-required", "planRequest.ts", PLAN_TOP, '["destination", "budget_minutes"], "the body"'),
  m("plan-destination-not-required", "planRequest.ts", PLAN_TOP, '["origin", "budget_minutes"], "the body"'),
  m("plan-budget-not-required", "planRequest.ts", PLAN_TOP, '["origin", "destination"], "the body"'),
  m("plan-origin-lat-not-required", "planRequest.ts", ORIGIN_LEVEL, 'keysProblem(origin, ORIGIN_KEYS, ["lon"], "origin")'),
  m("plan-origin-lon-not-required", "planRequest.ts", ORIGIN_LEVEL, 'keysProblem(origin, ORIGIN_KEYS, ["lat"], "origin")'),
  m("plan-place-not-required", "planRequest.ts", PLACE_LEVEL, 'keysProblem(destination, DESTINATION_KEYS, [], "destination")'),
  m("trip-origin-not-required", "tripRequest.ts", TRIP_TOP, 'REQUIRED_KEYS = ["destination", "days"];'),
  m("trip-destination-not-required", "tripRequest.ts", TRIP_TOP, 'REQUIRED_KEYS = ["origin", "days"];'),
  m("trip-days-not-required", "tripRequest.ts", TRIP_TOP, 'REQUIRED_KEYS = ["origin", "destination"];'),
  m("trip-origin-lat-not-required", "tripRequest.ts", ORIGIN_LEVEL, 'keysProblem(origin, ORIGIN_KEYS, ["lon"], "origin")'),
  m("trip-origin-lon-not-required", "tripRequest.ts", ORIGIN_LEVEL, 'keysProblem(origin, ORIGIN_KEYS, ["lat"], "origin")'),
  m("trip-place-not-required", "tripRequest.ts", PLACE_LEVEL, 'keysProblem(destination, DESTINATION_KEYS, [], "destination")'),
];

export const EQUIVALENT = [
  { id: "vehicle-any-type", file: "src/vehicle.ts", find: 'typeof value === "string" && ',
    witness: "Array.prototype.includes compares by SameValueZero, and ENABLED_VEHICLE_PROFILES holds strings only, so no "
      + "non-string value (null, number, boolean, array, object) is ever included: dropping the typeof test accepts nothing "
      + "more. It stays as the guard that names P-PRIV-05's reason (a non-string never rides)." },
];

export function floorRefusal(mutations = MUTATIONS, subjects = SUBJECTS) {
  if (mutations.length < MIN_MUTATIONS) return `population ${mutations.length} is below the floor ${MIN_MUTATIONS}`;
  for (const subject of subjects) {
    if (!mutations.some((x) => x.file === subject)) return `subject ${subject} has no mutation`;
  }
  return null;
}

function vitest(extra, tag) {
  mkdirSync(OUT, { recursive: true });
  const report = join(OUT, `${tag}.json`);
  writeFileSync(report, "");
  const bin = join(API, "node_modules", "vitest", "vitest.mjs");
  const run = spawnSync(process.execPath, [bin, "run", ...TESTS, "--reporter=json", `--outputFile=${report}`, ...extra],
    { cwd: API, encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
  let named = [];
  let total = 0;
  try {
    const parsed = JSON.parse(readFileSync(report, "utf8"));
    total = parsed.numTotalTests;
    for (const file of parsed.testResults) {
      for (const result of file.assertionResults) if (result.status === "failed") named.push(result.title);
    }
  } catch {
    named = [];
  }
  return { status: run.status, named, total };
}

function verdict(run) {
  if (run.named.length > 0) return "CAUGHT";
  return run.status === 0 ? "MISSED" : "TRAP";
}

function main(argv) {
  const only = onlyIds(argv, MUTATIONS.map((x) => x.id));
  if (argv.includes("--prove-floor")) {
    const arms = [
      ["empty table", floorRefusal([])],
      ["one short of the floor", floorRefusal(MUTATIONS.slice(0, MIN_MUTATIONS - 1))],
      ["a subject unmutated", floorRefusal(MUTATIONS.filter((x) => x.file !== "src/loopRequest.ts").concat(
        Array.from({ length: MIN_MUTATIONS }, () => MUTATIONS[0])))],
      ["a new subject with none", floorRefusal(MUTATIONS, [...SUBJECTS, "src/newModule.ts"])],
    ];
    for (const [arm, refusal] of arms) console.log(`prove-floor ${arm}: ${refusal === null ? "QUIET (WRONG)" : `REFUSED - ${refusal}`}`);
    const real = floorRefusal();
    console.log(`prove-floor real population: ${real === null ? "quiet" : `REFUSED - ${real}`}`);
    return arms.every(([, r]) => r !== null) && real === null ? 0 : 1;
  }

  const refusal = floorRefusal();
  if (refusal) { console.log(`REFUSING TO RUN: ${refusal}`); return 2; }
  for (const x of [...MUTATIONS, ...EQUIVALENT]) {
    const count = readFileSync(join(API, x.file), "utf8").split(x.find).length - 1;
    if (count !== 1) { console.log(`STALE ${x.id}: anchor occurs ${count} times in ${x.file}`); return 2; }
  }
  const dirty = spawnSync("git", ["status", "--porcelain", "--", "src"], { cwd: API, encoding: "utf8" });
  if (dirty.status !== 0 || dirty.stdout.trim() !== "") { console.log("REFUSING TO RUN: services/api/src is not clean"); return 2; }

  const chosen = only ? MUTATIONS.filter((x) => only.includes(x.id)) : MUTATIONS;
  const prove = argv.includes("--prove-vacuity");
  const extra = prove ? ["-t", "^no test is named this$", "--passWithNoTests"] : [];
  console.log(`population mutations=${MUTATIONS.length} (floor ${MIN_MUTATIONS}) equivalent=${EQUIVALENT.length} `
    + `subjects=${SUBJECTS.length} tests=${TESTS.length}${prove ? " PROVE-VACUITY" : ""}`);
  if (!prove) {
    const base = vitest([], "baseline");
    if (base.status !== 0 || base.total === 0) { console.log(`REFUSING: the baseline is not green (${base.named.join("; ")})`); return 2; }
    console.log(`baseline green tests=${base.total}`);
  }

  const tally = { CAUGHT: 0, MISSED: 0, TRAP: 0 };
  for (const x of chosen) {
    const path = join(API, x.file);
    const original = readFileSync(path, "utf8");
    let result;
    try {
      writeFileSync(path, original.replace(x.find, x.replace));
      result = vitest(extra, x.id);
    } finally {
      writeFileSync(path, original);
    }
    const v = verdict(result);
    tally[v] += 1;
    console.log(`${v.padEnd(6)} ${x.id}${result.named.length ? ` by "${result.named[0]}"` : ""}`);
  }
  console.log(`RESULT caught=${tally.CAUGHT} missed=${tally.MISSED} trap=${tally.TRAP} of ${chosen.length}${only ? " (--only)" : ""}`);
  if (prove) return tally.MISSED === chosen.length ? 0 : 1;
  return tally.CAUGHT === chosen.length ? 0 : 1;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) process.exit(main(process.argv.slice(2)));
