#!/usr/bin/env node
/**
 * Mutation population for the /loop modules (T-0252 R10) - the same vitest-driven form T-0248 ruled for
 * planMutants.mjs, because touches: is services/api/ and check-mutate-population.py reads Sources/ and
 * services/etl/etl/ only.
 *
 *   node services/api/test/mutate/loopMutants.mjs                  run the population
 *   node services/api/test/mutate/loopMutants.mjs --prove-vacuity  every mutant must report MISSED with no tests
 *   node services/api/test/mutate/loopMutants.mjs --prove-floor    the floor refuses on its arms; runs no tests
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

const API = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const OUT = resolve(API, "..", "..", ".build", "mutate-loop");

export const MIN_MUTATIONS = 41;
export const SUBJECTS = ["src/retrace.ts", "src/loopRequest.ts", "src/loopPlanner.ts", "src/loop.ts", "src/upstream.ts"];
const TESTS = ["test/retraceParity.test.ts", "test/loopCost.test.ts", "test/loopShape.test.ts"];

const m = (id, file, find, replace) => ({ id, file: `src/${file}`, find, replace });
export const MUTATIONS = [
  m("retrace-radius-24", "retrace.ts", "RETRACE_RADIUS_METERS = 25.0;", "RETRACE_RADIUS_METERS = 24.0;"),
  m("retrace-heading-105", "retrace.ts", "OPPOSITE_HEADING_DEGREES = 150.0;", "OPPOSITE_HEADING_DEGREES = 105.0;"),
  m("retrace-max-014", "retrace.ts", "MAX_RETRACE_FRACTION = 0.15;", "MAX_RETRACE_FRACTION = 0.14;"),
  m("retrace-strict", "retrace.ts", "return fraction <= MAX_RETRACE_FRACTION;", "return fraction < MAX_RETRACE_FRACTION;"),
  m("retrace-one-sample", "retrace.ts", "SAMPLES_PER_CELL = 2.0;", "SAMPLES_PER_CELL = 1.0;"),
  m("retrace-no-wrap", "retrace.ts", "return d > 180 ? 360 - d : d;", "return d;"),
  m("retrace-steps-floor", "retrace.ts", "Math.max(1, Math.ceil(length", "Math.max(1, Math.floor(length"),
  m("retrace-sample-end", "retrace.ts", "const t = (i + 0.5) / steps;", "const t = (i + 1) / steps;"),
  m("retrace-radius-zero", "retrace.ts", "&& distanceMeters(seen.point, here) <= RETRACE_RADIUS_METERS));", "&& distanceMeters(seen.point, here) <= 0));"),
  m("retrace-no-range", "retrace.ts", "if (!(p.lat >= -90 && p.lat <= 90) ||", "if (false ||"),
  m("retrace-half-share", "retrace.ts", "retraced += share;", "retraced += share / 2;"),
  m("retrace-no-samples", "retrace.ts", "retracedSamples.push(here);", ""),
  m("retrace-earth", "retrace.ts", "EARTH_RADIUS_METERS = 6_371_008.8;", "EARTH_RADIUS_METERS = 6_371_000;"),
  m("retrace-zero-length", "retrace.ts", "if (!(Number.isFinite(length) && length > 0)) continue;", "if (!(Number.isFinite(length))) continue;"),
  m("request-min-5", "loopRequest.ts", "MIN_LOOP_MINUTES = 10;", "MIN_LOOP_MINUTES = 5;"),
  m("request-max-181", "loopRequest.ts", "MAX_LOOP_MINUTES = 180;", "MAX_LOOP_MINUTES = 181;"),
  m("request-any-key", "loopRequest.ts", "if (!allowed.includes(key)) return", "if (false) return"),
  m("request-min-zero", "loopRequest.ts", "minutes < MIN_LOOP_MINUTES ||", "minutes < 0 ||"),
  m("request-any-decimals", "loopRequest.ts", "if (!atMostTwoDecimals(value))", "if (false)"),
  m("planner-lambda-3", "loopPlanner.ts", "LOOP_LAMBDA = 2;", "LOOP_LAMBDA = 3;"),
  m("planner-veff-45", "loopPlanner.ts", "V_EFF_KMH = 40;", "V_EFF_KMH = 45;"),
  m("planner-cost-4", "loopPlanner.ts", "LOOP_UPSTREAM_COST = 3;", "LOOP_UPSTREAM_COST = 4;"),
  m("planner-clearance-200", "loopPlanner.ts", "START_CLEARANCE_M = 300;", "START_CLEARANCE_M = 200;"),
  m("planner-spacing-50", "loopPlanner.ts", "AREA_SPACING_M = 100;", "AREA_SPACING_M = 50;"),
  m("planner-half-side-40", "loopPlanner.ts", "AREA_HALF_SIDE_M = 30;", "AREA_HALF_SIDE_M = 40;"),
  m("planner-areas-5", "loopPlanner.ts", "MAX_LOOP_AREAS = 50;", "MAX_LOOP_AREAS = 5;"),
  m("planner-reseed-2", "loopPlanner.ts", "(seed + 1) >>> 0", "(seed + 2) >>> 0"),
  m("planner-areas-old-seed", "loopPlanner.ts", "current = await attempt(reseed, areas);", "current = await attempt(seed, areas);"),
  m("planner-worst-fraction", "loopPlanner.ts", "Math.min(...fractions)", "Math.max(...fractions)"),
  m("planner-fnv-prime", "loopPlanner.ts", "0x01000193", "0x01000197"),
  m("planner-seed-no-bar", "loopPlanner.ts", "fnv1a32(`${userId}|${day}`)", "fnv1a32(`${userId}${day}`)"),
  m("planner-two-points", "loopPlanner.ts", "points: [[start.lon, start.lat]],", "points: [[start.lon, start.lat], [start.lon, start.lat]],"),
  m("planner-no-round-trip", "loopPlanner.ts", "algorithm: \"round_trip\",", ""),
  m("planner-any-loop-clean", "loopPlanner.ts", "a.scan !== null && isAcceptable(a.scan.fraction)", "a.scan !== null"),
  m("planner-url-no-waypoints", "loopPlanner.ts", "appleMapsUrl(start, start, waypoints)", "appleMapsUrl(start, start, [])"),
  m("loop-kill-late", "loop.ts", "if (killed(env)) return json", "if (false) return json"),
  m("loop-plan-budget", "loop.ts", ", LOOP_UPSTREAM_COST);", ");"),
  m("loop-quota-503", "loop.ts", "resets_at: verdict.resetsAt }, 429)", "resets_at: verdict.resetsAt }, 503)"),
  m("loop-seed-epoch", "loop.ts", "dayKey(deps.upstream.now())", "dayKey(new Date(0))"),
  m("upstream-cap-12", "upstream.ts", "if (spent > budget) {", "if (spent > PLAN_UPSTREAM_COST) {"),
  m("upstream-reserve-12", "upstream.ts", "reserve(args.userId, budget, now);", "reserve(args.userId, PLAN_UPSTREAM_COST, now);"),
];

export const EQUIVALENT = [
  { id: "retrace-bbox-first", file: "src/retrace.ts", find: "if (p.lat < minLat) minLat = p.lat;",
    witness: "the grid is an INDEX: with the cell at twice the radius every pair within 25 m lies in the 3x3 neighbourhood "
      + "whatever the anchor, and the true haversine distance decides - so moving the anchor (and the mid-latitude of the "
      + "longitude scale by a fraction of a degree) cannot change a verdict or a fraction. RetraceDetector.swift records "
      + "the same: the bounding-box anchor is real but unpinned (T-0119 KNOWN_MISSED). Measured: MISSED in the first run." },
  { id: "planner-model-gate", file: "src/loopPlanner.ts", find: "if (problem !== null) throw new RouteError",
    witness: "the model is buildCustomModel(LOOP_LAMBDA, closures), which never names road_access or surface (customModel.ts "
      + "property 1), so rejectCustomModel returns null for every model this module can build. Defence in depth for P-SAFE-01." },
  { id: "loop-killed-again", file: "src/loop.ts", find: "killed: () => killed(env) || deps.upstream.killed()",
    witness: "handleLoop already returned 503 when killed(env); env cannot change within one request, so the re-check inside "
      + "guardedPlan sees false either way. It exists for the shape /plan has; the KILL tests pin the first check." },
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
  for (const x of MUTATIONS) {
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
  console.log(`RESULT caught=${tally.CAUGHT} missed=${tally.MISSED} trap=${tally.TRAP} of ${MUTATIONS.length}`);
  if (prove) return tally.MISSED === MUTATIONS.length ? 0 : 1;
  return tally.CAUGHT === MUTATIONS.length ? 0 : 1;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) process.exit(main(process.argv.slice(2)));
