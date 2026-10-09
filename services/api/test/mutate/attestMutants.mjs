#!/usr/bin/env node
/**
 * Mutation population for App Attest and the session identity (T-0278): cbor.ts (the CBOR subset), appAttest.ts
 * (Apple's verification steps 1-9 and the root pin), x509.ts's extension values, attestStore.ts (challenge TTL,
 * pruning, single use), attest.ts (the routes' body, secret and answers), sessionJwt.ts (HS256, claims, the iat/exp
 * bounds) and sessionIdentity.ts with routerDeps.ts's identify (JWT first, no fallthrough, the migration flag). The
 * runner is tierMutants.mjs's, because touches: is services/api/ and check-mutate-population.py reads Sources/ and
 * services/etl/etl/ only.
 *
 *   node services/api/test/mutate/attestMutants.mjs                  run the population
 *   node services/api/test/mutate/attestMutants.mjs --prove-vacuity  every mutant must report MISSED with no tests
 *   node services/api/test/mutate/attestMutants.mjs --prove-floor    the floor refuses on its arms; runs no tests
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
import { onlyIds } from "./onlyIds.mjs";

const API = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const OUT = resolve(API, "..", "..", ".build", "mutate-attest");

export const MIN_MUTATIONS = 93;
export const SUBJECTS = ["src/cbor.ts", "src/appAttest.ts", "src/x509.ts", "src/attestStore.ts", "src/attest.ts", "src/sessionJwt.ts",
  "src/sessionIdentity.ts", "src/routerDeps.ts", "src/plan.ts", "src/trip.ts", "src/loop.ts"];
const TESTS = ["test/attestVerify.test.ts", "test/attestAccept.test.ts", "test/sessionIdentity.test.ts", "test/requestReadSites.test.ts",
  "test/asnRootPin.test.ts", "test/sessionCarriesAct.test.ts"];

const m = (id, file, find, replace) => ({ id, file: `src/${file}`, find, replace });
export const MUTATIONS = [
  m("cbor-trailing-accepted", "cbor.ts", "if (next !== bytes.length) fail(\"trailing bytes\");", ""),
  m("cbor-duplicate-key-accepted", "cbor.ts", "if (out.has(key.value)) fail(\"duplicate map key\");", ""),
  m("cbor-one-byte-length-size", "cbor.ts", "const size = 1 << (info - 24);", "const size = 1 << (info - 23);"),
  m("cbor-little-endian", "cbor.ts", "arg = arg * 256 + bytes[next + i]!;", "arg = arg + bytes[next + i]! * 256 ** i;"),
  m("cbor-bytes-as-text", "cbor.ts", "if (major === 2) return { value: raw, next: end };", ""),
  m("aa-root-unpinned", "appAttest.ts", "if ((await sha256Hex(trust.rootDer)) !== trust.rootSha256) reject(\"root is not the pinned root\");", ""),
  m("aa-validity-unchecked", "appAttest.ts", "if (!(cert.notBefore <= now && now <= cert.notAfter)) reject", "if (false) reject"),
  m("aa-notbefore-exclusive", "appAttest.ts", "cert.notBefore <= now &&", "cert.notBefore < now &&"),
  m("aa-notafter-exclusive", "appAttest.ts", "now <= cert.notAfter)", "now < cert.notAfter)"),
  m("aa-intermediate-unsigned", "appAttest.ts", "if (!(await signedBy(intermediate, root))) reject(\"intermediate not signed by root\");", ""),
  m("aa-leaf-unsigned", "appAttest.ts", "if (!(await signedBy(leaf, intermediate))) reject(\"credCert not signed by intermediate\");", ""),
  m("aa-nonce-unchecked", "appAttest.ts", "if (!sameBytes(nonceOf(leaf), await sha256(signed))) reject(\"nonce mismatch\");", "nonceOf(leaf);"),
  m("aa-nonce-without-client-data", "appAttest.ts", "signed.set(clientDataHash, authData.length);", ""),
  m("aa-nonce-repeat-accepted", "appAttest.ts", " || leaf.extensions.lastIndexOf(OID_APP_ATTEST_NONCE) !== at", ""),
  m("aa-nonce-two-elements", "appAttest.ts", "if (parts.length !== 1) reject(\"nonce sequence is not one element\");", ""),
  m("aa-nonce-any-tag", "appAttest.ts", "expectTag(parts[0], 0xa1).value", "parts[0]!.value"),
  m("aa-keyid-unchecked", "appAttest.ts", "if (!sameBytes(await sha256(publicPoint(leaf)), input.keyId)) reject(\"keyId is not the credCert key's hash\");", ""),
  m("aa-rpid-unchecked", "appAttest.ts", "if (!sameBytes(authData.subarray(0, 32), await sha256(new TextEncoder().encode(APP_ATTEST_APP_ID)))) reject(\"rpIdHash is not the App ID's\");", ""),
  m("aa-rpid-bundle-only", "appAttest.ts", "new TextEncoder().encode(APP_ATTEST_APP_ID)", "new TextEncoder().encode(APP_BUNDLE_ID)"),
  m("aa-counter-low-byte", "appAttest.ts", "const counter = ((authData[33]! << 24) | (authData[34]! << 16) | (authData[35]! << 8) | authData[36]!) >>> 0;",
    "const counter = authData[36]!;"),
  m("aa-counter-unchecked", "appAttest.ts", "if (counter !== 0) reject(\"counter is not 0\");", ""),
  m("aa-develop-without-flag", "appAttest.ts", "aaguid === AAGUID_DEVELOP && trust.allowDevelop", "aaguid === AAGUID_DEVELOP"),
  m("aa-aaguid-prefix", "appAttest.ts", "aaguid === AAGUID_PRODUCTION ? \"production\"", "aaguid.startsWith(\"appattest\") ? \"production\""),
  m("aa-credid-length-unchecked", "appAttest.ts", "if (authData[53]! * 256 + authData[54]! !== 32) reject(\"credentialId is not 32 bytes\");", ""),
  m("aa-credid-unchecked", "appAttest.ts", "if (!sameBytes(authData.subarray(55, 87), input.keyId)) reject(\"credentialId is not the keyId\");", ""),
  m("aa-x5c-at-least-two", "appAttest.ts", "x5c.length !== 2", "x5c.length < 2"),
  m("aa-receipt-unchecked", "appAttest.ts", "if (!(statement.get(\"receipt\") instanceof Uint8Array)) reject(\"receipt is not bytes\");", ""),
  m("aa-fmt-unchecked", "appAttest.ts", "if (top.get(\"fmt\") !== \"apple-appattest\") reject(\"fmt is not apple-appattest\");", ""),
  m("aa-map-keys-unchecked", "appAttest.ts", "if ([...value.keys()].sort().join() !== keys.join()) reject(`keys are not exactly ${keys.join()}`);", ""),
  m("aa-environment-swapped", "appAttest.ts", "? \"development\" : reject(", "? \"production\" : reject("),
  m("x509-ext-value-raw", "x509.ts", "children(expectTag(ext, 0x30)).at(-1), 0x04).value);", "children(expectTag(ext, 0x30)).at(-1), 0x04).raw);"),
  m("store-ttl-plus-1", "attestStore.ts", "CHALLENGE_TTL_MS = 300_000;", "CHALLENGE_TTL_MS = 300_001;"),
  m("store-prune-exclusive", "attestStore.ts", "DELETE FROM attest_challenges WHERE expires_at <= ?1\n", "DELETE FROM attest_challenges WHERE expires_at < ?1\n"),
  m("store-prune-dropped", "attestStore.ts", "    db.prepare(PRUNE_CHALLENGES).bind(nowMs, challenge),\n", ""),
  m("store-consume-unconditional", "attestStore.ts", "WHERE challenge = ?1 AND changes() = 1\"", "WHERE challenge = ?1\""),
  m("store-never-consumed", "attestStore.ts", "    db.prepare(CONSUME_CHALLENGE).bind(row.challenge),\n", ""),
  m("store-replace-key", "attestStore.ts", "INSERT OR IGNORE INTO attested_keys", "INSERT OR REPLACE INTO attested_keys"),
  m("store-commit-unchecked", "attestStore.ts", "return inserted?.meta.changes === 1;", "return true;"),
  m("store-attested-at-plus-1", "attestStore.ts", "row.environment, nowMs, row.challenge)", "row.environment, nowMs + 1, row.challenge)"),
  m("store-commit-without-exists", "attestStore.ts", "WHERE EXISTS (SELECT 1 FROM attest_challenges WHERE challenge = ?6 AND expires_at > ?5)",
    "WHERE ?6 IS NOT NULL"),
  m("store-commit-expiry-inclusive", "attestStore.ts", "AND expires_at > ?5)", "AND expires_at >= ?5)"),
  m("store-commit-any-challenge", "attestStore.ts", "WHERE challenge = ?6 AND expires_at", "WHERE ?6 = ?6 AND expires_at"),
  m("attest-act-dropped", "attest.ts", "  }\n  const session = await signSession(deps.secret, act === undefined ? { sub } : { sub, act }, nowMs);", "  }\n  const session = await signSession(deps.secret, { sub }, nowMs);"),
  m("attest-device-case-kept", "attest.ts", "const sub = device.toLowerCase();", "const sub = device;"),
  m("attest-extra-body-key", "attest.ts", "if (Object.keys(body).filter((k) => k !== \"appAccountToken\").sort().join() !== BODY_KEYS.join()) return INVALID();", ""),
  m("attest-act-unvalidated", "attest.ts", " || (\"appAccountToken\" in body && (act === undefined || !UUID.test(act)))", ""),
  // T-0322 pre-review M3, closed by class: every bound of the ruled shape at the /attest call site.
  m("attest-act-tail-admitted", "attest.ts", "!UUID.test(act)))) return INVALID();", "!UUID.test(act.slice(0, 36))))) return INVALID();"),
  m("attest-act-head-admitted", "attest.ts", "!UUID.test(act)))) return INVALID();", "!UUID.test(act.slice(-36))))) return INVALID();"),
  m("attest-act-short-padded", "attest.ts", "!UUID.test(act)))) return INVALID();", "!UUID.test(act.padEnd(36, \"0\"))))) return INVALID();"),
  m("attest-act-hyphens-unplaced", "attest.ts", "!UUID.test(act)))) return INVALID();", "!/^[0-9a-f-]{36}$/.test(act)))) return INVALID();"),
  m("attest-act-before-0-admitted", "attest.ts", "!UUID.test(act)))) return INVALID();", "!/^[/-9a-f]{8}-[/-9a-f]{4}-[/-9a-f]{4}-[/-9a-f]{4}-[/-9a-f]{12}$/.test(act)))) return INVALID();"),
  m("attest-act-past-9-admitted", "attest.ts", "!UUID.test(act)))) return INVALID();", "!/^[0-:a-f]{8}-[0-:a-f]{4}-[0-:a-f]{4}-[0-:a-f]{4}-[0-:a-f]{12}$/.test(act)))) return INVALID();"),
  m("attest-act-before-a-admitted", "attest.ts", "!UUID.test(act)))) return INVALID();", "!/^[0-9`-f]{8}-[0-9`-f]{4}-[0-9`-f]{4}-[0-9`-f]{4}-[0-9`-f]{12}$/.test(act)))) return INVALID();"),
  m("attest-act-past-f-admitted", "attest.ts", "!UUID.test(act)))) return INVALID();", "!/^[0-9a-g]{8}-[0-9a-g]{4}-[0-9a-g]{4}-[0-9a-g]{4}-[0-9a-g]{12}$/.test(act)))) return INVALID();"),
  m("attest-act-multiline-admitted", "attest.ts", "!UUID.test(act)))) return INVALID();", "!new RegExp(UUID.source, \"m\").test(act)))) return INVALID();"),
  m("attest-expires-plus-1s", "attest.ts", "new Date(session.expiresAtMs).toISOString() });\n}\n\nexport async function handleAttestAssert", "new Date(session.expiresAtMs + 1000).toISOString() });\n}\n\nexport async function handleAttestAssert"),
  m("attest-challenge-expiry-now", "attest.ts", "new Date(nowMs + CHALLENGE_TTL_MS).toISOString()", "new Date(nowMs).toISOString()"),
  m("attest-challenge-16-bytes", "attest.ts", "crypto.getRandomValues(new Uint8Array(32))", "crypto.getRandomValues(new Uint8Array(16))"),
  m("attest-challenge-without-secret", "attest.ts", "405);\n  if (deps.secret === null) return UNAVAILABLE();\n  const challenge", "405);\n  const challenge"),
  m("attest-without-secret", "attest.ts", "export async function handleAttest(req: Request, deps: AttestDeps): Promise<Response> {\n  if (req.method !== \"POST\") return json({ error: \"POST only\" }, 405);\n  if (deps.secret === null) return UNAVAILABLE();\n", "export async function handleAttest(req: Request, deps: AttestDeps): Promise<Response> {\n  if (req.method !== \"POST\") return json({ error: \"POST only\" }, 405);\n"),
  m("attest-develop-flag-any", "attest.ts", "allowDevelop: env.APP_ATTEST_ALLOW_DEVELOP === \"1\",", "allowDevelop: env.APP_ATTEST_ALLOW_DEVELOP !== undefined,"),
  m("attest-public-key-unpadded", "attest.ts", "b.toString(16).padStart(2, \"0\")", "b.toString(16)"),
  m("jwt-ttl-3601", "sessionJwt.ts", "SESSION_TTL_S = 3600;", "SESSION_TTL_S = 3601;"),
  m("jwt-min-secret-31", "sessionJwt.ts", "MIN_SECRET_LENGTH = 32;", "MIN_SECRET_LENGTH = 31;"),
  m("jwt-exp-inclusive", "sessionJwt.ts", "now < (exp as number)", "now <= (exp as number)"),
  m("jwt-now-ceil", "sessionJwt.ts", "const now = Math.floor(nowMs / 1000);", "const now = Math.ceil(nowMs / 1000);"),
  m("jwt-now-round", "sessionJwt.ts", "const now = Math.floor(nowMs / 1000);", "const now = Math.round(nowMs / 1000);"),
  m("jwt-iat-unchecked", "sessionJwt.ts", "(iat as number) <= now && ", ""),
  m("jwt-span-unchecked", "sessionJwt.ts", " || (exp as number) - (iat as number) !== SESSION_TTL_S", ""),
  m("jwt-header-unchecked", "sessionJwt.ts", " || parts[0] !== HEADER", ""),
  m("jwt-signature-unchecked", "sessionJwt.ts", "if (!(await crypto.subtle.verify(", "if (false && !(await crypto.subtle.verify("),
  m("jwt-extra-claims", "sessionJwt.ts", "keys.join() !== CLAIMS.join() || ", ""),
  m("jwt-iss-unchecked", "sessionJwt.ts", " || claims.iss !== SESSION_ISSUER", ""),
  m("jwt-sub-any-string", "sessionJwt.ts", "if (typeof sub !== \"string\" || !UUID.test(sub)) return null;", "if (typeof sub !== \"string\") return null;"),
  m("jwt-act-unchecked", "sessionJwt.ts", "if (\"act\" in claims && (typeof act !== \"string\" || !UUID.test(act))) return null;", ""),
  m("jwt-integer-unchecked", "sessionJwt.ts", "if (!Number.isSafeInteger(iat) || !Number.isSafeInteger(exp) || ", "if ("),
  // T-0322 B1: an unverifiable Bearer reads as no Bearer - legacy only under the flag (inverse), never anon ahead of it.
  m("ident-fallthrough", "sessionIdentity.ts", "if (claims === null) return env.IDENTITY_HEADERS === \"1\" ? legacy() : { userId: UNIDENTIFIED_SESSION, tier: \"anon\" };",
    "if (claims === null) return legacy();"),
  m("ident-early-anon", "sessionIdentity.ts", "  if (claims === null) return env.IDENTITY_HEADERS",
    "  if (bearer !== null && claims === null) return { userId: UNIDENTIFIED_SESSION, tier: \"anon\" };\n  if (claims === null) return env.IDENTITY_HEADERS"),
  m("ident-flag-ignored", "sessionIdentity.ts", "return env.IDENTITY_HEADERS === \"1\" ? legacy() : { userId: UNIDENTIFIED_SESSION, tier: \"anon\" };", "return legacy();"),
  m("ident-flag-any-value", "sessionIdentity.ts", "env.IDENTITY_HEADERS === \"1\"", "env.IDENTITY_HEADERS !== undefined"),
  m("ident-act-ignored", "sessionIdentity.ts", "tier: claims.act === undefined ? \"anon\" : await entitledTier(env.DB, claims.act, nowMs)", "tier: \"anon\""),
  m("ident-inactive-paid", "sessionIdentity.ts", ").status === \"active\" ? \"paid\" : \"anon\";", ").status !== \"none\" ? \"paid\" : \"anon\";"),
  m("ident-bearer-any-case", "sessionIdentity.ts", "const BEARER = /^Bearer ([A-Za-z0-9_.-]+)$/;", "const BEARER = /^Bearer ([A-Za-z0-9_.-]+)$/i;"),
  m("ident-secret-only-without-bearer", "sessionIdentity.ts", "if (secret === null) return legacy();", "if (secret === null && bearer === null) return legacy();"),
  m("deps-bearer-not-read", "routerDeps.ts", "identifySession(req.headers.get(AUTHORIZATION_HEADER), env,", "identifySession(null, env,"),
  // T-0333 R1: the flag closed, a present authorization that does not verify is 401 on /plan, /trip and /loop.
  m("reject-never", "sessionIdentity.ts", "  if (claims === null && bearer !== null && env.IDENTITY_HEADERS !== \"1\") return SESSION_REJECTED;\n", ""),
  m("reject-under-flag", "sessionIdentity.ts", " && env.IDENTITY_HEADERS !== \"1\") return SESSION_REJECTED;", ") return SESSION_REJECTED;"),
  m("reject-absent-header", "sessionIdentity.ts", "claims === null && bearer !== null &&", "claims === null &&"),
  m("reject-unmarked", "routerDeps.ts", "tier: \"anon\", rejected: true } : who;", "tier: \"anon\" } : who;"),
  m("reject-plan-unanswered", "plan.ts", "  if (who.rejected === true) return json({ error: \"session_rejected\" }, 401);\n", ""),
  m("reject-trip-unanswered", "trip.ts", "  if (who.rejected === true) return json({ error: \"session_rejected\" }, 401);\n", ""),
  m("reject-loop-unanswered", "loop.ts", "  if (who.rejected === true) return json({ error: \"session_rejected\" }, 401);\n", ""),
  m("reject-plan-after-reservation", "plan.ts", "  if (who.rejected === true) return json({ error: \"session_rejected\" }, 401);\n",
    "  if (who.rejected === true) {\n    await guardedPlan(upstream, who, async () => null).catch(() => null);\n    return json({ error: \"session_rejected\" }, 401);\n  }\n"),
];

export const EQUIVALENT = [
  { id: "cbor-depth-unbounded", file: "src/cbor.ts", find: "if (depth > MAX_DEPTH) fail(\"nested too deep\");",
    witness: "the attestation object's deepest legal item is depth 3 (map > attStmt map > x5c array > bytes), and verifyAttestation "
      + "catches EVERY throw of decodeCbor - a RangeError from unbounded recursion included - as 'not CBOR', and every object "
      + "deeper than 3 fails mapOf or the x5c / authData type checks; the cap bounds the work, not the answer" },
  { id: "aa-curve-unchecked", file: "src/appAttest.ts", find: "if (leaf.curve !== OID_P256) reject(\"credCert key is not P-256\");",
    witness: "publicPoint refuses every key whose BIT STRING is not 0x00 0x04 plus 64 bytes - an uncompressed P-256 point - so a "
      + "P-384 credCert (98 bytes) is refused either way, by the next check; the row 'credCert key on P-384' pins the answer" },
  { id: "aa-authdata-87", file: "src/appAttest.ts", find: "if (authData.length < 87) reject(\"authData truncated\");",
    witness: "the credentialId comparison sameBytes(authData.subarray(55, 87), keyId) compares lengths first, so authData shorter "
      + "than 87 bytes yields a short subarray and is refused by it; the rows 'authData cut to 86 / 54 bytes' pin the answer" },
  { id: "store-live-inclusive", file: "src/attestStore.ts", find: "AND expires_at > ?2\"",
    witness: "COMMIT_KEY re-checks `expires_at > ?5` inside the batch, so a challenge expiring at now that passed a widened read "
      + "commits nothing and answers 400 - the read only saves the verification work. That clause is not this entry's own "
      + "witness: it is mutated by store-commit-expiry-inclusive and store-commit-without-exists, CAUGHT by the rows 'the batch "
      + "sees the challenge expiring at now / 1 ms after now', which move the row between the read and the batch" },
  { id: "jwt-signature-length-unchecked", file: "src/sessionJwt.ts", find: " || signature.length !== 32",
    witness: "WebCrypto's HMAC verify compares the whole 32-byte SHA-256 MAC and answers false for a signature of any other "
      + "length, so the length check only refuses earlier; measured MISSED in the 2026-10-06 run, the row 'a signature cut "
      + "to 31 bytes' pins the unidentified answer" },
  { id: "attest-live-unchecked", file: "src/attest.ts", find: "if (!(await challengeIsLive(deps.db, challenge, nowMs))) return INVALID();",
    witness: "the same: COMMIT_KEY's EXISTS over the live challenge is the authority (mutated by store-commit-without-exists and "
      + "store-commit-any-challenge, CAUGHT by 'a concurrent attestation consumes the challenge after the read'), so an unknown "
      + "or expired challenge is 400 with nothing written whether or not the early read refuses it. The interleaved rows hook "
      + "the read, so without it they would see no gap - a property of the instrument, not of the answer" },
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
  const only = onlyIds(argv, MUTATIONS.map((x) => x.id));
  if (argv.includes("--prove-floor")) {
    const arms = [
      ["empty table", floorRefusal([])],
      ["one short of the floor", floorRefusal(MUTATIONS.slice(0, MIN_MUTATIONS - 1))],
      ["a subject unmutated", floorRefusal(MUTATIONS.filter((x) => x.file !== "src/sessionJwt.ts").concat(
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
