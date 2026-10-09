#!/usr/bin/env node
/**
 * Mutation population for GET and POST /ledger (T-0302): every validation branch of the body (src/ledger.ts parseEntry),
 * the session gate, the window bound on the read and on the purge, the user scoping of the read, the write and the
 * purge, the idempotent insert, the wiring in ROUTES (src/index.ts), the deletion in DELETE /account
 * (src/accountStore.ts) and the table's columns and keys (migrations/0008_surprise_ledger.sql); T-0304: the session sub
 * as the only identity, by behaviour, and the per-user daily write cap. The regionMutants.mjs shape.
 *
 *   node services/api/test/mutate/ledgerMutants.mjs                  run the population
 *   node services/api/test/mutate/ledgerMutants.mjs --prove-vacuity  every mutant must report MISSED with no tests
 *   node services/api/test/mutate/ledgerMutants.mjs --prove-floor    the floor refuses on its arms; runs no tests
 *   ... --only=<id>,<id>                                               run only the named entries
 *   ... --tests=<file>,<file>                                          run against those test files instead of TESTS
 *                                                                      (the MISSED-before half of a before/after pair)
 *
 * WHAT COUNTS. CAUGHT only when vitest's JSON report names a FAILED test. A run that fails with no named failure (a
 * mutant that does not load) is a TRAP and does not count. An anchor that does not occur exactly once is STALE and the
 * run refuses before mutating anything. Pass condition: caught == the mutants run. THE FLOOR is literal:
 * MIN_MUTATIONS, and every SUBJECT is mutated by at least one entry. The source guards (requestReadSites,
 * configAnswerPath's digest) are deliberately NOT in TESTS: a mutant must be caught by behaviour, not by a hash.
 */
import { spawnSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { onlyIds } from "./onlyIds.mjs";

const API = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const OUT = resolve(API, "..", "..", ".build", "mutate-ledger");

export const MIN_MUTATIONS = 61;
export const SUBJECTS = ["src/ledger.ts", "src/index.ts", "src/accountStore.ts", "migrations/0008_surprise_ledger.sql"];
const TESTS = ["test/ledger.test.ts", "test/ledgerWindow.test.ts", "test/migrationColumns.test.ts", "test/accountDelete.test.ts",
  "test/routes.test.ts", "test/killSwitchRoutes.test.ts", "test/ledgerIdentity.test.ts", "test/ledgerCap.test.ts"];

const m = (id, file, find, replace) => ({ id, file: file.startsWith("migrations/") ? file : `src/${file}`, find, replace });
const L = "ledger.ts";
const MIG = "migrations/0008_surprise_ledger.sql";
const OBJECT = "return { problem: \"the body must be a JSON object\" };";
const ROUTE = "  \"/ledger\": (req, env) => handleLedger(req, ledgerDepsFromEnv(env)),\n";
const LAST_COLUMN = "  day TEXT NOT NULL CHECK (length(day) = 10),\n";
export const MUTATIONS = [
  // R3: every validation branch of the body.
  m("not-json-accepted", L, "return json({ error: \"invalid_request\", detail: \"the body is not JSON\" }, 400);", "return json({ recorded: true }, 200);"),
  m("object-check-dropped", L, `  if (raw === null || typeof raw !== "object" || Array.isArray(raw)) ${OBJECT}\n`, ""),
  m("array-accepted", L, `|| Array.isArray(raw)) ${OBJECT}`, `) ${OBJECT}`),
  m("keys-whitelist-dropped", L, "  if (Object.keys(raw).sort().join() !== BODY_KEYS.join()) return { problem: \"the body must be exactly {place_id, cell}\" };\n", ""),
  m("keys-superset-accepted", L, "Object.keys(raw).sort().join() !== BODY_KEYS.join()", "!BODY_KEYS.every((k) => Object.keys(raw).includes(k))"),
  m("place-type-dropped", L, "typeof placeId !== \"string\" || !PLACE_ID.test(placeId)", "!PLACE_ID.test(placeId)"),
  m("place-leading-zero", L, "/^[1-9][0-9]{0,18}$/", "/^[0-9]{1,19}$/"),
  m("place-unanchored-end", L, "[0-9]{0,18}$/", "[0-9]{0,18}/"),
  m("place-unanchored-start", L, "/^[1-9]", "/[1-9]"),
  m("place-digits-narrowed", L, "[0-9]{0,18}$/", "[0-9]{0,17}$/"),
  m("place-max-dropped", L, " || BigInt(placeId) > MAX_PLACE_ID", ""),
  m("place-max-inclusive", L, "BigInt(placeId) > MAX_PLACE_ID", "BigInt(placeId) >= MAX_PLACE_ID"),
  m("place-max-off-by-one", L, "MAX_PLACE_ID = 9223372036854775807n", "MAX_PLACE_ID = 9223372036854775808n"),
  m("cell-check-dropped", L, "typeof cell !== \"string\" || !isResolution5Cell(cell)", "typeof cell !== \"string\""),
  // R1, R6: the gates before the body.
  m("method-any", L, "if (req.method !== \"GET\" && req.method !== \"POST\") return", "if (req.method === \"HEAD\") return"),
  m("secret-check-dropped", L, "  if (deps.secret === null) return json({ error: \"auth_unavailable\" }, 503);\n", ""),
  m("unauthorized-passes", L, "if (user === null) return", "if (user === null && false) return"),
  m("unverified-is-unidentified", L, "?.sub ?? null);", "?.sub ?? \"unidentified\");"),
  m("legacy-header-identity", L, "return match === null ? null :", "return match === null ? req.headers.get(\"x-scenic-device\") :"),
  // R4, R5: the window bound on the read and on the purge, and the day written.
  m("window-89", L, "LEDGER_WINDOW_DAYS = 90", "LEDGER_WINDOW_DAYS = 89"),
  m("window-91", L, "LEDGER_WINDOW_DAYS = 90", "LEDGER_WINDOW_DAYS = 91"),
  m("read-bound-strict", L, "AND day >= ?2", "AND day > ?2"),
  m("purge-bound-inclusive", L, "WHERE day < ?5", "WHERE day <= ?5"),
  m("purge-dropped", L, "      db.prepare(PURGE_LEDGER).bind(user, parsed.placeId, today, LEDGER_DAILY_CAP, first),\n", ""),
  m("written-day-is-first", L, "SELECT ?1, ?2, ?6, ?3 WHERE", "SELECT ?1, ?2, ?6, ?5 WHERE"),
  m("order-ascending", L, "ORDER BY day DESC", "ORDER BY day ASC"),
  m("insert-replaces", L, "DO NOTHING", "DO UPDATE SET cell = excluded.cell"),
  // R1, R4, R5: the user scoping of the read, the write and the purge.
  m("read-ignores-user", L, "WHERE user_id = ?1 AND day >= ?2", "WHERE ?1 IS NOT NULL AND day >= ?2"),
  m("write-other-user", L, "SELECT ?1, ?2, ?6, ?3 WHERE", "SELECT 'unidentified', ?2, ?6, ?3 WHERE"),
  m("purge-caller-only", L, "WHERE day < ?5 AND", "WHERE day < ?5 AND user_id = ?1 AND"),
  // D1 failures answer 503, never a success.
  m("write-failure-answers-200", L, "  } catch {\n    return UNAVAILABLE();\n  }\n  return admitted === 1",
    "  } catch {\n    return json({ recorded: true }, 200);\n  }\n  return admitted === 1"),
  m("read-failure-answers-empty", L, "  } catch {\n    return UNAVAILABLE();\n  }\n}\n", "  } catch {\n    return json({ places: [] }, 200);\n  }\n}\n"),
  // R7: the wiring, outside the kill switch.
  m("route-unwired", "index.ts", ROUTE, ""),
  m("route-killable", "index.ts", ROUTE, "  \"/ledger\": (req, env) => (env.KILL === \"1\" ? Promise.resolve(new Response(\"{}\", { status: 503 })) "
    + ": handleLedger(req, ledgerDepsFromEnv(env))),\n"),
  // R8 (P-PRIV-04): the deletion.
  m("account-ledger-delete-dropped", "accountStore.ts", "    db.prepare(DELETE_LEDGER).bind(user.deviceId, user.appleSub),\n", ""),
  m("account-ledger-session-device-only", "accountStore.ts", "WHERE user_id IN (SELECT device FROM (${USER_DEVICES}))",
    "WHERE user_id = ?1 AND (?2 IS NULL OR ?2 IS NOT NULL)"),
  // R2, R9 (P-PRIV-05): the columns and the keys.
  m("ledger-address-column", MIG, LAST_COLUMN, `${LAST_COLUMN}  address TEXT,\n`),
  m("ledger-lat-column", MIG, LAST_COLUMN, `${LAST_COLUMN}  lat REAL,\n`),
  m("ledger-key-without-day", MIG, "PRIMARY KEY (user_id, place_id, day)", "PRIMARY KEY (user_id, place_id)"),
  m("ledger-unique-across-users", MIG, "PRIMARY KEY (user_id, place_id, day)", "PRIMARY KEY (user_id, place_id, day),\n  UNIQUE (place_id, day)"),
  // T-0304 R4: the user is the session sub, by behaviour (rv1-t0302 recordable a; MISSED by the T-0302 TESTS).
  m("rv-user-is-apple-claim", L, "((await verifySession(secret, match[1]!, nowMs))?.sub ?? null)",
    "(((c) => c?.apple ?? c?.sub ?? null)(await verifySession(secret, match[1]!, nowMs)))"),
  m("rv-user-is-act-claim", L, "((await verifySession(secret, match[1]!, nowMs))?.sub ?? null)",
    "(((c) => c?.act ?? c?.sub ?? null)(await verifySession(secret, match[1]!, nowMs)))"),
  m("get-scoped-by-legacy-device-header", L, "return readLedger(deps.db, user, first);",
    "return readLedger(deps.db, req.headers.get(\"x-scenic-device\") ?? user, first);"),
  m("post-scoped-by-legacy-device-header", L, "const user = await caller(req, deps.secret, now.getTime());",
    "const user = await caller(req, deps.secret, now.getTime()).then((u) => u && (req.headers.get(\"x-scenic-device\") ?? u));"),
  // T-0304 R1-R3: the daily write cap, its every bound and branch.
  m("cap-unbounded", L, "LEDGER_DAILY_CAP = DAILY_SURPRISE_QUOTA.paid;", "LEDGER_DAILY_CAP = Number.MAX_SAFE_INTEGER;"),
  m("cap-plus-one", L, "LEDGER_DAILY_CAP = DAILY_SURPRISE_QUOTA.paid;", "LEDGER_DAILY_CAP = DAILY_SURPRISE_QUOTA.paid + 1;"),
  m("cap-minus-one", L, "LEDGER_DAILY_CAP = DAILY_SURPRISE_QUOTA.paid;", "LEDGER_DAILY_CAP = DAILY_SURPRISE_QUOTA.paid - 1;"),
  m("cap-free-tier", L, "LEDGER_DAILY_CAP = DAILY_SURPRISE_QUOTA.paid;", "LEDGER_DAILY_CAP = DAILY_SURPRISE_QUOTA.free;"),
  m("cap-inclusive", L, "AND day = ?3) < ?4", "AND day = ?3) <= ?4"),
  m("cap-counts-every-day", L, "WHERE user_id = ?1 AND day = ?3) < ?4", "WHERE user_id = ?1) < ?4"),
  m("cap-counts-every-user", L, "FROM surprise_ledger WHERE user_id = ?1 AND day = ?3) < ?4", "FROM surprise_ledger WHERE day = ?3) < ?4"),
  m("cap-refuses-held", L, "OR EXISTS (SELECT 1 FROM surprise_ledger WHERE user_id = ?1 AND place_id = ?2 AND day = ?3))", "OR 0)"),
  m("cap-held-any-user", L, "WHERE user_id = ?1 AND place_id = ?2 AND day = ?3", "WHERE place_id = ?2 AND day = ?3"),
  m("cap-held-any-day", L, "AND place_id = ?2 AND day = ?3))", "AND place_id = ?2))"),
  m("cap-refusal-answers-200", L, "json({ error: \"ledger_daily_cap\" }, 429)", "json({ recorded: true }, 200)"),
  m("cap-admission-ignored", L, "return admitted === 1 ?", "return true ?"),
  m("cap-purge-unguarded", L, "WHERE day < ?5 AND ${ADMITTED}`", "WHERE day < ?5`"),
  m("cap-insert-unguarded", L, "SELECT ?1, ?2, ?6, ?3 WHERE ${ADMITTED} `", "SELECT ?1, ?2, ?6, ?3 WHERE true `"),
  m("cap-today-is-first", L, ".bind(user, parsed.placeId, today, LEDGER_DAILY_CAP),", ".bind(user, parsed.placeId, first, LEDGER_DAILY_CAP),"),
  // rv1-t0304: a refusal purges nothing of the writer's own; an admission row D1 does not return admits nothing.
  m("rv-refusal-purges-own-stale", L, "WHERE day < ?5 AND ${ADMITTED}`", "WHERE day < ?5 AND (user_id = ?1 OR ${ADMITTED})`"),
  m("rv-no-admission-row-admits", L, "admitted = admit?.results[0]?.admitted;", "admitted = admit?.results[0]?.admitted ?? 1;"),
];

export const EQUIVALENT = [];

export function floorRefusal(mutations = MUTATIONS, subjects = SUBJECTS) {
  if (mutations.length < MIN_MUTATIONS) return `population ${mutations.length} is below the floor ${MIN_MUTATIONS}`;
  for (const subject of subjects) {
    if (!mutations.some((x) => x.file === subject)) return `subject ${subject} has no mutation`;
  }
  return null;
}

function vitest(tests, extra, tag) {
  mkdirSync(OUT, { recursive: true });
  const report = join(OUT, `${tag}.json`);
  writeFileSync(report, "");
  const bin = join(API, "node_modules", "vitest", "vitest.mjs");
  const run = spawnSync(process.execPath, [bin, "run", ...tests, "--reporter=json", `--outputFile=${report}`, ...extra],
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
  const only = onlyIds(argv, MUTATIONS.map((x) => x.id));
  if (argv.includes("--prove-floor")) {
    const arms = [
      ["empty table", floorRefusal([])],
      ["one short of the floor", floorRefusal(MUTATIONS.slice(0, MIN_MUTATIONS - 1))],
      ["a subject unmutated", floorRefusal(MUTATIONS.filter((x) => x.file !== "src/accountStore.ts").concat(
        Array.from({ length: MIN_MUTATIONS }, () => MUTATIONS.find((x) => x.file !== "src/accountStore.ts"))))],
      ["a new subject with none", floorRefusal(MUTATIONS, [...SUBJECTS, "src/newModule.ts"])],
    ];
    for (const [arm, refusal] of arms) console.log(`prove-floor ${arm}: ${refusal === null ? "QUIET (WRONG)" : `REFUSED - ${refusal}`}`);
    const real = floorRefusal();
    console.log(`prove-floor real population: ${real === null ? "quiet" : `REFUSED - ${real}`}`);
    return arms.every(([, r]) => r !== null) && real === null ? 0 : 1;
  }

  const refusal = floorRefusal();
  if (refusal) { console.log(`REFUSING TO RUN: ${refusal}`); return 2; }
  if (new Set(MUTATIONS.map((x) => x.id)).size !== MUTATIONS.length) { console.log("REFUSING TO RUN: duplicate mutation id"); return 2; }
  for (const x of [...MUTATIONS, ...EQUIVALENT]) {
    const count = readFileSync(join(API, x.file), "utf8").split(x.find).length - 1;
    if (count !== 1) { console.log(`STALE ${x.id}: anchor occurs ${count} times in ${x.file}`); return 2; }
  }
  const dirty = spawnSync("git", ["status", "--porcelain", "--", "src", "migrations"], { cwd: API, encoding: "utf8" });
  if (dirty.status !== 0 || dirty.stdout.trim() !== "") { console.log("REFUSING TO RUN: services/api/src or migrations is not clean"); return 2; }

  const prove = argv.includes("--prove-vacuity");
  const tests = argv.find((a) => a.startsWith("--tests="))?.slice("--tests=".length).split(",") ?? TESTS;
  const run = only === null ? MUTATIONS : MUTATIONS.filter((x) => only.includes(x.id));
  const extra = prove ? ["-t", "^no test is named this$", "--passWithNoTests"] : [];
  console.log(`population mutations=${MUTATIONS.length} (floor ${MIN_MUTATIONS}) equivalent=${EQUIVALENT.length} `
    + `subjects=${SUBJECTS.length} tests=${tests.length}${tests === TESTS ? "" : ` OVERRIDE=${tests.join(",")}`}`
    + `${prove ? " PROVE-VACUITY" : ""}${only ? ` ONLY=${run.length}` : ""}`);
  if (!prove) {
    const base = vitest(tests, [], "baseline");
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
      result = vitest(tests, extra, x.id);
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
