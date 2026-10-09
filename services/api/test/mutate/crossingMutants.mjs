#!/usr/bin/env node
/**
 * Mutation population for T-0286 (every returned path held to every stored closure): closuresCrossing.ts (the closed
 * segment-polygon predicate, a new numeric module), the picker's one re-request and swap in closuresNearest.ts, the
 * `crosses` hazard in closuresStore.ts, and the wiring and caps in plan/loop/trip and their planners. The vitest-driven
 * form of closuresMutants.mjs (that file is at 281 of 300 lines), the same rules:
 *
 *   node services/api/test/mutate/crossingMutants.mjs                  run the population
 *   node services/api/test/mutate/crossingMutants.mjs --prove-vacuity  every mutant must report MISSED with no tests
 *   node services/api/test/mutate/crossingMutants.mjs --prove-floor    the floor refuses on its arms; runs no tests
 *   ... --only=<id>,<id>                                                run only the named entries; an unknown id refuses
 *
 * CAUGHT only when vitest's JSON report names a FAILED test; a run failing with no named failure is a TRAP. An anchor
 * that does not occur exactly once is STALE and the run refuses before mutating anything. THE FLOOR is literal
 * (MIN_MUTATIONS) and every SUBJECT is mutated at least once. EQUIVALENT entries carry a witness and are never run.
 */
import { spawnSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const API = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const OUT = resolve(API, "..", "..", ".build", "mutate-crossing");

export const MIN_MUTATIONS = 59;
export const SUBJECTS = ["src/closuresCrossing.ts", "src/closuresNearest.ts", "src/closuresStore.ts", "src/plan.ts", "src/loop.ts",
  "src/trip.ts", "src/scenicPlanner.ts", "src/loopPlanner.ts", "src/tripPlanner.ts"];
const TESTS = ["test/closuresCrossing.test.ts", "test/closuresCrossingTrip.test.ts", "test/closuresCrossingGeometry.test.ts",
  "test/closuresNearest.test.ts", "test/closuresNearestRetry.test.ts", "test/closuresNearestPick.test.ts"];

const m = (id, file, find, replace) => ({ id, file: `src/${file}`, find, replace });
export const MUTATIONS = [
  m("cx-proper-off", "closuresCrossing.ts", "if (o1 * o2 < 0 && o3 * o4 < 0) return true;", ""),
  m("cx-proper-or", "closuresCrossing.ts", "o1 * o2 < 0 && o3 * o4 < 0", "o1 * o2 < 0 || o3 * o4 < 0"),
  m("cx-o1-off", "closuresCrossing.ts", "(o1 === 0 && within(a, c, d)) || ", ""),
  m("cx-o2-off", "closuresCrossing.ts", " || (o2 === 0 && within(b, c, d))", ""),
  m("cx-ring-ends-off", "closuresCrossing.ts", "\n    || (o3 === 0 && within(c, a, b)) || (o4 === 0 && within(d, a, b))", ""),
  m("cx-within-x-min-open", "closuresCrossing.ts", "Math.min(a[0]!, b[0]!) <= p[0]!", "Math.min(a[0]!, b[0]!) < p[0]!"),
  m("cx-within-x-max-open", "closuresCrossing.ts", "p[0]! <= Math.max(a[0]!, b[0]!)", "p[0]! < Math.max(a[0]!, b[0]!)"),
  m("cx-within-y-min-open", "closuresCrossing.ts", "Math.min(a[1]!, b[1]!) <= p[1]!", "Math.min(a[1]!, b[1]!) < p[1]!"),
  m("cx-within-y-max-open", "closuresCrossing.ts", "p[1]! <= Math.max(a[1]!, b[1]!)", "p[1]! < Math.max(a[1]!, b[1]!)"),
  m("cx-within-x-only", "closuresCrossing.ts", "\n  && Math.min(a[1]!, b[1]!) <= p[1]! && p[1]! <= Math.max(a[1]!, b[1]!)", ""),
  m("cx-sign-no-zero", "closuresCrossing.ts", "x > 0 ? 1 : x < 0 ? -1 : 0", "x > 0 ? 1 : -1"),
  m("cx-orient-plus", "closuresCrossing.ts", "(a[0]! - o[0]!) * (b[1]! - o[1]!) - (a[1]! - o[1]!)", "(a[0]! - o[0]!) * (b[1]! - o[1]!) + (a[1]! - o[1]!)"),
  m("cx-inside-off", "closuresCrossing.ts", "if (path.some((p) => insideRing(p, ring))) return true;", ""),
  m("cx-ring-closing-edge", "closuresCrossing.ts", "i + 1 < ring.length; i += 1) {\n      if (segmentsMeet", "i + 2 < ring.length; i += 1) {\n      if (segmentsMeet"),
  m("cx-first-segment-only", "closuresCrossing.ts", "const last = Math.max(1, path.length - 1);", "const last = 1;"),
  m("cx-last-segment-dropped", "closuresCrossing.ts", "Math.max(1, path.length - 1)", "Math.max(1, path.length - 2)"),
  m("cx-one-point-skipped", "closuresCrossing.ts", "Math.max(1, path.length - 1)", "Math.max(0, path.length - 1)"),
  m("cx-empty-crosses", "closuresCrossing.ts", "if (path.length === 0) return false;", "if (path.length === 0) return true;"),
  m("pk-cap-ignored", "closuresNearest.ts", "first.size === 0 || retry === null ? null", "first.size === 0 ? null"),
  m("pk-futile-off", "closuresNearest.ts", "swap.closures.features.every((f) => sent.has(f))", "false"),
  m("pk-swap-dropped-ignored", "closuresNearest.ts", "most = Math.max(most, swap.dropped);", ""),
  m("pk-reports-first", "closuresNearest.ts", "const kept = again === null ? first : crossed(coordinates(again));", "const kept = first;"),
  m("pk-returns-original", "closuresNearest.ts", "return again === null ? value : again;", "return value;"),
  m("pk-crosses-unsorted", "closuresNearest.ts", "[...left].sort((a, b) => a - b)", "[...left]"),
  m("pk-id-position-groups", "closuresNearest.ts", "position += features.length;", "position += 1;"),
  m("pk-id-lcs-ignored", "closuresNearest.ts", "const id = typeof index === \"string\" ? index : ", "const id = false ? index : "),
  m("pk-last-ring", "closuresNearest.ts", "pathCrossesRing(path, f.geometry.coordinates[0]!)", "pathCrossesRing(path, f.geometry.coordinates.at(-1)!)"),
  m("swap-crossers-skip", "closuresNearest.ts", "if (group.features.length > room) break;", "if (group.features.length > room) continue;"),
  m("swap-room-ge", "closuresNearest.ts", "if (group.features.length > room) break;", "if (group.features.length >= room) break;"),
  m("swap-others-first", "closuresNearest.ts", "[ranked.filter((g) => crossed.has(g.at)), ranked.filter((g) => !crossed.has(g.at))]",
    "[ranked.filter((g) => !crossed.has(g.at)), ranked.filter((g) => crossed.has(g.at))]"),
  m("swap-crossers-only", "closuresNearest.ts", ", ranked.filter((g) => !crossed.has(g.at))]", "]"),
  m("swap-dropped-zero", "closuresNearest.ts", ".flat();\n  return { closures: { type: \"FeatureCollection\", features }, dropped: ranked.length - kept.size };",
    ".flat();\n  return { closures: { type: \"FeatureCollection\", features }, dropped: 0 };"),
  m("store-crosses-ignored", "closuresStore.ts", "if (dropped === 0 && crosses.length === 0) return", "if (dropped === 0) return"),
  m("store-crosses-unreported", "closuresStore.ts", ", ...(crosses.length > 0 ? { crosses: [...crosses] } : {})", ""),
  m("store-crosses-always", "closuresStore.ts", "crosses.length > 0 ? { crosses", "true ? { crosses"),
  m("store-dropped-always", "closuresStore.ts", "...(dropped > 0 ? { dropped } : {})", "...({ dropped })"),
  m("plan-unchecked", "plan.ts", "picker.pick, picker.returned));", "picker.pick, async (v) => v));"),
  m("plan-crosses-unreported", "plan.ts", "picker.dropped(), picker.crosses())", "picker.dropped())"),
  m("loop-unchecked", "loop.ts", "seed, picker.pick, picker.returned),", "seed, picker.pick, async (v) => v),"),
  m("loop-crosses-unreported", "loop.ts", "picker.dropped(), picker.crosses())", "picker.dropped())"),
  m("trip-unchecked", "trip.ts", "who.tier === \"paid\", picker.pick, picker.returned)", "who.tier === \"paid\", picker.pick, async (v) => v)"),
  m("trip-crosses-unreported", "trip.ts", "picker.dropped(), picker.crosses())", "picker.dropped())"),
  m("plan-re-ceiling-unchecked", "scenicPlanner.ts", "return durationSeconds(again) <= ceiling && ", "return "),
  m("plan-re-overlap-unchecked", "scenicPlanner.ts", " && overlap(wayIds(again), wayIds(fastest)) < MAXIMUM_OVERLAP ? again", " ? again"),
  m("plan-re-lambda-0", "scenicPlanner.ts", "buildCustomModel(outcome.lambda, swapped)", "buildCustomModel(0, swapped)"),
  m("plan-re-corridor", "scenicPlanner.ts", "(p) => p.coordinates, origin, destination,", "(p) => p.coordinates, origin, origin,"),
  m("loop-cap-ignored", "loopPlanner.ts", "tried.length + 1 <= LOOP_UPSTREAM_COST ?", "true ?"),
  m("loop-cap-strict", "loopPlanner.ts", "tried.length + 1 <= LOOP_UPSTREAM_COST ?", "tried.length + 1 < LOOP_UPSTREAM_COST ?"),
  m("loop-re-unchecked", "loopPlanner.ts", "return clean(again) ? again : null;", "return again;"),
  m("loop-re-reseeded", "loopPlanner.ts", "await attempt(shown.seed, swapped);", "await attempt((shown.seed + 1) >>> 0, swapped);"),
  m("loop-re-corridor", "loopPlanner.ts", "(a) => a.path.coordinates, start, start,", "(a) => a.path.coordinates, start, { lat: start.lat - 1, lon: start.lon },"),
  m("trip-search-reserve-ignored", "tripPlanner.ts", "used + 1 + (full ? days : 0) <= TRIP_UPSTREAM_COST", "used + 1 <= TRIP_UPSTREAM_COST"),
  m("trip-preview-reserves", "tripPlanner.ts", "(full ? days : 0)", "days"),
  m("trip-leg-reserve-ignored", "tripPlanner.ts", "used + 1 + after <= TRIP_UPSTREAM_COST", "used + 1 <= TRIP_UPSTREAM_COST"),
  m("trip-search-re-unchecked", "tripPlanner.ts", "return \"plan\" in again.split ? again : null;", "return again;"),
  m("trip-leg-re-unchecked", "tripPlanner.ts", "return again.timeMs > ceiling ? null : again;", "return again;"),
  m("trip-re-lambda-0", "tripPlanner.ts", "buildCustomModel(outcome.lambda, swapped)))", "buildCustomModel(0, swapped)))"),
  m("trip-leg-re-corridor", "tripPlanner.ts", "return returned(legPath, (p) => p.coordinates, from, to,",
    "return returned(legPath, (p) => p.coordinates, origin, destination,"),
  m("trip-fastest-uncounted", "tripPlanner.ts", "const fastest = await route(counted, routerBase,", "const fastest = await route(call, routerBase,"),
];

export const EQUIVALENT = [
  { id: "cx-inside-flip", file: "src/closuresCrossing.ts", find: "p[0]! < a[0]! + ",
    witness: "Counting the ring's crossings to the LEFT of p instead of the right: a horizontal line meets a closed ring an "
      + "even number of times, so the two parities agree for every p off the boundary; on the boundary they may differ, and "
      + "there segmentsMeet decides (every boundary point is on an edge), so pathCrossesRing's verdict is unchanged. Seen "
      + "MISSED by the whole population on 2026-10-06, as the witness says." },
  { id: "cx-o3-alone-off", file: "src/closuresCrossing.ts", find: " || (o3 === 0 && within(c, a, b))",
    witness: "In a CLOSED ring (buildCustomModel refuses an unclosed one, so the store never holds one) every position is the "
      + "start c of one edge and the end d of the edge before it; a ring position lying on a path segment is therefore also "
      + "found by the o4 branch on the previous edge. Removing BOTH is cx-ring-ends-off, caught by the tangent-corner case." },
  { id: "cx-o4-alone-off", file: "src/closuresCrossing.ts", find: " || (o4 === 0 && within(d, a, b))",
    witness: "The mirror of cx-o3-alone-off: a ring position is the end d of one edge and the start c of the next." },
  { id: "plan-cap-ignored", file: "src/scenicPlanner.ts", find: "used + 1 <= PLAN_UPSTREAM_COST ?",
    witness: "A plan makes 1 fastest + at most MAX_EVALUATIONS (6) scenic requests before the check, so used + 1 <= 8 < 12 "
      + "always: the condition is never false. It stays as the ruled cap (C5) so a later MAX_EVALUATIONS cannot pass 12." },
  { id: "pk-empty-crossers-swapped", file: "src/closuresNearest.ts", find: "first.size === 0 || retry",
    witness: "With no crossed closure the swap is the ranked prefix of every closure that fits 50 - exactly the sent set - "
      + "so the futile test returns the value unchanged and records nothing, the same as the short-circuit." },
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
      ["a subject unmutated", floorRefusal(MUTATIONS.filter((x) => x.file !== "src/trip.ts").concat(
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
