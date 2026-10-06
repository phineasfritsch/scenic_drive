#!/usr/bin/env node
/**
 * Mutation population for POST /telemetry (T-0279 R11): the whitelist (telemetryPoint.ts), the H3 res-5 cell rule
 * (h3Res5.ts), the handler's order - KILL, whitelist, reserve n events, then write (telemetry.ts) - its wiring in
 * ROUTES (index.ts), and the telemetry arms of quota.ts and QuotaCounter.ts. The tierMutants.mjs shape.
 *
 *   node services/api/test/mutate/telemetryMutants.mjs                  run the population
 *   node services/api/test/mutate/telemetryMutants.mjs --prove-vacuity  every mutant must report MISSED with no tests
 *   node services/api/test/mutate/telemetryMutants.mjs --prove-floor    the floor refuses on its arms; runs no tests
 *   ... --only=<id>,<id>                                                  run only the named entries
 *
 * WHAT COUNTS. CAUGHT only when vitest's JSON report names a FAILED test. A run that fails with no named
 * failure (a mutant that does not load) is a TRAP and does not count. An anchor that does not occur exactly
 * once is STALE and the run refuses before mutating anything. Pass condition: caught == MUTATIONS.length.
 * THE FLOOR is literal: MIN_MUTATIONS, and every SUBJECT is mutated by at least one entry. EQUIVALENT entries
 * carry a witness - the reason no test CAN tell them apart - and are never run.
 */
import { spawnSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const API = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const OUT = resolve(API, "..", "..", ".build", "mutate-telemetry");

export const MIN_MUTATIONS = 61;
export const SUBJECTS = ["src/telemetry.ts", "src/telemetryPoint.ts", "src/h3Res5.ts", "src/index.ts", "src/quota.ts",
  "src/QuotaCounter.ts"];
const TESTS = ["test/telemetryCost.test.ts", "test/telemetryWhitelist.test.ts", "test/telemetryFixture.test.ts",
  "test/killSwitchRoutes.test.ts", "test/quotaCounter.test.ts"];

const m = (id, file, find, replace) => ({ id, file: `src/${file}`, find, replace });
const T = "telemetry.ts";
const P = "telemetryPoint.ts";
const H = "h3Res5.ts";
export const MUTATIONS = [
  m("kill-ignored", T, "if (await killSwitch(env)) return", "if (false && (await killSwitch(env))) return"),
  m("kill-env-only", T, "if (await killSwitch(env)) return", "if (await killSwitch({ KILL: env.KILL })) return"),
  m("post-only-dropped", T, "if (req.method !== \"POST\") return", "if (req.method === \"PUT\") return"),
  m("unavailable-ignored", T, "if (!env.TELEMETRY || !env.QUOTA) return null;", "if (!env.QUOTA) return null;"),
  m("write-before-reserve", T, "  let reserved: boolean;", "  for (const point of parsed.points) deps.dataset.writeDataPoint(point);\n  let reserved: boolean;"),
  m("reserve-one-not-n", T, "DAILY_TELEMETRY_QUOTA, parsed.points.length)", "DAILY_TELEMETRY_QUOTA)"),
  m("reserve-plan-kind", T, "dayKey(now), \"telemetry\", DAILY", "dayKey(now), \"plan\", DAILY"),
  m("reserve-shared-bucket", T, "idFromName(`device:${userId}`)", "idFromName(\"device:shared\")"),
  m("refusal-ignored", T, "if (!reserved) return", "if (false) return"),
  m("identity-bare-header", T, "await identifyCaller(req.headers.get(AUTHORIZATION_HEADER), env, now.getTime(), async () => deviceIdentity(req));",
    "deviceIdentity(req);"),
  m("resets-at-now", T, "resets_at: nextReset(now)", "resets_at: now.toISOString()"),
  m("write-raw-body", T, "for (const point of parsed.points) deps.dataset.writeDataPoint(point);",
    "for (const point of (raw as { events: unknown[] }).events) deps.dataset.writeDataPoint(point as never);"),
  m("written-count-1", T, "json({ written: parsed.points.length }, 200)", "json({ written: 1 }, 200)"),
  m("route-unkilled", "index.ts", "handleTelemetry(req, env, telemetryDepsFromEnv(env))",
    "handleTelemetry(req, { ...env, KILL: undefined, KILL_SWITCH: undefined }, telemetryDepsFromEnv(env))"),
  m("max-per-request-21", P, "MAX_TELEMETRY_EVENTS_PER_REQUEST = 20;", "MAX_TELEMETRY_EVENTS_PER_REQUEST = 21;"),
  m("empty-events", P, "events.length < 1 ||", "events.length < 0 ||"),
  m("top-extra-key", P, "!hasExactKeys(raw, [\"events\"])", "!(\"events\" in raw)"),
  m("point-extra-key", P, "!hasExactKeys(raw, [\"indexes\", \"blobs\", \"doubles\"])", "false"),
  m("exact-keys-superset", P, "own.length === keys.length &&", "own.length >= keys.length &&"),
  m("blob-count-at-least-3", P, "blobs.length !== 3", "blobs.length < 3"),
  m("blob-type-unchecked", P, "!blobs.every((b) => typeof b === \"string\")", "false"),
  m("name-in-prototype", P, "!Object.prototype.hasOwnProperty.call(TELEMETRY_WIRE, name)", "!(name in TELEMETRY_WIRE)"),
  m("indexes-any-string", P, "indexes[0] !== name", "typeof indexes[0] !== \"string\""),
  m("indexes-at-least-1", P, "indexes.length !== 1", "indexes.length < 1"),
  m("label-unchecked", P, "if (!rule.labels.includes(label)) return", "if (false) return"),
  m("cell-anywhere", P, ": cell !== \"\") {", ": false) {"),
  m("cell-rule-skipped", P, "rule.cell ? !isResolution5Cell(cell)", "rule.cell ? cell === \"\""),
  m("doubles-at-least-2", P, "doubles.length !== 2", "doubles.length < 2"),
  m("minus-zero-allowed", P, "!Object.is(value, -0) && ", ""),
  m("fractions-allowed", P, "Number.isInteger(value)", "Number.isFinite(value)"),
  m("range-min-minus-1", P, "value >= min &&", "value >= min - 1 &&"),
  m("unused-min-minus-1", P, "const UNUSED: Range = [0, 0];", "const UNUSED: Range = [-1, 0];"),
  m("label-prefix-accepted", P, "if (!rule.labels.includes(label)) return",
    "if (!(rule.labels.includes(label) || (label.length > 0 && rule.labels.some((l) => l.startsWith(label))))) return"),
  m("range-max-plus-1", P, "value <= max;", "value <= max + 1;"),
  m("budget-1441", P, "[[0, 1440], UNUSED]", "[[0, 1441], UNUSED]"),
  m("percent-101", P, "const PERCENT: Range = [0, 100];", "const PERCENT: Range = [0, 101];"),
  m("deviations-1001", P, "[PERCENT, [0, 1000]]", "[PERCENT, [0, 1001]]"),
  m("version-2147483648", P, "[[0, 2147483647], UNUSED]", "[[0, 2147483648], UNUSED]"),
  m("handoff-label-added", P, "[\"apple_maps\", \"google_maps\", \"waze\"]", "[\"apple_maps\", \"google_maps\", \"waze\", \"here_maps\"]"),
  m("abandoned-v2-open", P, "doubles: [PERCENT, UNUSED] }", "doubles: [PERCENT, PERCENT] }"),
  m("feature-label-dropped", P, "[\"scenic\", \"loop\", \"surprise\", \"road_trip\"]", "[\"scenic\", \"loop\", \"surprise\"]"),
  m("rebuilt-doubles-swapped", P, "doubles: [v1, v2], indexes: [name]", "doubles: [v2, v1], indexes: [name]"),
  m("rebuilt-label-dropped", P, "blobs: [name, label, cell], doubles", "blobs: [name, \"\", cell], doubles"),
  m("cell-uppercase", H, "/^[0-9a-f]{15}$/", "/^[0-9a-fA-F]{15}$/"),
  m("cell-16-digits", H, "/^[0-9a-f]{15}$/", "/^[0-9a-f]{15,16}$/"),
  m("cell-mode-0", H, "& 15n) !== 1n) return false;", "& 15n) > 1n) return false;"),
  m("cell-reserved-1", H, "& 7n) !== 0n) return false;", "& 7n) > 1n) return false;"),
  m("cell-res-6", H, "& 15n) !== 5n) return false;", "& 15n) < 5n) return false;"),
  m("cell-base-122", H, "if (base > MAX_BASE_CELL) return false;", "if (base > MAX_BASE_CELL + 1) return false;"),
  m("cell-digit-7", H, "if (digit(index, r) > 6) return false;", "if (digit(index, r) > 7) return false;"),
  m("cell-digit-5-unchecked", H, "r <= 5; r++) if (digit(index, r) > 6)", "r <= 4; r++) if (digit(index, r) > 6)"),
  m("cell-tail-unchecked", H, "if (digit(index, r) !== 7) return false;", "if (digit(index, r) > 7) return false;"),
  m("cell-pentagon-117-dropped", H, "107, 117]", "107]"),
  m("cell-pentagon-58-dropped", H, "49, 58, 63,", "49, 63,"),
  m("cell-pentagon-zero-stops", H, "if (d === 0) continue;", "if (d === 0) return true;"),
  m("cell-pentagon-unchecked", H, "return d !== 1;", "return true;"),
  m("quota-telemetry-arm-dropped", "quota.ts", "  if (kind === \"telemetry\") return DAILY_TELEMETRY_QUOTA;\n", ""),
  m("quota-201", "quota.ts", "DAILY_TELEMETRY_QUOTA = 200;", "DAILY_TELEMETRY_QUOTA = 201;"),
  m("counter-amount-ignored", "QuotaCounter.ts", "used(record, kind) + amount <= limit", "used(record, kind) < limit"),
  m("counter-adds-one", "QuotaCounter.ts", "[kind]: used(record, kind) + amount }", "[kind]: used(record, kind) + 1 }"),
  m("counter-default-2", "QuotaCounter.ts", "limit: number, amount = 1)", "limit: number, amount = 2)"),
];

export const EQUIVALENT = [
  { id: "cell-mode-high-bits", file: "src/h3Res5.ts", find: "& 15n) !== 1n) return false;",
    witness: "the mode field is bits 59-62, but HEX15 admits only 15 hex digits, so bits 60-63 of every index that "
      + "reaches this line are 0: `& 15n` and `& 1n` give the same value for every input, and no test can tell a mask "
      + "change apart. The bit-63 (reserved) check was not written for the same reason." },
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
      ["a subject unmutated", floorRefusal(MUTATIONS.filter((x) => x.file !== "src/h3Res5.ts").concat(
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
