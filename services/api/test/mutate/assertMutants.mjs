#!/usr/bin/env node
/**
 * Mutation population for T-0280: appAssert.ts (Apple's assertion steps: CBOR shape, 37-byte authenticatorData, the
 * nonce over the challenge, ECDSA P-256 by the stored key, rpIdHash, the unsigned counter), attestStore.ts (the
 * /attest/challenge reservation - per-device hour, global day, every write guarded, the prunes - and the assertion
 * commit: counter strictly above the stored one, key and live challenge in the batch) and attest.ts (the challenge
 * route's limit and device, the assert route's body, sub and act). The runner is attestMutants.mjs's (T-0278),
 * because touches: is services/api/ and check-mutate-population.py reads Sources/ and services/etl/etl/ only.
 *
 *   node services/api/test/mutate/assertMutants.mjs                  run the population
 *   node services/api/test/mutate/assertMutants.mjs --prove-vacuity  every mutant must report MISSED with no tests
 *   node services/api/test/mutate/assertMutants.mjs --prove-floor    the floor refuses on its arms; runs no tests
 *   ... --only=<id>,<id>                                              run only the named entries; an unknown id refuses
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
const OUT = resolve(API, "..", "..", ".build", "mutate-assert");

export const MIN_MUTATIONS = 40;
export const SUBJECTS = ["src/appAssert.ts", "src/attestStore.ts", "src/attest.ts"];
const TESTS = ["test/attestAssert.test.ts", "test/attestRate.test.ts", "test/attestAccept.test.ts", "test/attestVerify.test.ts",
  "test/requestReadSites.test.ts", "test/killSwitchRoutes.test.ts", "test/routes.test.ts"];

const m = (id, file, find, replace) => ({ id, file: `src/${file}`, find, replace });
export const MUTATIONS = [
  m("as-cbor-keys-unchecked", "appAssert.ts", " || [...object.keys()].sort().join() !== \"authenticatorData,signature\"", ""),
  m("as-length-unchecked", "appAssert.ts", "if (authData.length !== ASSERTION_AUTH_DATA_LENGTH) reject(\"authenticatorData is not 37 bytes\");", ""),
  m("as-length-minimum", "appAssert.ts", "if (authData.length !== ASSERTION_AUTH_DATA_LENGTH)", "if (authData.length < ASSERTION_AUTH_DATA_LENGTH)"),
  m("as-length-38", "appAssert.ts", "ASSERTION_AUTH_DATA_LENGTH = 37;", "ASSERTION_AUTH_DATA_LENGTH = 38;"),
  m("as-nonce-without-clientdata", "appAssert.ts", "signed.set(clientDataHash, authData.length);", ""),
  m("as-clientdata-not-challenge", "appAssert.ts", "new TextEncoder().encode(input.challenge)", "new TextEncoder().encode(input.challenge.slice(1))"),
  m("as-signature-unchecked", "appAssert.ts", "if (!valid) reject(\"signature is not the stored key's over the nonce\");", ""),
  m("as-signature-over-authdata", "appAssert.ts", "ecdsaRaw(signature, 32), nonce);", "ecdsaRaw(signature, 32), signed);"),
  m("as-curve-p384", "appAssert.ts", "namedCurve: \"P-256\" }", "namedCurve: \"P-384\" }"),
  m("as-hash-sha384", "appAssert.ts", "{ name: \"ECDSA\", hash: \"SHA-256\" }, key", "{ name: \"ECDSA\", hash: \"SHA-384\" }, key"),
  m("as-ecdsa-size", "appAssert.ts", "ecdsaRaw(signature, 32)", "ecdsaRaw(signature, 33)"),
  m("as-rpid-unchecked", "appAssert.ts", "if (!sameBytes(authData.subarray(0, 32), await sha256(new TextEncoder().encode(APP_ATTEST_APP_ID)))) reject(\"rpIdHash is not the App ID's\");", ""),
  m("as-counter-signed", "appAssert.ts", " | authData[36]!) >>> 0;", " | authData[36]!);"),
  m("as-counter-high-byte-dropped", "appAssert.ts", "const counter = ((authData[33]! << 24) | ", "const counter = ("),
  m("as-counter-offset", "appAssert.ts", "(authData[34]! << 16) | (authData[35]! << 8) | authData[36]!)", "(authData[34]! << 16) | (authData[35]! << 8) | authData[32]!)"),
  m("store-device-limit-inclusive", "attestStore.ts", "WHERE bucket = ?1 AND slot = ?2), 0) < ?3", "WHERE bucket = ?1 AND slot = ?2), 0) <= ?3"),
  m("store-device-limit-unchecked", "attestStore.ts", "WHERE COALESCE((SELECT issued FROM attest_challenge_counts WHERE bucket = ?1 AND slot = ?2), 0) < ?3\n  AND ", "WHERE "),
  m("store-global-limit-inclusive", "attestStore.ts", "AND slot = ?4), 0) < ?5", "AND slot = ?4), 0) <= ?5"),
  m("store-global-limit-unchecked", "attestStore.ts", "\n  AND COALESCE((SELECT issued FROM attest_challenge_counts WHERE bucket = '${GLOBAL_BUCKET}' AND slot = ?4), 0) < ?5", ""),
  m("store-global-unguarded", "attestStore.ts", "SELECT '${GLOBAL_BUCKET}', ?1, 1 WHERE changes() = 1", "SELECT '${GLOBAL_BUCKET}', ?1, 1 WHERE 1"),
  m("store-insert-unguarded", "attestStore.ts", "SELECT ?1, ?2 WHERE changes() = 1\"", "SELECT ?1, ?2 WHERE 1\""),
  m("store-prune-challenges-unguarded", "attestStore.ts", "\n  AND EXISTS (SELECT 1 FROM attest_challenges WHERE challenge = ?2)`;", "`;"),
  m("store-prune-challenges-live", "attestStore.ts", "DELETE FROM attest_challenges WHERE expires_at <= ?1", "DELETE FROM attest_challenges WHERE expires_at <= ?1 + 1"),
  m("store-prune-counts-unguarded", "attestStore.ts", "\n  AND EXISTS (SELECT 1 FROM attest_challenges WHERE challenge = ?3)`;\n\n/**", "`;\n\n/**"),
  m("store-prune-day-inclusive", "attestStore.ts", "AND slot < ?1)", "AND slot <= ?1)"),
  m("store-prune-hour-inclusive", "attestStore.ts", "AND slot < ?2)", "AND slot <= ?2)"),
  m("store-hour-unwindowed", "attestStore.ts", "const hour = Math.floor(nowMs / HOUR_MS) * HOUR_MS;", "const hour = nowMs;"),
  m("store-day-is-hour", "attestStore.ts", "const day = Math.floor(nowMs / DAY_MS) * DAY_MS;", "const day = hour;"),
  m("store-device-limit-11", "attestStore.ts", "ATTEST_CHALLENGES_PER_DEVICE_HOUR = 10;", "ATTEST_CHALLENGES_PER_DEVICE_HOUR = 11;"),
  m("store-day-limit-10001", "attestStore.ts", "ATTEST_CHALLENGES_PER_DAY = 10_000;", "ATTEST_CHALLENGES_PER_DAY = 10_001;"),
  m("store-device-bucket-shared", "attestStore.ts", ".bind(`device:${device}`, hour,", ".bind(\"device:all\", hour,"),
  m("store-issued-unchecked", "attestStore.ts", "return results[2]?.meta.changes === 1;", "return true;"),
  m("store-counter-ge", "attestStore.ts", "WHERE ?2 > COALESCE((SELECT sign_count", "WHERE ?2 >= COALESCE((SELECT sign_count"),
  m("store-counter-unguarded", "attestStore.ts", "WHERE ?2 > COALESCE((SELECT sign_count FROM attest_sign_counts WHERE key_id = ?1), 0)\n  AND EXISTS", "WHERE EXISTS"),
  m("store-commit-key-unchecked", "attestStore.ts", "\n  AND EXISTS (SELECT 1 FROM attested_keys WHERE key_id = ?1)", ""),
  m("store-commit-challenge-unchecked", "attestStore.ts", "\n  AND EXISTS (SELECT 1 FROM attest_challenges WHERE challenge = ?3 AND expires_at > ?4)", ""),
  m("store-commit-expiry-inclusive", "attestStore.ts", "challenge = ?3 AND expires_at > ?4", "challenge = ?3 AND expires_at >= ?4"),
  m("store-commit-update-nothing", "attestStore.ts", "DO UPDATE SET sign_count = excluded.sign_count", "DO NOTHING"),
  m("store-commit-unchecked", "attestStore.ts", "return stored?.meta.changes === 1;", "return true;"),
  m("store-stored-count-default-1", "attestStore.ts", "COALESCE(c.sign_count, 0)", "COALESCE(c.sign_count, 1)"),
  m("store-device-is-key", "attestStore.ts", "k.device_id AS device_id", "k.key_id AS device_id"),
  m("attest-challenge-unlimited", "attest.ts", "if (!(await issueChallenge(deps.db, challenge, deviceIdentity(req).userId, nowMs))) return LIMITED();",
    "await issueChallenge(deps.db, challenge, deviceIdentity(req).userId, nowMs);"),
  m("attest-limited-status-503", "attest.ts", "json({ error: \"challenge_rate_limited\" }, 429)", "json({ error: \"challenge_rate_limited\" }, 503)"),
  m("assert-body-extra-allowed", "attest.ts", "if (Object.keys(body).filter((k) => k !== \"appAccountToken\").sort().join() !== ASSERT_KEYS.join()) return INVALID_ASSERTION();", ""),
  m("assert-token-unchecked", "attest.ts", "if (\"appAccountToken\" in body && (act === undefined || !UUID.test(act))) return INVALID_ASSERTION();", ""),
  m("assert-commit-ignored", "attest.ts", "if (!(await commitAssertion(deps.db, keyId, counter, challenge, nowMs))) return INVALID_ASSERTION();",
    "await commitAssertion(deps.db, keyId, counter, challenge, nowMs);"),
  m("assert-sub-is-key", "attest.ts", "const sub = key.deviceId;", "const sub = keyId;"),
  m("assert-act-dropped", "attest.ts", "const sub = key.deviceId;\n  const session = await signSession(deps.secret, act === undefined ? { sub } : { sub, act }, nowMs);",
    "const sub = key.deviceId;\n  const session = await signSession(deps.secret, { sub }, nowMs);"),
  m("assert-act-not-lowercased", "attest.ts", "const act = typeof appAccountToken === \"string\" ? appAccountToken.toLowerCase() : undefined;\n  if (\"appAccountToken\" in body && (act === undefined || !UUID.test(act))) return INVALID_ASSERTION();",
    "const act = typeof appAccountToken === \"string\" ? appAccountToken : undefined;\n  if (\"appAccountToken\" in body && (act === undefined || !UUID.test(act.toLowerCase()))) return INVALID_ASSERTION();"),
];

export const EQUIVALENT = [
  { id: "as-counter-ge", file: "src/appAssert.ts", find: "if (!(counter > input.storedCounter))",
    witness: "COMMIT_COUNTER re-checks `?2 > COALESCE(stored, 0)` inside the batch, so an equal counter that passes a widened "
      + "in-process check commits nothing and answers 400 with nothing written - the early check only saves the batch. That "
      + "clause is not this entry's own witness: it is mutated by store-counter-ge and store-counter-unguarded, which the row "
      + "'a rival commits counter 6 after the read' must catch by moving the stored counter between the read and the batch" },
  { id: "assert-live-unchecked", file: "src/attest.ts", find: "if (!(await challengeIsLive(deps.db, challenge, nowMs))) return INVALID_ASSERTION();",
    witness: "COMMIT_COUNTER's EXISTS over the live challenge is the authority (mutated by store-commit-challenge-unchecked and "
      + "store-commit-expiry-inclusive, which the rows 'the challenge is consumed after the read' and 'the batch sees the "
      + "challenge expiring at now' must catch), so an unknown or expired challenge is 400 with nothing written whether or "
      + "not the early read refuses it" },
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
      ["a subject unmutated", floorRefusal(MUTATIONS.filter((x) => x.file !== "src/attest.ts").concat(
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
