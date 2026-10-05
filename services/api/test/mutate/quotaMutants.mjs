#!/usr/bin/env node
/**
 * Mutation population for the Worker's production deps (T-0256 R10): the QuotaCounter Durable Object's counter
 * arithmetic, the Counters over it, the per-kind allowance, the router binding with its secret header, the kill
 * switch and the D1 place resolver. The vitest-driven form T-0248 ruled for planMutants.mjs and T-0252 copied for
 * loopMutants.mjs, because touches: is services/api/ and check-mutate-population.py reads Sources/ and
 * services/etl/etl/ only.
 *
 *   node services/api/test/mutate/quotaMutants.mjs                  run the population
 *   node services/api/test/mutate/quotaMutants.mjs --prove-vacuity  every mutant must report MISSED with no tests
 *   node services/api/test/mutate/quotaMutants.mjs --prove-floor    the floor refuses on its arms; runs no tests
 *   ... --only=<id>,<id>                                             run only the named entries (a round re-runs
 *                                                                    what it touched); an unknown id refuses
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
const OUT = resolve(API, "..", "..", ".build", "mutate-quota");

export const MIN_MUTATIONS = 58;
export const SUBJECTS = ["src/QuotaCounter.ts", "src/quotaCounters.ts", "src/quota.ts", "src/upstream.ts", "src/loop.ts",
  "src/plan.ts", "src/routerDeps.ts", "src/killSwitch.ts", "src/placeResolver.ts"];
const TESTS = ["test/productionDeps.test.ts", "test/quotaCounter.test.ts", "test/planCost.test.ts", "test/loopCost.test.ts",
  "test/placeBounds.test.ts"];

const m = (id, file, find, replace) => ({ id, file: `src/${file}`, find, replace });
export const MUTATIONS = [
  m("do-daily-no-reset", "QuotaCounter.ts", "stored?.day === day ? stored : { day", "stored ? stored : { day"),
  m("do-daily-inclusive", "QuotaCounter.ts", "if (!(used(record, kind) < limit)) return false;", "if (!(used(record, kind) <= limit)) return false;"),
  m("do-daily-step-2", "QuotaCounter.ts", "[kind]: used(record, kind) + 1 }", "[kind]: used(record, kind) + 2 }"),
  m("do-daily-fresh-one", "QuotaCounter.ts", "{ day, plan: 0, loop: 0 }", "{ day, plan: 1, loop: 0 }"),
  m("do-read-daily-stale", "QuotaCounter.ts", "return stored?.day === day ? used(stored, kind) : 0;", "return stored ? used(stored, kind) : 0;"),
  m("do-read-daily-kind", "QuotaCounter.ts", "? used(stored, kind) : 0;", "? stored.plan : 0;"),
  m("do-read-monthly-stale", "QuotaCounter.ts", "return stored?.month === month ? stored.calls : 0;", "return stored ? stored.calls : 0;"),
  m("do-monthly-no-reset", "QuotaCounter.ts", "const current = stored?.month === month ? stored.calls : 0;", "const current = stored ? stored.calls : 0;"),
  m("do-monthly-add-one", "QuotaCounter.ts", "calls: current + calls }", "calls: current + 1 }"),
  m("do-monthly-no-trip", "QuotaCounter.ts", "if (killSwitchTripped(current)) return false;", "if (false) return false;"),
  m("do-daily-key", "QuotaCounter.ts", "DAILY_RECORD = \"daily\";", "DAILY_RECORD = \"day\";"),
  m("do-monthly-key", "QuotaCounter.ts", "MONTHLY_RECORD = \"monthly\";", "MONTHLY_RECORD = \"month\";"),
  m("counters-no-device-prefix", "quotaCounters.ts", "idFromName(`device:${userId}`)", "idFromName(`${userId}`)"),
  m("counters-global-name", "quotaCounters.ts", "GLOBAL_COUNTER = \"global\";", "GLOBAL_COUNTER = \"all\";"),
  m("counters-plan-limit", "quotaCounters.ts", "dailyQuota(kind, tier)", "dailyQuota(\"plan\", tier)"),
  m("counters-refusal-paused", "quotaCounters.ts", "reason: \"quota_exhausted\", tier,", "reason: \"upstream_paused\", tier,"),
  m("counters-month-refusal-ignored", "quotaCounters.ts", "if (!(await global().reserveMonthly(monthKey(now), upstreamCalls))) {",
    "if (!(await global().reserveMonthly(monthKey(now), upstreamCalls)) && false) {"),
  m("counters-month-by-day", "quotaCounters.ts", "global().readMonthly(monthKey(now))", "global().readMonthly(dayKey(now))"),
  m("counters-reserve-wrong-day", "quotaCounters.ts", "reserveDaily(dayKey(now), kind,", "reserveDaily(monthKey(now), kind,"),
  m("quota-loop-free-2", "quota.ts", "{ anon: 1, free: 1, paid", "{ anon: 1, free: 2, paid"),
  m("quota-loop-anon-2", "quota.ts", "{ anon: 1, free: 1, paid", "{ anon: 2, free: 1, paid"),
  m("quota-loop-paid-201", "quota.ts", "paid: DAILY_PLAN_QUOTA.paid }", "paid: 201 }"),
  m("quota-kind-table", "quota.ts", "(kind === \"loop\" ? DAILY_LOOP_QUOTA : DAILY_PLAN_QUOTA)[tier]", "DAILY_PLAN_QUOTA[tier]"),
  m("quota-check-ignores-kind", "quota.ts", "const kind = args.kind ?? \"plan\";", "const kind = \"plan\";"),
  m("upstream-read-plan-kind", "upstream.ts", "deps.counters.read(args.userId, now, kind)", "deps.counters.read(args.userId, now, \"plan\")"),
  m("upstream-check-no-kind", "upstream.ts", "checkQuota({ tier: args.tier, kind, plansUsedToday", "checkQuota({ tier: args.tier, plansUsedToday"),
  m("loop-spends-plan", "loop.ts", "{ ...who, kind: \"loop\" }", "{ ...who, kind: \"plan\" }"),
  m("loop-deps-null", "loop.ts", "return routerDepsFromEnv(env);", "return null;"),
  m("plan-resolver-error-404", "plan.ts", "} catch {\n    return json({ error: \"planning_unavailable\" }, 503);",
    "} catch {\n    return json({ error: \"unknown_place\" }, 404);"),
  m("plan-deps-no-resolver", "plan.ts", "resolvePlace: d1PlaceResolver(env.DB) }", "resolvePlace: async () => null }"),
  m("router-http-allowed", "routerDeps.ts", "if (url.protocol !== \"https:\") return null;", "if (false) return null;"),
  m("router-invalid-allowed", "routerDeps.ts", "if (url.hostname === \"invalid\" || url.hostname.endsWith(\".invalid\")) return null;", "if (false) return null;"),
  m("router-trailing-slash", "routerDeps.ts", "return value.replace(/\\/+$/, \"\");", "return value;"),
  m("router-empty-secret", "routerDeps.ts", "|| secret.length === 0)", "|| false)"),
  m("router-no-quota-check", "routerDeps.ts", "if (!env.QUOTA ||", "if (false ||"),
  m("router-no-secret-header", "routerDeps.ts", "headers.set(ROUTER_SECRET_HEADER, secret);", ""),
  m("router-header-name", "routerDeps.ts", "ROUTER_SECRET_HEADER = \"x-scenic-router-secret\";", "ROUTER_SECRET_HEADER = \"x-router-secret\";"),
  m("router-device-case", "routerDeps.ts", "(req.headers.get(DEVICE_HEADER) ?? \"\").toLowerCase()", "(req.headers.get(DEVICE_HEADER) ?? \"\")"),
  m("router-device-any", "routerDeps.ts", "DEVICE_ID.test(raw) ? raw", "raw.length > 0 ? raw"),
  m("router-tier-free", "routerDeps.ts", "tier: \"anon\" }", "tier: \"free\" }"),
  m("router-tier-from-header", "routerDeps.ts", "UNIDENTIFIED_DEVICE, tier: \"anon\" };",
    "UNIDENTIFIED_DEVICE, tier: ((t) => (t === \"free\" || t === \"paid\" ? t : \"anon\"))(req.headers.get(\"x-scenic-tier\")) };"),
  m("router-device-header", "routerDeps.ts", "DEVICE_HEADER = \"x-scenic-device\";", "DEVICE_HEADER = \"x-device\";"),
  m("kill-kv-ignored", "killSwitch.ts", "return (await env.KILL_SWITCH.get(KILL_KEY)) === \"1\";", "return false;"),
  m("kill-kv-fails-open", "killSwitch.ts", "} catch {\n    return true;", "} catch {\n    return false;"),
  m("kill-env-yields-to-kv", "killSwitch.ts", "if (env.KILL === \"1\") return true;", "if (env.KILL === \"1\" && !env.KILL_SWITCH) return true;"),
  m("kill-key", "killSwitch.ts", "KILL_KEY = \"KILL\";", "KILL_KEY = \"kill\";"),
  m("place-lat-unbounded", "placeResolver.ts", "!(lat >= -90 && lat <= 90)", "!(lat >= -90)"),
  m("place-lat-unbounded-lo", "placeResolver.ts", "!(lat >= -90 && lat <= 90)", "!(lat <= 90)"),
  m("place-lon-unbounded-hi", "placeResolver.ts", "!(lon >= -180 && lon <= 180)", "!(lon >= -180)"),
  m("place-lon-unbounded-lo", "placeResolver.ts", "!(lon >= -180 && lon <= 180)", "!(lon <= 180)"),
  m("place-lat-lo-exclusive", "placeResolver.ts", "lat >= -90", "lat > -90"),
  m("place-lat-hi-exclusive", "placeResolver.ts", "lat <= 90", "lat < 90"),
  m("place-lon-lo-exclusive", "placeResolver.ts", "lon >= -180", "lon > -180"),
  m("place-lon-hi-exclusive", "placeResolver.ts", "lon <= 180", "lon < 180"),
  m("place-lat-any-type", "placeResolver.ts", "typeof lat !== \"number\" || ", ""),
  m("place-lon-any-type", "placeResolver.ts", "typeof lon !== \"number\" || ", ""),
  m("place-missing-is-origin", "placeResolver.ts", "if (row === null) return null;", "if (row === null) return { lat: 0, lon: 0 };"),
  m("place-columns-swapped", "placeResolver.ts", "SELECT lat, lon FROM places", "SELECT lon AS lat, lat AS lon FROM places"),
];

export const EQUIVALENT = [
  { id: "plan-deps-without-db", file: "src/plan.ts", find: "if (router === null || !env.DB) return null;",
    witness: "with the DB check removed, d1PlaceResolver(undefined) is built and its first call throws a TypeError inside "
      + "handlePlan's resolver try, which answers the same 503 planning_unavailable, before guardedPlan, with zero upstream "
      + "calls and nothing reserved - two fail-closed paths with one observable answer. The check stays so the deps factory "
      + "says what it needs; the test '/plan without the DB binding' pins the answer either path gives." },
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
      ["a subject unmutated", floorRefusal(MUTATIONS.filter((x) => x.file !== "src/placeResolver.ts").concat(
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
