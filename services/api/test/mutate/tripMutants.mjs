#!/usr/bin/env node
/**
 * Mutation population for the /trip modules (T-0268 R9) - the vitest-driven form T-0248 ruled for planMutants.mjs and
 * T-0252 for loopMutants.mjs, because touches: is services/api/ and check-mutate-population.py reads Sources/ and
 * services/etl/etl/ only.
 *
 *   node services/api/test/mutate/tripMutants.mjs                  run the population
 *   node services/api/test/mutate/tripMutants.mjs --prove-vacuity  every mutant must report MISSED with no tests
 *   node services/api/test/mutate/tripMutants.mjs --prove-floor    the floor refuses on its arms; runs no tests
 *   node services/api/test/mutate/tripMutants.mjs --only a,b       run only the named mutations (a later round's re-run)
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
const OUT = resolve(API, "..", "..", ".build", "mutate-trip");

export const MIN_MUTATIONS = 91;
export const SUBJECTS = ["src/roadTrip.ts", "src/tripRequest.ts", "src/tripPlanner.ts", "src/trip.ts", "src/tripPlaces.ts",
  "migrations/0009_trip_places.sql"];
const TESTS = ["test/roadTripParity.test.ts", "test/tripRequest.test.ts", "test/tripRoute.test.ts", "test/tripFull.test.ts",
  "test/killSwitchRoutes.test.ts", "test/tripPlaces.test.ts"];

const m = (id, file, find, replace) => ({ id, file: `src/${file}`, find, replace });
export const MUTATIONS = [
  m("split-percent-41", "roadTrip.ts", "BUDGET_PERCENT = 40;", "BUDGET_PERCENT = 41;"),
  m("split-corridor-4000", "roadTrip.ts", "CORRIDOR_METERS = 5_000;", "CORRIDOR_METERS = 4_000;"),
  m("split-stops-3", "roadTrip.ts", "MAX_STOPS_PER_DAY = 4;", "MAX_STOPS_PER_DAY = 3;"),
  m("split-overnight-14000", "roadTrip.ts", "OVERNIGHT_RADIUS_METERS = 15_000;", "OVERNIGHT_RADIUS_METERS = 14_000;"),
  m("split-earth", "roadTrip.ts", "EARTH_RADIUS_METERS = 6_371_008.8;", "EARTH_RADIUS_METERS = 6_370_000;"),
  m("split-budget-ceil", "roadTrip.ts", "Math.floor((fastestSeconds * percent) / 100)", "Math.ceil((fastestSeconds * percent) / 100)"),
  m("split-share-strict", "roadTrip.ts", "cumulative * limits.days >= day * total", "cumulative * limits.days > day * total"),
  m("split-share-tie-lookahead", "roadTrip.ts", "cumulative * limits.days >= day * total)", "cumulative * limits.days >= day * total - 1)"),
  m("split-share-empty-day", "roadTrip.ts", "if (index > start && cumulative", "if (cumulative"),
  m("split-drive-exclusive", "roadTrip.ts", "seconds + edge.seconds > limits.maxDriveSeconds", "seconds + edge.seconds >= limits.maxDriveSeconds"),
  m("split-metres-exclusive", "roadTrip.ts", "meters + edge.meters > limits.maxMeters", "meters + edge.meters >= limits.maxMeters"),
  m("split-nearest-ties-high", "roadTrip.ts", "if (meters < bestMeters) {", "if (meters <= bestMeters) {"),
  m("split-day1-no-v0", "roadTrip.ts", "const first = start === 0 ? 0 : start + 1;", "const first = start + 1;"),
  m("split-boundary-to-next", "roadTrip.ts", "c.vertex >= first && c.vertex <= end", "c.vertex >= first && c.vertex < end"),
  m("split-score-ascending", "roadTrip.ts", "? b.place.score - a.place.score", "? a.place.score - b.place.score"),
  m("split-all-stops", "roadTrip.ts", "ranked.slice(0, MAX_STOPS_PER_DAY)", "ranked"),
  m("split-rank-order", "roadTrip.ts", "    .sort((a, b) => (a.vertex !== b.vertex ? a.vertex - b.vertex : byName(a.place.name, b.place.name)))\n", ""),
  m("split-overnight-farthest", "roadTrip.ts", "best.meters < meters ||", "best.meters > meters ||"),
  m("split-overnight-radius-exclusive", "roadTrip.ts", "if (!(meters <= OVERNIGHT_RADIUS_METERS)) continue;", "if (!(meters < OVERNIGHT_RADIUS_METERS)) continue;"),
  m("split-overnight-floor", "roadTrip.ts", "Math.round(best.meters)", "Math.floor(best.meters)"),
  m("split-over-budget-inclusive", "roadTrip.ts", "if (total > ceiling) return", "if (total >= ceiling) return"),
  m("split-last-day-night", "roadTrip.ts", "overnight: index === spans.length - 1 ? null :", "overnight: index === spans.length ? null :"),
  m("split-empty-route", "roadTrip.ts", "if (edges.length === 0) return { plan: [] };", ""),
  m("split-lodging-is-stop", "roadTrip.ts", "if (place.kind !== \"stop\") continue;", ""),
  m("request-max-days-6", "tripRequest.ts", "MAX_TRIP_DAYS = 5;", "MAX_TRIP_DAYS = 6;"),
  m("request-min-days-0", "tripRequest.ts", "MIN_TRIP_DAYS = 1;", "MIN_TRIP_DAYS = 0;"),
  m("request-pct-41", "tripRequest.ts", "MAX_EXTRA_BUDGET_PCT = 40;", "MAX_EXTRA_BUDGET_PCT = 41;"),
  m("request-any-key", "tripRequest.ts", "if (!allowed.includes(key)) return", "if (false) return"),
  m("request-any-decimals", "tripRequest.ts", "if (!atMostTwoDecimals(value))", "if (false)"),
  m("request-fractions", "tripRequest.ts", "return Number.isInteger(value) &&", "return typeof value === \"number\" &&"),
  m("request-pct-floor-minus-1", "tripRequest.ts", "if (!wholeIn(pct, 0, MAX_EXTRA_BUDGET_PCT))", "if (!wholeIn(pct, -1, MAX_EXTRA_BUDGET_PCT))"),
  m("request-no-lower-coordinate", "tripRequest.ts", "if (value < -limit || value > limit)", "if (value > limit)"),
  m("request-default-pct-30", "tripRequest.ts", "let extraBudgetPct = MAX_EXTRA_BUDGET_PCT;", "let extraBudgetPct = 30;"),
  m("request-days-optional", "tripRequest.ts", "const REQUIRED_KEYS = [\"origin\", \"destination\", \"days\"];", "const REQUIRED_KEYS = [\"origin\", \"destination\"];"),
  m("request-any-place", "tripRequest.ts", "place.length > MAX_PLACE_ID_LENGTH || !PLACE_ID.test(place)", "place.length > MAX_PLACE_ID_LENGTH"),
  m("planner-cost-11", "tripPlanner.ts", "TRIP_UPSTREAM_COST = 12;", "TRIP_UPSTREAM_COST = 11;"),
  m("planner-drive-minus-1", "tripPlanner.ts", "MAX_DRIVE_MS_PER_DAY = 21_600_000;", "MAX_DRIVE_MS_PER_DAY = 21_599_999;"),
  m("planner-metres-minus-1", "tripPlanner.ts", "MAX_METERS_PER_DAY = 482_803;", "MAX_METERS_PER_DAY = 482_802;"),
  m("planner-details-more", "tripPlanner.ts", "TRIP_DETAILS = [\"time\", \"distance\"];", "TRIP_DETAILS = [\"time\", \"distance\", \"road_class\"];"),
  m("planner-search-7", "tripPlanner.ts", "}, MAX_EVALUATIONS);", "}, MAX_EVALUATIONS + 1);"),
  m("planner-pct-ignored", "tripPlanner.ts", "budgetSeconds(fastestMs, extraBudgetPct);", "budgetSeconds(fastestMs);"),
  m("planner-leg-ceiling-exclusive", "tripPlanner.ts", "if (legPath.timeMs > ceiling)", "if (legPath.timeMs >= ceiling)"),
  m("planner-legs-always", "tripPlanner.ts", "    if (full) {\n", "    if (true) {\n"),
  m("planner-day-ceiling-fastest", "tripPlanner.ts", "dayCeilingMs(ceilingMs, day.seconds, totalMs)", "dayCeilingMs(fastestMs, day.seconds, totalMs)"),
  m("planner-day-ceiling-ceil", "tripPlanner.ts", "(BigInt(ceilingMs) * BigInt(dayMs)) / BigInt(totalMs)",
    "(BigInt(ceilingMs) * BigInt(dayMs) + BigInt(totalMs) - 1n) / BigInt(totalMs)"),
  m("planner-split-pct-dropped", "tripPlanner.ts", "maxMeters: MAX_METERS_PER_DAY }, extraBudgetPct) };", "maxMeters: MAX_METERS_PER_DAY }) };"),
  m("planner-split-pct-constant", "tripPlanner.ts", "maxMeters: MAX_METERS_PER_DAY }, extraBudgetPct) };", "maxMeters: MAX_METERS_PER_DAY }, 40) };"),
  m("planner-budget-pct-constant", "tripPlanner.ts", "budgetSeconds(fastestMs, extraBudgetPct);", "budgetSeconds(fastestMs, 10);"),
  m("planner-budget-ceil", "tripPlanner.ts", "const budgetMs = budgetSeconds(fastestMs, extraBudgetPct);",
    "const budgetMs = Math.ceil((fastestMs * extraBudgetPct) / 100);"),
  m("planner-day-ceiling-float-ceil", "tripPlanner.ts", "return Number((BigInt(ceilingMs) * BigInt(dayMs)) / BigInt(totalMs));",
    "return Math.ceil((ceilingMs * dayMs) / totalMs);"),
  m("planner-day-check-trip-ceiling", "tripPlanner.ts", "if (legPath.timeMs > ceiling) {", "if (legPath.timeMs > ceilingMs) {"),
  m("planner-tile-no-start", "tripPlanner.ts", "if (run.from !== at || ", "if ("),
  m("planner-tile-empty-run", "tripPlanner.ts", "run.to <= run.from || ", ""),
  m("planner-tile-distance-edges", "tripPlanner.ts", "d.from !== run.from || d.to !== run.to", "false"),
  m("planner-negative-time", "tripPlanner.ts", "(run.value as number) < 0 || ", ""),
  m("planner-negative-distance", "tripPlanner.ts", " ||\n      !Number.isFinite(d.value) || d.value < 0) {", " ||\n      !Number.isFinite(d.value)) {"),
  m("planner-distance-floor", "tripPlanner.ts", "Math.round(distances[i]!.value as number)", "Math.floor(distances[i]!.value as number)"),
  m("planner-zero-time", "tripPlanner.ts", "if (edges.every((e) => e.seconds === 0))", "if (false)"),
  m("planner-runs-short", "tripPlanner.ts", "if (at !== last) throw", "if (at > last) throw"),
  m("planner-night-always", "tripPlanner.ts", "TripOvernight | null => o === null ? null\n", "TripOvernight | null => false ? null\n"),
  m("planner-full-eta-total", "tripPlanner.ts", "if (full) etaMs = 0;", ""),
  m("trip-kind-plan", "trip.ts", "{ ...who, kind: \"trip\" }", "{ ...who, kind: \"plan\" }"),
  m("trip-free-full", "trip.ts", "who.tier === \"paid\"", "who.tier !== \"anon\""),
  m("trip-no-kill", "trip.ts", "  if (paused) return json({ error: \"planning_paused\" }, 503);\n  if (req.method", "  if (req.method"),
  m("trip-reserve-13", "trip.ts", "), TRIP_UPSTREAM_COST);", "), 13);"),
  // T-0316: the server's trip_places rows reach the splitter, and the wire tells searched from not searched.
  m("places-dropped", "tripPlanner.ts", "planRoadTrip(pathEdges, places ?? [], fastestMs,", "planRoadTrip(pathEdges, [], fastestMs,"),
  m("places-searched-always-false", "tripPlanner.ts", "places_searched: places !== null,", "places_searched: false,"),
  m("places-searched-always-true", "tripPlanner.ts", "places_searched: places !== null,", "places_searched: true,"),
  m("places-failure-claims-searched", "tripPlanner.ts", "places === null ? { kind: \"not_searched\" } : ", ""),
  m("places-lodging-as-no-lodging", "tripPlanner.ts", "o === \"no_lodging\" ? { kind: \"no_lodging\" }", "true ? { kind: \"no_lodging\" }"),
  m("places-lodging-meters-dropped", "tripPlanner.ts", "name: o.lodging.name, meters: o.lodging.meters }", "name: o.lodging.name, meters: 0 }"),
  m("places-not-read", "trip.ts", "places = await deps.tripPlaces();", "places = [];"),
  m("places-failure-rethrown", "trip.ts", "  } catch {\n    places = null;\n  }", "  } catch (e) {\n    throw e;\n  }"),
  m("places-deps-empty", "trip.ts", "tripPlaces: d1TripPlaces(env.DB)", "tripPlaces: async () => []"),
  m("places-query-lodging-only", "tripPlaces.ts", "lon FROM trip_places\";", "lon FROM trip_places WHERE kind = 'lodging'\";"),
  m("places-lat-lon-swapped", "tripPlaces.ts", "coordinate: { lat: r.lat, lon: r.lon }", "coordinate: { lat: r.lon, lon: r.lat }"),
  m("places-score-ignored", "tripPlaces.ts", "score: r.score,", "score: 0,"),
  { id: "table-no-lat-low", file: "migrations/0009_trip_places.sql", find: "CHECK (lat >= -90 AND ", replace: "CHECK (" },
  { id: "table-no-lat-high", file: "migrations/0009_trip_places.sql", find: " AND lat <= 90)", replace: ")" },
  { id: "table-no-lon-low", file: "migrations/0009_trip_places.sql", find: "CHECK (lon >= -180 AND ", replace: "CHECK (" },
  { id: "table-no-lon-high", file: "migrations/0009_trip_places.sql", find: " AND lon <= 180)", replace: ")" },
  { id: "table-any-kind", file: "migrations/0009_trip_places.sql", find: " CHECK (kind IN ('stop', 'lodging'))", replace: "" },
  { id: "table-any-score", file: "migrations/0009_trip_places.sql", find: " CHECK (typeof(score) = 'integer')", replace: "" },
  { id: "table-empty-name", file: "migrations/0009_trip_places.sql", find: " AND length(name) >= 1", replace: "" },
  { id: "table-extra-column", file: "migrations/0009_trip_places.sql", find: "  lon REAL NOT NULL", replace: "  device TEXT,\n  lon REAL NOT NULL" },
  m("places-query-bound", "tripPlaces.ts", "db.prepare(TRIP_PLACES_QUERY).all", "db.prepare(TRIP_PLACES_QUERY).bind().all"),
  m("places-read-before-kill", "trip.ts", "  const paused = await killSwitch(env);\n",
    "  await deps?.tripPlaces().catch(() => null);\n  const paused = await killSwitch(env);\n"),
  // T-0316 review round 1 (B1, B2, B3, R-c).
  m("split-corridor-exclusive", "roadTrip.ts", "if (bestMeters <= CORRIDOR_METERS)", "if (bestMeters < CORRIDOR_METERS)"),
  m("split-overnight-tie-late-name", "roadTrip.ts", "best.meters === meters && best.name < lodging.name",
    "best.meters === meters && best.name > lodging.name"),
  { id: "table-name-any-type", file: "migrations/0009_trip_places.sql", find: "CHECK (typeof(name) = 'text' AND ", replace: "CHECK (" },
  m("split-lodging-from-any-kind", "roadTrip.ts", "const lodgings = places.filter((p) => p.kind === \"lodging\");", "const lodgings = places;"),
];

export const EQUIVALENT = [
  { id: "split-no-empty-day-stop", file: "src/roadTrip.ts", find: "if (index <= start) break;",
    witness: "a day takes no edge only when the edge at `index` breaks a limit (the share break needs index > start), and every "
      + "later day meets that same edge with zero seconds and metres, so it takes none either: the pass appends empty spans "
      + "ending at the same index, the last span's end is unchanged, and the outcome is the same too_few_days {days, reached}. "
      + "MISSED in the full run at 441c274; the Swift original's guard exists so `spans.last` names a real day." },
  { id: "split-days-guard", file: "src/roadTrip.ts", find: "if (limits.days < 1) return",
    witness: "without the guard, days < 1 runs forwardPass's `for (day = 1; day <= days)` zero times, spans is [], reached is 0 "
      + "!= edges.length (non-empty here), and the very next line returns too_few_days {days, reached_vertex: 0} - the same "
      + "value. The Swift original keeps the guard because `1...0` traps; the port keeps it for line-for-line parity." },
  { id: "planner-model-gate", file: "src/tripPlanner.ts", find: "if (problem !== null) throw new RouteError",
    witness: "every model this module sends is buildCustomModel(lambda, null), which never names road_access or surface "
      + "(customModel.ts property 1), so rejectCustomModel returns null for each. Defence in depth for P-SAFE-01, as in loopPlanner." },
  { id: "planner-no-recorded-lambda", file: "src/tripPlanner.ts", find: "if (!measuredChosen) throw new TripFailure",
    witness: "searchLambda only ever returns a lambda it passed to `measure`, and `measure` sets measured[formatMultiplier(lambda)] "
      + "before it returns, so `measuredChosen` is never undefined. scenicPlanner keeps the same guard (no_recorded_lambda)." },
  { id: "trip-killed-again", file: "src/trip.ts", find: "killed: () => paused || deps.upstream.killed()",
    witness: "handleTrip already returned 503 when paused (killSwitch(env), read once); env cannot change within one request, so "
      + "the re-check inside guardedPlan sees false either way. It exists for the /plan shape; the KILL tests pin the first check." },
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
      ["a subject unmutated", floorRefusal(MUTATIONS.filter((x) => x.file !== "src/tripRequest.ts").concat(
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

  const onlyAt = argv.indexOf("--only");
  const only = onlyAt >= 0 ? new Set((argv[onlyAt + 1] ?? "").split(",")) : null;
  const chosen = only ? MUTATIONS.filter((x) => only.has(x.id)) : MUTATIONS;
  if (only && chosen.length !== only.size) { console.log("REFUSING: --only names an id that is not a mutation"); return 2; }
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
