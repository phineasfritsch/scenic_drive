#!/usr/bin/env node
/**
 * Mutation population for the caller's quota tier (T-0272 R9): accountTier.ts (the entitlement of
 * x-scenic-account-token -> paid | anon, fail-closed), the identify routerDeps.ts builds from it (the install bucket,
 * the Worker's now), REFUND_REVERSED in asnNotification.ts, and the await of identify in every handler that spends
 * a reservation. The vitest-driven form of quotaMutants.mjs, because touches: is services/api/ and
 * check-mutate-population.py reads Sources/ and services/etl/etl/ only.
 *
 *   node services/api/test/mutate/tierMutants.mjs                  run the population
 *   node services/api/test/mutate/tierMutants.mjs --prove-vacuity  every mutant must report MISSED with no tests
 *   node services/api/test/mutate/tierMutants.mjs --prove-floor    the floor refuses on its arms; runs no tests
 *   ... --only=<id>,<id>                                            run only the named entries; an unknown id refuses
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
const OUT = resolve(API, "..", "..", ".build", "mutate-tier");

export const MIN_MUTATIONS = 18;
export const SUBJECTS = ["src/accountTier.ts", "src/routerDeps.ts", "src/asnNotification.ts", "src/plan.ts", "src/loop.ts",
  "src/trip.ts", "src/isochrone.ts"];
const TESTS = ["test/accountTier.test.ts", "test/asnState.test.ts", "test/isochroneCost.test.ts"];

const m = (id, file, find, replace) => ({ id, file: `src/${file}`, find, replace });
export const MUTATIONS = [
  m("tier-case-sensitive", "accountTier.ts", "?? \"\").toLowerCase();", "?? \"\");"),
  m("tier-any-token-read", "accountTier.ts", "if (db === undefined || !UUID.test(token)) return \"anon\";", "if (db === undefined) return \"anon\";"),
  m("tier-inactive-paid", "accountTier.ts", ").status === \"active\" ? \"paid\"", ").status !== \"none\" ? \"paid\""),
  m("tier-active-free", "accountTier.ts", "? \"paid\" : \"anon\";", "? \"free\" : \"anon\";"),
  m("tier-failure-paid", "accountTier.ts", "} catch {\n    return \"anon\";", "} catch {\n    return \"paid\";"),
  m("tier-from-device-header", "accountTier.ts", "req.headers.get(ACCOUNT_TOKEN_HEADER)", "req.headers.get(\"x-scenic-device\")"),
  m("tier-from-another-header", "accountTier.ts", "(req.headers.get(ACCOUNT_TOKEN_HEADER) ?? \"\")",
    "(req.headers.get(ACCOUNT_TOKEN_HEADER) ?? req.headers.get(\"x-account-token\") ?? \"\")"),
  m("deps-tier-always-anon", "routerDeps.ts", "=== \"paid\" ? { ...device, tier: \"paid\" } : device;", "=== \"paid\" ? device : device;"),
  m("deps-tier-without-db", "routerDeps.ts", "accountTier(req, env.DB,", "accountTier(req, undefined,"),
  m("deps-now-minus-1", "routerDeps.ts", "env.DB, now().getTime())", "env.DB, now().getTime() - 1)"),
  m("deps-now-plus-1", "routerDeps.ts", "env.DB, now().getTime())", "env.DB, now().getTime() + 1)"),
  m("deps-bucket-is-token", "routerDeps.ts", "{ ...device, tier: \"paid\" }",
    "{ userId: req.headers.get(\"x-scenic-account-token\") ?? device.userId, tier: \"paid\" as const }"),
  m("asn-reversal-dropped", "asnNotification.ts", "REACTIVATES = [\"REFUND_REVERSED\"];", "REACTIVATES = [];"),
  m("asn-reversal-no-expiry", "asnNotification.ts", "} else if (status === \"active\" && expiresDate !== undefined) {",
    "} else if (status === \"active\" && expiresDate !== undefined && !REACTIVATES.includes(type)) {"),
  m("plan-identify-unawaited", "plan.ts", "guardedPlan(upstream, await deps.identify(req),", "guardedPlan(upstream, deps.identify(req),"),
  m("loop-identify-unawaited", "loop.ts", "const who = await deps.identify(req);", "const who = deps.identify(req);"),
  m("trip-identify-unawaited", "trip.ts", "const who = await deps.identify(req);", "const who = deps.identify(req);"),
  m("isochrone-identify-unawaited", "isochrone.ts", "{ ...(await deps.identify(req)), kind", "{ ...deps.identify(req), kind"),
];

export const EQUIVALENT = [
  { id: "tier-no-db-check", file: "src/accountTier.ts", find: "if (db === undefined || !UUID.test(token)) return \"anon\";",
    witness: "with `db === undefined ||` removed, an absent DB reaches readEntitlement(undefined, ...), whose first "
      + "`db.prepare` throws a TypeError inside accountTier's try, which answers the same anon - two fail-closed paths "
      + "with one observable answer and no D1 to count reads on. The check stays so an absent binding never reaches D1 "
      + "code; the D1-failure tests (accountTier.test.ts R4) pin the anon answer a throwing read gives." },
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
