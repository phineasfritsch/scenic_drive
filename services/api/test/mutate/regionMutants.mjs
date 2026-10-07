#!/usr/bin/env node
/**
 * Mutation population for the served-region gate and POST /waitlist (T-0293): every half-bound and edge of the gate
 * (servedRegion.ts), the gate's call in each planning handler (plan.ts, loop.ts, trip.ts, isochrone.ts), every
 * validation branch and the counter write of the waitlist (waitlist.ts), its wiring in ROUTES (index.ts), and the
 * waitlist table's columns (migrations/0006_waitlist.sql). The telemetryMutants.mjs shape.
 *
 *   node services/api/test/mutate/regionMutants.mjs                  run the population
 *   node services/api/test/mutate/regionMutants.mjs --prove-vacuity  every mutant must report MISSED with no tests
 *   node services/api/test/mutate/regionMutants.mjs --prove-floor    the floor refuses on its arms; runs no tests
 *   ... --only=<id>,<id>                                               run only the named entries
 *
 * WHAT COUNTS. CAUGHT only when vitest's JSON report names a FAILED test. A run that fails with no named
 * failure (a mutant that does not load) is a TRAP and does not count. An anchor that does not occur exactly
 * once is STALE and the run refuses before mutating anything. Pass condition: caught == MUTATIONS.length.
 * THE FLOOR is literal: MIN_MUTATIONS, and every SUBJECT is mutated by at least one entry. requestReadSites.test.ts
 * is deliberately NOT in TESTS: a mutant must be caught by behaviour through worker.fetch, not by a source guard.
 */
import { spawnSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const API = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const OUT = resolve(API, "..", "..", ".build", "mutate-region");

export const MIN_MUTATIONS = 40;
export const SUBJECTS = ["src/servedRegion.ts", "src/plan.ts", "src/loop.ts", "src/trip.ts", "src/isochrone.ts",
  "src/waitlist.ts", "src/index.ts", "migrations/0006_waitlist.sql"];
const TESTS = ["test/regionGate.test.ts", "test/waitlist.test.ts", "test/migrationColumns.test.ts", "test/planWire.test.ts",
  "test/routes.test.ts", "test/killSwitchRoutes.test.ts"];

const m = (id, file, find, replace) => ({ id, file: file.startsWith("migrations/") ? file : `src/${file}`, find, replace });
const S = "servedRegion.ts";
const W = "waitlist.ts";
const MIG = "migrations/0006_waitlist.sql";
const gate = (field) => `  if (!inServedRegion(request.${field})) return json({ error: "region_unsupported" }, 422);\n`;
export const MUTATIONS = [
  m("lat-min-dropped", S, "point.lat >= box.min_lat && ", ""),
  m("lat-max-dropped", S, "point.lat <= box.max_lat && ", ""),
  m("lon-min-dropped", S, "point.lon >= box.min_lon && ", ""),
  m("lon-max-dropped", S, " && point.lon <= box.max_lon;", ";"),
  m("lat-min-strict", S, "point.lat >= box.min_lat", "point.lat > box.min_lat"),
  m("lat-max-strict", S, "point.lat <= box.max_lat", "point.lat < box.max_lat"),
  m("lon-min-strict", S, "point.lon >= box.min_lon", "point.lon > box.min_lon"),
  m("lon-max-strict", S, "point.lon <= box.max_lon", "point.lon < box.max_lon"),
  m("lat-min-widened", S, "point.lat >= box.min_lat", "point.lat >= box.min_lat - 0.01"),
  m("lon-max-widened", S, "point.lon <= box.max_lon", "point.lon <= box.max_lon + 0.01"),
  m("la-dropped", S, "  { id: la.id, bbox: la.bbox },\n", ""),
  m("sfbay-dropped", S, "  { id: sfbay.id, bbox: sfbay.bbox },\n", ""),
  m("some-to-every", S, "SERVED_REGIONS.some(", "SERVED_REGIONS.every("),
  m("lat-reads-lon", S, "point.lat >= box.min_lat && point.lat <= box.max_lat", "point.lon >= box.min_lat && point.lon <= box.max_lat"),
  m("boxes-merged-south", S, "{ id: sfbay.id, bbox: sfbay.bbox }", "{ id: sfbay.id, bbox: { ...sfbay.bbox, min_lat: la.bbox.min_lat } }"),
  m("plan-gate-dropped", "plan.ts", gate("origin"), ""),
  m("loop-gate-dropped", "loop.ts", gate("start"), ""),
  m("trip-gate-dropped", "trip.ts", gate("origin"), ""),
  m("isochrone-gate-dropped", "isochrone.ts", gate("start"), ""),
  m("plan-gate-400", "plan.ts", "{ error: \"region_unsupported\" }, 422)", "{ error: \"region_unsupported\" }, 400)"),
  m("trip-gate-code", "trip.ts", "{ error: \"region_unsupported\" }, 422)", "{ error: \"region_unsupported_trip\" }, 422)"),
  m("isochrone-gate-constant", "isochrone.ts", "inServedRegion(request.start)", "inServedRegion({ lat: 34.02, lon: -118.49 })"),
  m("post-only-dropped", W, "if (req.method !== \"POST\") return", "if (req.method === \"PATCH\") return"),
  m("array-is-an-object", W, " || Array.isArray(raw)) return", ") return"),
  m("keys-superset", W, "keys.length !== 1 || ", ""),
  m("keys-includes", W, "keys.length !== 1 || keys[0] !== \"cell\"", "!keys.includes(\"cell\")"),
  m("cell-type-unchecked", W, "typeof cell !== \"string\" || ", ""),
  m("cell-unvalidated", W, " || !isResolution5Cell(cell)", ""),
  m("cell-trimmed", W, "isResolution5Cell(cell)", "isResolution5Cell(String(cell).trim())"),
  m("cell-lowercased", W, "isResolution5Cell(cell)", "isResolution5Cell(String(cell).toLowerCase())"),
  m("count-not-incremented", W, "count = count + 1", "count = 1"),
  m("count-plus-two", W, "count + 1,", "count + 2,"),
  m("updated-at-instant", W, ".toISOString().slice(0, 10)", ".toISOString().slice(0, 10).replace(\"-\", \"/\")"),
  m("updated-at-kept", W, ", updated_at = excluded.updated_at", ""),
  m("write-failure-answers-200", W, "  } catch {\n    return json({ error: \"waitlist_unavailable\" }, 503);",
    "  } catch {\n    return json({ waitlisted: true }, 200);"),
  m("route-unwired", "index.ts", "  \"/waitlist\": (req, env) => handleWaitlist(req, waitlistDepsFromEnv(env)),\n", ""),
  m("route-killed", "index.ts", "handleWaitlist(req, waitlistDepsFromEnv(env))",
    "(env.KILL === \"1\" ? Promise.resolve(new Response(\"{}\", { status: 503 })) : handleWaitlist(req, waitlistDepsFromEnv(env)))"),
  m("answer-echoes-cell", W, "json({ waitlisted: true }, 200)", "json({ waitlisted: true, cell: parsed.cell }, 200)"),
  m("migration-address-column", MIG, "  count INTEGER", "  address TEXT,\n  count INTEGER"),
  m("migration-device-column", MIG, "  count INTEGER", "  device_id TEXT,\n  count INTEGER"),
];

export const EQUIVALENT = [
  { id: "bound-widened-sub-step", file: "src/servedRegion.ts", find: "point.lat <= box.max_lat",
    replace: "point.lat <= box.max_lat + 0.005",
    witness: "every coordinate that reaches the gate has passed the body whitelist's atMostTwoDecimals, so it lies on "
      + "the 0.01 lattice, and every bound is itself a 2 dp value: no sendable latitude lies in (max_lat, max_lat + "
      + "0.005]. The table's one-ulp rows show the whitelist answers 400 there before the gate runs; a widening of a "
      + "whole step is lat-min-widened / lon-max-widened, both run." },
  { id: "db-missing-ignored", file: "src/waitlist.ts", find: "if (!deps.db) return json({ error: \"waitlist_unavailable\" }, 503);\n",
    replace: "",
    witness: "without the guard, an unbound DB makes deps.db.prepare throw a TypeError INSIDE the write's try, whose "
      + "catch answers the same 503 waitlist_unavailable: the answer is identical for every input (measured: MISSED in "
      + "the first population run, 2026-10-07). The guard stays for the type narrowing; write-failure-answers-200 "
      + "holds the catch that makes it redundant." },
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
      ["a subject unmutated", floorRefusal(MUTATIONS.filter((x) => x.file !== "src/servedRegion.ts").concat(
        Array.from({ length: MIN_MUTATIONS }, () => MUTATIONS.find((x) => x.file !== "src/servedRegion.ts"))))],
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
  const dirty = spawnSync("git", ["status", "--porcelain", "--", "src", "migrations"], { cwd: API, encoding: "utf8" });
  if (dirty.status !== 0 || dirty.stdout.trim() !== "") { console.log("REFUSING TO RUN: services/api/src or migrations is not clean"); return 2; }

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
