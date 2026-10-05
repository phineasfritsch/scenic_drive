#!/usr/bin/env node
/**
 * Mutation population for POST /isochrone (T-0262 R9): the request whitelist and the bucket arithmetic, the one
 * GraphHopper request and the reading of its answer, the daily reach cache's key and lifetime, the handler's order,
 * the surprise allowance, the QuotaCounter's absent-means-0 surprise count and the Surprise.pick reach conversion.
 * The vitest-driven form T-0248 ruled for planMutants.mjs (T-0252, T-0256 copied it), because touches: is
 * services/api/ and check-mutate-population.py reads Sources/ and services/etl/etl/ only.
 *
 *   node services/api/test/mutate/isochroneMutants.mjs                  run the population
 *   node services/api/test/mutate/isochroneMutants.mjs --prove-vacuity  every mutant must report MISSED with no tests
 *   node services/api/test/mutate/isochroneMutants.mjs --prove-floor    the floor refuses on its arms; runs no tests
 *   ... --only=<id>,<id>                                                 run only the named entries (a round re-runs
 *                                                                        what it touched); an unknown id refuses
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
const OUT = resolve(API, "..", "..", ".build", "mutate-isochrone");

export const MIN_MUTATIONS = 57;
export const SUBJECTS = ["src/isochroneRequest.ts", "src/isochronePlanner.ts", "src/reachCache.ts", "src/surpriseReach.ts",
  "src/isochrone.ts", "src/quota.ts", "src/QuotaCounter.ts"];
const TESTS = ["test/isochroneCost.test.ts", "test/isochroneShape.test.ts", "test/quotaCounter.test.ts"];

const m = (id, file, find, replace) => ({ id, file: `src/${file}`, find, replace });
export const MUTATIONS = [
  m("req-min-29", "isochroneRequest.ts", "MIN_REACH_MINUTES = 30;", "MIN_REACH_MINUTES = 29;"),
  m("req-max-241", "isochroneRequest.ts", "MAX_REACH_MINUTES = 240;", "MAX_REACH_MINUTES = 241;"),
  m("req-bucket-10", "isochroneRequest.ts", "BUCKET_MINUTES = 15;", "BUCKET_MINUTES = 10;"),
  m("req-any-key", "isochroneRequest.ts", "if (!allowed.includes(key)) return", "if (false) return"),
  m("req-key-missing-ok", "isochroneRequest.ts", "if (!(key in value)) return", "if (false) return"),
  m("req-any-decimals", "isochroneRequest.ts", "if (!atMostTwoDecimals(value))", "if (false)"),
  m("req-lat-180", "isochroneRequest.ts", "coordinateProblem(start.lat, \"lat\", 90)", "coordinateProblem(start.lat, \"lat\", 180)"),
  m("req-limit-round", "isochroneRequest.ts", "Math.floor(minutes / 2 / BUCKET_MINUTES)", "Math.round(minutes / 2 / BUCKET_MINUTES)"),
  m("req-limit-one-way", "isochroneRequest.ts", "minutes / 2 / BUCKET_MINUTES", "minutes / BUCKET_MINUTES"),
  m("plan-profile-scenic", "isochronePlanner.ts", "ISOCHRONE_PROFILE = \"car_fast\";", "ISOCHRONE_PROFILE = \"car_scenic\";"),
  m("plan-cost-2", "isochronePlanner.ts", "ISOCHRONE_UPSTREAM_COST = 1;", "ISOCHRONE_UPSTREAM_COST = 2;"),
  m("plan-minutes-not-seconds", "isochronePlanner.ts", "time_limit: String(limit * 60)", "time_limit: String(limit)"),
  m("plan-point-lon-lat", "isochronePlanner.ts", "point: `${start.lat.toFixed(2)},${start.lon.toFixed(2)}`",
    "point: `${start.lon.toFixed(2)},${start.lat.toFixed(2)}`"),
  m("plan-point-3dp", "isochronePlanner.ts", "point: `${start.lat.toFixed(2)}", "point: `${start.lat.toFixed(3)}"),
  m("plan-no-reverse-flow", "isochronePlanner.ts", "reverse_flow: \"false\",", ""),
  m("plan-buckets-plus-one", "isochronePlanner.ts", "buckets: String(limit / BUCKET_MINUTES)", "buckets: String(limit / BUCKET_MINUTES + 1)"),
  m("plan-method-post", "isochronePlanner.ts", "{ method: \"GET\" }", "{ method: \"POST\" }"),
  m("plan-status-ignored", "isochronePlanner.ts", "if (!response.ok) throw", "if (false) throw"),
  m("plan-array-order", "isochronePlanner.ts", "byBucket.get(i)!", "byBucket.get(count - 1 - i)!"),
  m("plan-duplicate-ok", "isochronePlanner.ts", " || byBucket.has(bucket)) {", ") {"),
  m("plan-bucket-high", "isochronePlanner.ts", "bucket >= count ||", "bucket > count ||"),
  m("plan-bucket-negative", "isochronePlanner.ts", "bucket < 0 ||", "false ||"),
  m("plan-any-geometry", "isochronePlanner.ts", "g?.type !== \"Polygon\" ||", "!g ||"),
  m("plan-empty-polygon", "isochronePlanner.ts", "|| g.coordinates.length === 0) return null;", ") return null;"),
  m("plan-ring-three", "isochronePlanner.ts", "value.length < 4) return null;", "value.length < 3) return null;"),
  m("plan-ring-infinite", "isochronePlanner.ts", "|| !Number.isFinite(lon) || !Number.isFinite(lat)) return null;", ") return null;"),
  m("plan-count-short", "isochronePlanner.ts", "if (byBucket.size !== count) throw", "if (false) throw"),
  m("plan-not-json-plain-error", "isochronePlanner.ts", "throw new ReachError(\"the router answer is not JSON\");",
    "throw new Error(\"the router answer is not JSON\");"),
  m("plan-minutes-from-zero", "isochronePlanner.ts", "const minutes = (i + 1) * BUCKET_MINUTES;", "const minutes = i * BUCKET_MINUTES;"),
  m("reach-one-way", "surpriseReach.ts", "return 2 * oneWayMinutes;", "return oneWayMinutes;"),
  m("reach-holes-ignored", "surpriseReach.ts", "|| holes.some((hole) => inRing(hole, point))) continue;", ") continue;"),
  m("reach-largest", "surpriseReach.ts", "bucket.round_trip_minutes < best", "bucket.round_trip_minutes > best"),
  m("reach-ray-vertex", "surpriseReach.ts", "yi > point.lat !== yj > point.lat", "yi >= point.lat !== yj > point.lat"),
  m("cache-key-no-day", "reachCache.ts", "|${dayKey(now)}|", "|"),
  m("cache-key-no-version", "reachCache.ts", "|${graphVersion}`", "`"),
  m("cache-key-no-limit", "reachCache.ts", "toFixed(2)}|${limit}|", "toFixed(2)}|"),
  m("cache-key-lat-1dp", "reachCache.ts", "return `${start.lat.toFixed(2)}", "return `${start.lat.toFixed(1)}"),
  m("cache-key-lon-1dp", "reachCache.ts", "${start.lon.toFixed(2)}|${limit}|", "${start.lon.toFixed(1)}|${limit}|"),
  m("cache-ttl-zero", "reachCache.ts", "max-age=${secondsToNextDay(now)}", "max-age=0"),
  m("cache-ttl-units", "reachCache.ts", "now.getTime()) / 1000)", "now.getTime()) / 100)"),
  m("iso-kill-late", "isochrone.ts", "if (await killSwitch(env)) return json", "if (false) return json"),
  m("iso-method-any", "isochrone.ts", "if (req.method !== \"POST\") return json({ error: \"POST only\" }, 405);", ""),
  m("iso-deps-before-whitelist", "isochrone.ts", "let raw: unknown;",
    "if (deps === null) return json({ error: \"planning_unavailable\" }, 503);\n  let raw: unknown;"),
  m("iso-kind-plan", "isochrone.ts", "kind: \"surprise\" }", "kind: \"plan\" }"),
  m("iso-plan-budget", "isochrone.ts", ", ISOCHRONE_UPSTREAM_COST);", ");"),
  m("iso-hit-ignored", "isochrone.ts", "if (cached !== null) return json", "if (false) return json"),
  m("iso-no-put", "isochrone.ts", "await deps.cache.put(key, buckets, now)", "await Promise.resolve()"),
  m("iso-key-minutes", "isochrone.ts", "reachCacheKey(start, limit, now,", "reachCacheKey(start, minutes, now,"),
  m("iso-hit-echoes-limit", "isochrone.ts", "json({ minutes, buckets: cached }, 200)", "json({ minutes: limit, buckets: cached }, 200)"),
  m("iso-quota-503", "isochrone.ts", "resets_at: verdict.resetsAt }, 429)", "resets_at: verdict.resetsAt }, 503)"),
  m("iso-one-graph", "isochrone.ts", "env.GRAPH_VERSION.length > 0 ? env.GRAPH_VERSION :", "env.GRAPH_VERSION.length > 0 ? \"one-graph\" :"),
  m("quota-surprise-anon-4", "quota.ts", "DAILY_SURPRISE_QUOTA = { anon: 3, free: 3,", "DAILY_SURPRISE_QUOTA = { anon: 4, free: 3,"),
  m("quota-surprise-free-4", "quota.ts", "DAILY_SURPRISE_QUOTA = { anon: 3, free: 3,", "DAILY_SURPRISE_QUOTA = { anon: 3, free: 4,"),
  m("quota-surprise-paid-201", "quota.ts", "free: 3, paid: DAILY_PLAN_QUOTA.paid }", "free: 3, paid: 201 }"),
  m("quota-surprise-is-plan", "quota.ts", "if (kind === \"surprise\") return DAILY_SURPRISE_QUOTA[tier];", ""),
  m("do-surprise-absent-one", "QuotaCounter.ts", "(record[kind] as number) : 0;", "(record[kind] as number) : 1;"),
  m("do-used-ignores-record", "QuotaCounter.ts", "return kind in record ?", "return false ?"),
];

export const EQUIVALENT = [
  { id: "reach-ray-flip", file: "src/surpriseReach.ts", find: "point.lon < ((xj - xi)",
    witness: "even-odd parity does not depend on the ray's direction: a ray cast west from a point crosses a closed ring's "
      + "edges as many times mod 2 as a ray cast east (the two together cross every edge spanning the point's latitude, "
      + "and a closed ring spans it an even number of times), so flipping the comparison flips no verdict off the "
      + "boundary. Measured: MISSED in the first full run (T-0262 Log)." },
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
      ["a subject unmutated", floorRefusal(MUTATIONS.filter((x) => x.file !== "src/surpriseReach.ts").concat(
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
  const only = argv.find((a) => a.startsWith("--only="))?.slice("--only=".length).split(",") ?? null;
  const unknown = (only ?? []).filter((id) => !MUTATIONS.some((x) => x.id === id));
  if (only !== null && (only.length === 0 || unknown.length > 0)) { console.log(`REFUSING: unknown --only id(s) ${unknown.join(",")}`); return 2; }
  const run = only === null ? MUTATIONS : MUTATIONS.filter((x) => only.includes(x.id));
  const extra = prove ? ["-t", "^no test is named this$", "--passWithNoTests"] : [];
  console.log(`population mutations=${MUTATIONS.length} (floor ${MIN_MUTATIONS}) equivalent=${EQUIVALENT.length} `
    + `subjects=${SUBJECTS.length} tests=${TESTS.length}${prove ? " PROVE-VACUITY" : ""}${only ? ` ONLY=${run.length}` : ""}`);
  if (!prove) {
    const base = vitest([], "baseline");
    if (base.status !== 0 || base.total === 0) { console.log(`REFUSING: the baseline is not green (${base.named.join("; ")})`); return 2; }
    console.log(`baseline green tests=${base.total}`);
  }

  const tally = { CAUGHT: 0, MISSED: 0, TRAP: 0 };
  for (const x of run) {
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
  console.log(`RESULT caught=${tally.CAUGHT} missed=${tally.MISSED} trap=${tally.TRAP} of ${run.length}`);
  if (prove) return tally.MISSED === run.length ? 0 : 1;
  return tally.CAUGHT === run.length ? 0 : 1;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) process.exit(main(process.argv.slice(2)));
