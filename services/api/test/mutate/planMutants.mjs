#!/usr/bin/env node
/**
 * Mutation population for the /plan modules (T-0248 R9) - the vitest-driven equivalent of an ops/mutate/
 * driver, because T-0248's touches: is services/api/ and check-mutate-population.py reads Sources/ and
 * services/etl/etl/ only.
 *
 *   node services/api/test/mutate/planMutants.mjs                  run the population
 *   node services/api/test/mutate/planMutants.mjs --prove-vacuity  every mutant must report MISSED with no tests
 *   node services/api/test/mutate/planMutants.mjs --prove-floor    the floor refuses on its arms; runs no tests
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
const OUT = resolve(API, "..", "..", ".build", "mutate-plan");

export const MIN_MUTATIONS = 43;
export const SUBJECTS = ["src/lambdaSearch.ts", "src/planRequest.ts", "src/routePath.ts", "src/planWaypoints.ts",
  "src/appleMaps.ts", "src/hazards.ts", "src/scenicPlanner.ts", "src/plan.ts"];
const TESTS = ["test/lambdaSearch.test.ts", "test/appleMaps.test.ts", "test/planRecorded.test.ts",
  "test/planPrivacy.test.ts", "test/planCost.test.ts", "test/planCeiling.test.ts", "test/planWaypoints.test.ts"];

const m = (id, file, find, replace) => ({ id, file: `src/${file}`, find, replace });
export const MUTATIONS = [
  m("search-ceiling-strict", "lambdaSearch.ts", "if (duration <= ceiling && (best", "if (duration < ceiling && (best"),
  m("search-keeps-shorter", "lambdaSearch.ts", "duration > best.duration ||", "duration < best.duration ||"),
  m("search-tie-smaller", "lambdaSearch.ts", "lambda > best.lambda))", "lambda < best.lambda))"),
  m("search-bracket-strict", "lambdaSearch.ts", "if (duration <= ceiling) lo = mid;", "if (duration < ceiling) lo = mid;"),
  m("search-tolerance", "lambdaSearch.ts", "LAMBDA_TOLERANCE = 0.05", "LAMBDA_TOLERANCE = 0.1"),
  m("search-mid-third", "lambdaSearch.ts", "lo + (hi - lo) / 2", "lo + (hi - lo) / 3"),
  m("search-one-extra", "lambdaSearch.ts", "evaluations < cap &&", "evaluations <= cap &&"),
  m("search-zero-budget", "lambdaSearch.ts", "budget === 0 ||", "budget === 1 ||"),
  m("search-used-strict", "lambdaSearch.ts", "winner.duration >= fastest + MIN", "winner.duration > fastest + MIN"),
  m("search-mono-equal", "lambdaSearch.ts", "b.duration < a.duration", "b.duration <= a.duration"),
  m("search-zero-fastest", "lambdaSearch.ts", "!(fastest > 0)", "!(fastest >= 0)"),
  m("search-max-lambda", "lambdaSearch.ts", "MAX_LAMBDA = 8;", "MAX_LAMBDA = 7;"),
  m("request-four-dp", "planRequest.ts", "ORIGIN_DECIMALS = 2;", "ORIGIN_DECIMALS = 4;"),
  m("request-any-key", "planRequest.ts", "if (!allowed.includes(key))", "if (!allowed.includes(key) && false)"),
  m("request-budget-181", "planRequest.ts", "MAX_BUDGET_MINUTES = 180;", "MAX_BUDGET_MINUTES = 181;"),
  m("request-budget-negative", "planRequest.ts", "minutes < 0 ||", "minutes < -1 ||"),
  m("request-lat-range", "planRequest.ts", "value > limit)", "value > limit + 1)"),
  m("request-place-length", "planRequest.ts", "place.length > MAX_PLACE_ID_LENGTH", "place.length >= MAX_PLACE_ID_LENGTH"),
  m("request-instant-rollover", "planRequest.ts", "const same = date.getUTCFullYear()", "const same = true || date.getUTCFullYear()"),
  m("route-empty-differs", "routePath.ts", "if (union.size === 0) return 1;", "if (union.size === 0) return 0;"),
  m("route-overlap-07", "routePath.ts", "MAXIMUM_OVERLAP = 0.6;", "MAXIMUM_OVERLAP = 0.7;"),
  m("route-shared-inverted", "routePath.ts", "if (b.has(id)) shared", "if (!b.has(id)) shared"),
  m("route-seconds", "routePath.ts", "path.timeMs / 1000", "path.timeMs / 1001"),
  m("pins-shortest-first", "planWaypoints.ts", ": b.meters - a.meters))", ": a.meters - b.meters))"),
  m("pins-closed-run", "planWaypoints.ts", "index < run.to) return", "index <= run.to) return"),
  m("pins-unsorted", "planWaypoints.ts", ".map((row) => row.fromIndex)\n    .sort((a, b) => a - b);", ".map((row) => row.fromIndex);"),
  m("pins-merge-roads", "planWaypoints.ts", "previous.highway === highway &&", "true &&"),
  m("pins-limit-8", "planWaypoints.ts", "MAX_WAYPOINTS = 9;", "MAX_WAYPOINTS = 8;"),
  m("url-round-toward-up", "appleMaps.ts", "Math.sign(product) * Math.round(Math.abs(product))", "Math.round(product)"),
  m("url-nine-refused", "appleMaps.ts", "waypoints.length > MAX_WAYPOINTS", "waypoints.length >= MAX_WAYPOINTS"),
  m("url-six-dp", "appleMaps.ts", "COORDINATE_DECIMALS = 5;", "COORDINATE_DECIMALS = 6;"),
  m("hazard-asphalt", "hazards.ts", "[\"asphalt\", ", "["),
  m("hazard-case", "hazards.ts", "run.value.toLowerCase()", "run.value"),
  m("hazard-access-yes", "hazards.ts", "[\"yes\", \"missing\"]", "[\"missing\"]"),
  m("planner-seven-scenic", "scenicPlanner.ts", "MAX_EVALUATIONS = 6;", "MAX_EVALUATIONS = 7;"),
  m("planner-other-model", "scenicPlanner.ts", "SCENIC_PROFILE, buildCustomModel(lambda, null)", "SCENIC_PROFILE, buildCustomModel(Math.min(8, lambda + 0.25), null)"),
  m("planner-ceiling-plus", "scenicPlanner.ts", "fastestSeconds + budgetSeconds;", "fastestSeconds + budgetSeconds + 1;"),
  m("planner-overlap-inclusive", "scenicPlanner.ts", "!(shared < MAXIMUM_OVERLAP)", "!(shared <= MAXIMUM_OVERLAP)"),
  m("planner-no-way-ids", "scenicPlanner.ts", "\"osm_way_id\", ...HAZARD_DETAILS", "...HAZARD_DETAILS"),
  m("plan-kill-true", "killSwitch.ts", "if (env.KILL === \"1\") return true;", "if (env.KILL === \"true\") return true;"),
  m("plan-kill-late", "plan.ts", "if (paused) return", "if (false) return"),
  m("plan-hours", "plan.ts", "request.budgetMinutes * 60", "request.budgetMinutes * 3600"),
  m("plan-quota-503", "plan.ts", "resets_at: verdict.resetsAt }, 429)", "resets_at: verdict.resetsAt }, 503)"),
];

export const EQUIVALENT = [
  { id: "planner-ceiling-guard", file: "src/scenicPlanner.ts", find: "if (!(eta <= ceiling))",
    witness: "chosen is the measured route at outcome.lambda, and searchLambda returns only a measured duration <= the "
      + "same ceiling; bisection lambdas are distinct at formatMultiplier's 6 dp, so no second route shares the key. "
      + "Defence in depth - searchLambda's own ceiling mutants (search-ceiling-strict etc.) are the observable ones." },
  { id: "search-cap-floor", file: "src/lambdaSearch.ts", find: "Math.max(1, maxEvaluations)",
    witness: "lambda 0 is evaluated before the loop, so a cap of 0 and a cap of 1 both stop after one evaluation." },
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
      ["a subject unmutated", floorRefusal(MUTATIONS.filter((x) => x.file !== "src/hazards.ts").concat(
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
