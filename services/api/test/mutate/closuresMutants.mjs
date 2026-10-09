#!/usr/bin/env node
/**
 * Mutation population for the closures cron (T-0276): lcsFeed.ts (the LCS D7 parse, its bounds, the buffer and the
 * cap), closuresStore.ts (max age and fail-safe), closuresCron.ts (what gets written, and when nothing does), the
 * wiring in index.ts, routerDeps.ts, reachCache.ts and the four planning routes and their planners. The vitest-driven
 * form of tierMutants.mjs, because touches: is services/api/ and check-mutate-population.py reads Sources/ and
 * services/etl/etl/ only.
 *
 *   node services/api/test/mutate/closuresMutants.mjs                  run the population
 *   node services/api/test/mutate/closuresMutants.mjs --prove-vacuity  every mutant must report MISSED with no tests
 *   node services/api/test/mutate/closuresMutants.mjs --prove-floor    the floor refuses on its arms; runs no tests
 *   ... --only=<id>,<id>                                                run only the named entries; an unknown id refuses
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
const OUT = resolve(API, "..", "..", ".build", "mutate-closures");

export const MIN_MUTATIONS = 133;
export const SUBJECTS = ["src/lcsFeed.ts", "src/closuresStore.ts", "src/closuresCron.ts", "src/index.ts", "src/routerDeps.ts",
  "src/reachCache.ts", "src/plan.ts", "src/scenicPlanner.ts", "src/loop.ts", "src/loopPlanner.ts", "src/trip.ts",
  "src/tripPlanner.ts", "src/isochrone.ts", "src/closuresNearest.ts"];
const TESTS = ["test/closuresFeed.test.ts", "test/closuresCron.test.ts", "test/closuresRoutes.test.ts", "test/closuresDriven.test.ts",
  "test/closuresNearest.test.ts", "test/closuresNearestPick.test.ts",
  "test/closuresNearestRetry.test.ts"];

const m = (id, file, find, replace) => ({ id, file: `src/${file}`, find, replace });
export const MUTATIONS = [
  m("feed-full-any-case", "lcsFeed.ts", "if (kind !== FULL_CLOSURE) continue;", "if (kind.toLowerCase() !== \"full\") continue;"),
  m("feed-lane-too", "lcsFeed.ts", "if (kind !== FULL_CLOSURE) continue;", "if (kind !== FULL_CLOSURE && kind !== \"Lane\") continue;"),
  m("feed-lon-min-open", "lcsFeed.ts", "x >= D7_LON_MIN", "x > D7_LON_MIN"),
  m("feed-lon-max-open", "lcsFeed.ts", "x <= D7_LON_MAX", "x < D7_LON_MAX"),
  m("feed-lat-min-open", "lcsFeed.ts", "y >= D7_LAT_MIN", "y > D7_LAT_MIN"),
  m("feed-lat-max-open", "lcsFeed.ts", "y <= D7_LAT_MAX", "y < D7_LAT_MAX"),
  m("feed-no-box", "lcsFeed.ts", "if (!(x >= D7_LON_MIN", "if (false && !(x >= D7_LON_MIN"),
  m("feed-9-decimals", "lcsFeed.ts", "(\\.[0-9]{1,8})?$/", "(\\.[0-9]{1,9})?$/"),
  m("feed-11-digit-epoch", "lcsFeed.ts", "/^[0-9]{1,10}$/", "/^[0-9]{1,11}$/"),
  m("feed-end-equals-start-inverted", "lcsFeed.ts", "Number(end) < Number(start)", "Number(end) <= Number(start)"),
  m("feed-start-strict", "lcsFeed.ts", "(start <= nowS &&", "(start < nowS &&"),
  m("feed-end-strict", "lcsFeed.ts", "nowS <= Number(", "nowS < Number("),
  m("feed-1097-ignored", "lcsFeed.ts", "const live = placed ||", "const live = false ||"),
  m("feed-1022-ignored", "lcsFeed.ts", "if (cancelled || pickedUp || !live) continue;", "if (pickedUp || !live) continue;"),
  m("feed-1098-ignored", "lcsFeed.ts", "if (cancelled || pickedUp || !live) continue;", "if (cancelled || !live) continue;"),
  m("feed-indefinite-ignored", "lcsFeed.ts", "(indefinite || nowS <=", "(nowS <="),
  m("feed-buffer-25", "lcsFeed.ts", "export const CLOSURE_BUFFER_M = 30;", "export const CLOSURE_BUFFER_M = 25;"),
  m("feed-lon-scale", "lcsFeed.ts", "export const METERS_PER_DEGREE_LON = 91961;", "export const METERS_PER_DEGREE_LON = 92000;"),
  m("feed-lat-scale", "lcsFeed.ts", "export const METERS_PER_DEGREE_LAT = 110946;", "export const METERS_PER_DEGREE_LAT = 111000;"),
  m("feed-normal-flipped", "lcsFeed.ts", "const nx = -uy;", "const nx = uy;"),
  m("feed-no-end-extension", "lcsFeed.ts", "const p1y = dy + uy * b;", "const p1y = dy;"),
  m("feed-one-gate", "lcsFeed.ts", "return [square(0, 0), square(dx, dy)];", "return [square(0, 0)];"),
  m("feed-long-is-chord", "lcsFeed.ts", "if (length > LONG_CLOSURE_M) return [square(0, 0), square(dx, dy)];", ""),
  m("feed-confirmed-last", "lcsFeed.ts", "return a.confirmed ? -1 : 1;", "return a.confirmed ? 1 : -1;"),
  m("feed-unknown-facility-first", "lcsFeed.ts", ": FACILITY_RANK.length);", ": -1);"),
  m("feed-rank-ignored", "lcsFeed.ts", "if (byRank !== 0) return byRank;", ""),
  m("feed-index-descending", "lcsFeed.ts", "a.index < b.index ? -1 : a.index > b.index ? 1 : 0", "a.index < b.index ? 1 : a.index > b.index ? -1 : 0"),
  m("feed-cap-49", "lcsFeed.ts", "features.length + closure.rings.length > cap", "features.length + closure.rings.length >= cap"),
  m("feed-cap-stops", "lcsFeed.ts", "dropped += 1;\n      continue;", "dropped += 1;\n      break;"),
  m("feed-empty-facility-ok", "lcsFeed.ts", "if (typeof facility !== \"string\" || facility === \"\")", "if (typeof facility !== \"string\")"),
  m("feed-empty-index-ok", "lcsFeed.ts", "if (index === null || index === \"\") return", "if (index === null) return"),
  m("feed-codes-unchecked", "lcsFeed.ts", "if (codes.includes(null)) return \"code_not_boolean\";", ""),
  m("feed-end-unchecked", "lcsFeed.ts", "if (indefinite === \"false\" && !epoch(end))", "if (false && !epoch(end))"),
  m("feed-indefinite-unchecked", "lcsFeed.ts", "if (indefinite === null) return \"indefinite_not_boolean\";", ""),
  m("feed-type-number-skipped", "lcsFeed.ts", "out.refused.push({ index, reason: \"type_missing\" });\n      continue;", "continue;"),
  m("feed-end-refusal-first", "lcsFeed.ts", "reason: typeof begin === \"string\" ? begin : (end as LcsRefusal)", "reason: typeof end === \"string\" ? end : (begin as LcsRefusal)"),
  m("feed-feature-untagged", "lcsFeed.ts", "properties: { lcs_index: closure.index }", "properties: {}"),
  m("store-age-strict", "closuresStore.ts", "age <= CLOSURES_MAX_AGE_MS", "age < CLOSURES_MAX_AGE_MS"),
  m("store-future-fresh", "closuresStore.ts", "const fresh = age >= 0 && age", "const fresh = age"),
  m("store-max-age-60", "closuresStore.ts", "30 * 60 * 1000", "60 * 60 * 1000"),
  m("store-stale-drops-set", "closuresStore.ts", "closures: r.geojson,", "closures: fresh ? r.geojson : null,"),
  m("store-unavailable-silent", "closuresStore.ts", "hazard: { state: \"unavailable\", version: NO_CLOSURES_VERSION, fetched_at: null },", "hazard: null,"),
  m("store-stale-silent", "closuresStore.ts", "hazard: fresh ? null :", "hazard: true ? null :"),
  m("store-geojson-unchecked", "closuresStore.ts", "buildCustomModel(LAMBDA_MIN, { type: \"FeatureCollection\", features: g.features.slice(at, at + MAX_CLOSURE_POLYGONS) });", ""),
  m("store-record-shape-unchecked", "closuresStore.ts", "if (r === null || typeof r !== \"object\") return null;", ""),
  m("store-version-unchecked", "closuresStore.ts", "if (typeof r.version !== \"string\" || !CLOSURES_VERSION.test(r.version)) return null;", ""),
  m("store-fetched-at-unchecked", "closuresStore.ts", "if (typeof r.fetched_at !== \"string\" || !ISO_INSTANT.test(r.fetched_at)) return null;", ""),
  m("store-ms-unchecked", "closuresStore.ts", "if (!Number.isFinite(ms)) return null;", ""),
  m("store-null-geojson-unchecked", "closuresStore.ts", "if (g === null || typeof g !== \"object\" || g.type", "if (typeof g !== \"object\" || g.type"),
  m("store-version-unchecked-on-empty", "closuresStore.ts", "!CLOSURES_VERSION.test(r.version)) return null;",
    "(!CLOSURES_VERSION.test(r.version) && (r.geojson as {features?: unknown[]} | null)?.features?.length !== 0)) return null;"),
  m("store-fetched-at-unchecked-on-empty", "closuresStore.ts", "if (typeof r.fetched_at !== \"string\" || !ISO_INSTANT.test(r.fetched_at)) return null;",
    "if ((typeof r.fetched_at !== \"string\" || !ISO_INSTANT.test(r.fetched_at)) && (r.geojson as {features?: unknown[]} | null)?.features?.length !== 0) return null;"),
  m("store-shape-unchecked-on-empty", "closuresStore.ts", "g.type !== \"FeatureCollection\" || ", ""),
  m("store-empty-never-stale", "closuresStore.ts", "const fresh = age >= 0 && age <= CLOSURES_MAX_AGE_MS;",
    "const fresh = r.geojson.features.length === 0 || (age >= 0 && age <= CLOSURES_MAX_AGE_MS);"),
  m("store-version-loose","closuresStore.ts", "/^lcs-d7-[0-9a-f]{16}$/", "/^lcs-d7-/"),
  m("store-instant-loose", "closuresStore.ts", "!ISO_INSTANT.test(r.fetched_at)", "false"),
  m("store-throw-is-fresh", "closuresStore.ts", "raw = await kv.get(CLOSURES_KEY);\n  } catch {\n    return UNAVAILABLE;",
    "raw = await kv.get(CLOSURES_KEY);\n  } catch {\n    return { version: NO_CLOSURES_VERSION, closures: null, hazard: null };"),
  m("store-merge-unbounded", "closuresStore.ts", ".slice(0, MAX_CLOSURE_POLYGONS);", ";"),
  m("store-merge-drops-feed", "closuresStore.ts", "[...(feed?.features ?? []), ...(extra?.features ?? [])]", "[...(extra?.features ?? [])]"),
  m("store-merge-extra-first", "closuresStore.ts", "[...(feed?.features ?? []), ...(extra?.features ?? [])]", "[...(extra?.features ?? []), ...(feed?.features ?? [])]"),
  m("cron-half-refused-stops", "closuresCron.ts", "parsed.refused.length * 2 > parsed.full", "parsed.refused.length * 2 >= parsed.full"),
  m("cron-fetched-at-now", "closuresCron.ts", "Math.min(lastModified, nowMs)", "nowMs"),
  m("cron-fetched-at-max", "closuresCron.ts", "Math.min(lastModified, nowMs)", "Math.max(lastModified, nowMs)"),
  m("cron-unbound-fetches", "closuresCron.ts", "if (!deps.kv) return { written: false, reason: \"unbound\" };",
    "if (!deps.kv) { await deps.fetchImpl(LCS_D7_FEED); return { written: false, reason: \"unbound\" }; }"),
  m("cron-any-ok", "closuresCron.ts", "if (response.status !== 200)", "if (!response.ok)"),
  m("cron-version-over-wrapper", "closuresCron.ts", "encode(JSON.stringify(geojson))", "encode(JSON.stringify({ geojson }))"),
  m("cron-empty-data-written", "closuresCron.ts", "if (!Array.isArray(data) || data.length === 0)", "if (!Array.isArray(data))"),
  m("cron-no-last-modified-ok", "closuresCron.ts", "if (!Number.isFinite(lastModified)) return { written: false, reason: \"no_last_modified\" };", ""),
  m("cron-now-ms-as-s", "closuresCron.ts", "Math.floor(nowMs / 1000)", "nowMs"),
  m("cron-now-is-last-modified", "closuresCron.ts", "parseLcsFeed(data, Math.floor(nowMs / 1000))", "parseLcsFeed(data, Math.floor(lastModified / 1000))"),
  m("cron-now-ceil", "closuresCron.ts", "Math.floor(nowMs / 1000)", "Math.ceil(nowMs / 1000)"),
  m("cron-now-round", "closuresCron.ts", "Math.floor(nowMs / 1000)", "Math.round(nowMs / 1000)"),
  m("index-cron-unbound", "index.ts", "kv: env.CLOSURES,", "kv: undefined,"),
  m("deps-closures-unbound", "routerDeps.ts", "readClosures(env.CLOSURES, now().getTime())", "readClosures(undefined, now().getTime())"),
  m("deps-closures-clock-plus-1", "routerDeps.ts", "readClosures(env.CLOSURES, now().getTime())", "readClosures(env.CLOSURES, now().getTime() + 1)"),
  m("deps-closures-clock-minus-1", "routerDeps.ts", "readClosures(env.CLOSURES, now().getTime())", "readClosures(env.CLOSURES, now().getTime() - 1)"),
  m("cache-key-no-closures", "reachCache.ts", "|${graphVersion}|${closuresVersion}`", "|${graphVersion}`"),
  m("plan-no-closures", "plan.ts", "request.budgetMinutes * 60, picker.pick,", "request.budgetMinutes * 60, () => null,"),
  m("plan-no-hazard", "plan.ts", "return json(withClosuresHazard(plan, snapshot, picker.dropped(), picker.crosses()), 200);", "return json(plan, 200);"),
  m("plan-closures-before-kill", "plan.ts", "  const paused = await killSwitch(env);", "  await deps?.closures();\n  const paused = await killSwitch(env);"),
  m("plan-closures-twice", "plan.ts", "const snapshot = await deps.closures();", "await deps.closures();\n  const snapshot = await deps.closures();"),
  m("scenic-search-no-closures", "scenicPlanner.ts", "SCENIC_PROFILE, buildCustomModel(lambda, closures));", "SCENIC_PROFILE, buildCustomModel(lambda, null));"),
  m("scenic-fast-gets-model", "scenicPlanner.ts", "FAST_PROFILE, undefined);", "FAST_PROFILE, closures === null ? undefined : buildCustomModel(0, closures));"),
  m("loop-no-closures", "loop.ts", "seed, picker.pick,", "seed, () => null,"),
  m("loop-no-hazard", "loop.ts", "return json(withClosuresHazard(loop, snapshot, picker.dropped(), picker.crosses()), 200);", "return json(loop, 200);"),
  m("loop-first-attempt-bare", "loopPlanner.ts", "let current = await attempt(seed, feed);", "let current = await attempt(seed, null);"),
  m("loop-reseed-bare", "loopPlanner.ts", "current = await attempt(reseed, feed);", "current = await attempt(reseed, null);"),
  m("loop-retrace-drops-feed", "loopPlanner.ts", "attempt(reseed, mergeClosures(feed, areas))", "attempt(reseed, areas)"),
  m("trip-no-closures", "trip.ts", "who.tier === \"paid\", picker.pick,", "who.tier === \"paid\", () => null,"),
  m("trip-no-hazard", "trip.ts", "return json(withClosuresHazard(trip, snapshot, picker.dropped(), picker.crosses()), 200);", "return json(trip, 200);"),
  m("trip-search-no-closures", "tripPlanner.ts", "SCENIC_PROFILE, buildCustomModel(lambda, closures));", "SCENIC_PROFILE, buildCustomModel(lambda, null));"),
  m("trip-legs-no-closures", "tripPlanner.ts", "buildCustomModel(outcome.lambda, closuresFor(from, to))", "buildCustomModel(outcome.lambda, null)"),
  m("iso-key-no-version", "isochrone.ts", "deps.graphVersion, snapshot.version)", "deps.graphVersion, \"none\")"),
  m("iso-hit-no-hazard", "isochrone.ts", "return json(withClosuresHazard({ minutes, buckets: cached }, snapshot), 200);", "return json({ minutes, buckets: cached }, 200);"),
  m("iso-miss-no-hazard", "isochrone.ts", "return json(withClosuresHazard({ minutes, buckets }, snapshot), 200);", "return json({ minutes, buckets }, 200);"),
  m("iso-closures-before-kill", "isochrone.ts", "if (await killSwitch(env)) return", "await deps?.closures();\n  if (await killSwitch(env)) return"),
  // T-0282 N1-N6: the stored bound, the per-request selection, the hazard's dropped, the corridor each request uses.
  m("near-fast-path-lt", "closuresNearest.ts", "set.features.length <= MAX_CLOSURE_POLYGONS) return", "set.features.length < MAX_CLOSURE_POLYGONS) return"),
  m("near-greedy-skip", "closuresNearest.ts", "if (used + group.features.length > MAX_CLOSURE_POLYGONS) break;", "if (used + group.features.length > MAX_CLOSURE_POLYGONS) continue;"),
  m("near-fill-49", "closuresNearest.ts", "if (used + group.features.length > MAX_CLOSURE_POLYGONS) break;", "if (used + group.features.length >= MAX_CLOSURE_POLYGONS) break;"),
  m("near-tie-reversed", "closuresNearest.ts", "x.distance - y.distance || x.at - y.at", "x.distance - y.distance || y.at - x.at"),
  m("near-farthest-first", "closuresNearest.ts", "x.distance - y.distance || x.at - y.at", "y.distance - x.distance || x.at - y.at"),
  m("near-sent-ranked", "closuresNearest.ts", ".sort((x, y) => x.at - y.at).flatMap", ".flatMap"),
  m("near-inside-off", "closuresNearest.ts", "if (inside(o, ring)) return 0;", ""),
  m("near-cross-off", "closuresNearest.ts", "if (crosses(o, d, a, b)) return 0;", ""),
  m("near-clamp-high-off", "closuresNearest.ts", "t = t < 0 ? 0 : t > 1 ? 1 : t;", "t = t < 0 ? 0 : t;"),
  m("near-clamp-low-off", "closuresNearest.ts", "t = t < 0 ? 0 : t > 1 ? 1 : t;", "t = t > 1 ? 1 : t;"),
  m("near-no-groups", "closuresNearest.ts", "typeof index === \"string\" && index === last", "false"),
  m("near-group-max", "closuresNearest.ts", "distance: Math.min(...features", "distance: Math.max(...features"),
  m("near-ends-only", "closuresNearest.ts", "pointSegment2(o, a, b), pointSegment2(d, a, b), pointSegment2(a, o, d), pointSegment2(b, o, d)", "pointSegment2(o, a, b), pointSegment2(d, a, b)"),
  m("near-origin-end-only", "closuresNearest.ts", "pointSegment2(o, a, b), pointSegment2(d, a, b), ", "pointSegment2(o, a, b), "),
  m("near-picker-last", "closuresNearest.ts", "most = Math.max(most, picked.dropped);", "most = picked.dropped;"),
  m("near-picker-sum", "closuresNearest.ts", "most = Math.max(most, picked.dropped);", "most += picked.dropped;"),
  m("near-lat-scale", "closuresNearest.ts", "lat * METERS_PER_DEGREE_LAT]", "lat * METERS_PER_DEGREE_LON]"),
  m("store-cap-2001", "closuresStore.ts", "CLOSURES_STORED_MAX_POLYGONS = 2000;", "CLOSURES_STORED_MAX_POLYGONS = 2001;"),
  m("store-cap-1999", "closuresStore.ts", "CLOSURES_STORED_MAX_POLYGONS = 2000;", "CLOSURES_STORED_MAX_POLYGONS = 1999;"),
  m("store-first-chunk-only", "closuresStore.ts", "at === 0 || at < g.features.length", "at === 0"),
  m("store-dropped-ignored", "closuresStore.ts", "if (dropped === 0 && crosses.length === 0) return snapshot.hazard", "if (dropped >= 0 && crosses.length === 0) return snapshot.hazard"),
  m("store-dropped-state", "closuresStore.ts", "state: \"fresh\" as const", "state: \"stale\" as const"),
  m("store-fetched-at-lost", "closuresStore.ts", "    fetchedAt: r.fetchedAt,", "    fetchedAt: null,"),
  m("plan-dropped-unreported", "plan.ts", "withClosuresHazard(plan, snapshot, picker.dropped(),", "withClosuresHazard(plan, snapshot, 0,"),
  m("loop-dropped-unreported", "loop.ts", "withClosuresHazard(loop, snapshot, picker.dropped(),", "withClosuresHazard(loop, snapshot, 0,"),
  m("trip-dropped-unreported", "trip.ts", "withClosuresHazard(trip, snapshot, picker.dropped(),", "withClosuresHazard(trip, snapshot, 0,"),
  m("plan-whole-set", "plan.ts", "request.budgetMinutes * 60, picker.pick,", "request.budgetMinutes * 60, () => snapshot.closures,"),
  m("loop-whole-set", "loop.ts", "seed, picker.pick,", "seed, () => snapshot.closures,"),
  m("trip-whole-set", "trip.ts", "who.tier === \"paid\", picker.pick,", "who.tier === \"paid\", () => snapshot.closures,"),
  m("scenic-origin-only", "scenicPlanner.ts", "const closures = closuresFor(origin, destination);", "const closures = closuresFor(origin, origin);"),
  m("trip-search-origin-only", "tripPlanner.ts", "const closures = closuresFor(origin, destination);", "const closures = closuresFor(origin, origin);"),
  m("trip-legs-search-set", "tripPlanner.ts", "buildCustomModel(outcome.lambda, closuresFor(from, to))", "buildCustomModel(outcome.lambda, closures)"),
  m("loop-start-south", "loopPlanner.ts", "const feed = closuresFor(start, start);", "const feed = closuresFor(start, { lat: start.lat - 1, lon: start.lon });"),
  m("feed-cap-50", "lcsFeed.ts", "export function capClosures(closures: ActiveClosure[], cap = CLOSURES_STORED_MAX_POLYGONS)", "export function capClosures(closures: ActiveClosure[], cap = 50)"),
  m("loop-reseed-other-corridor", "loopPlanner.ts", "current = await attempt(reseed, feed);", "current = await attempt(reseed, closuresFor(start, { lat: start.lat - 1, lon: start.lon }));"),
  m("loop-retrace-other-corridor", "loopPlanner.ts", "attempt(reseed, mergeClosures(feed, areas))", "attempt(reseed, mergeClosures(closuresFor(start, { lat: start.lat - 1, lon: start.lon }), areas))"),
  m("trip-legs-3plus-search-set", "tripPlanner.ts", "buildCustomModel(outcome.lambda, closuresFor(from, to))", "buildCustomModel(outcome.lambda, dayNumber > 2 ? closures : closuresFor(from, to))"),
  m("trip-last-leg-search-set", "tripPlanner.ts", "buildCustomModel(outcome.lambda, closuresFor(from, to))", "buildCustomModel(outcome.lambda, dayNumber === days ? closures : closuresFor(from, to))"),
];

export const EQUIVALENT = [
  { id: "feed-long-at-500", file: "src/lcsFeed.ts", find: "if (length > LONG_CLOSURE_M)",
    witness: "`>` and `>=` differ only at a chord of EXACTLY 500.0 m, and no row the parse accepts was found to make one: "
      + "the chord is sqrt(dx*dx + dy*dy) over decimal strings of <= 8 places scaled by 110946 / 91961, and "
      + "a search quoted in the T-0276 Log tried 28572 begin latitudes x 20 end offsets of a lat-only chord around 500 m and "
      + "found none equal to 500.0. closuresFeed.test.ts brackets the threshold at 499.9992 m (one rectangle) and "
      + "500.0003 m (two gates), 1.1 mm apart, which kills every mutant that moves the threshold by more than that." },
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
      ["a subject unmutated", floorRefusal(MUTATIONS.filter((x) => x.file !== "src/isochrone.ts").concat(
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
