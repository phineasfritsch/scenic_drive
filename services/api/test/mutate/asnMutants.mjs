#!/usr/bin/env node
/**
 * Mutation population for POST /asn and GET /entitlement (T-0267 R10): the DER reader, the X.509 parse and chain
 * signatures, the JWS verifier and its pinned root, the notification-type mapping, the signedDate-guarded upsert
 * and the entitlement read. The quotaMutants.mjs driver shape (T-0256 R10), copied: touches: is services/api/ and
 * check-mutate-population.py reads Sources/ and services/etl/etl/ only.
 *
 *   node services/api/test/mutate/asnMutants.mjs                  run the population
 *   node services/api/test/mutate/asnMutants.mjs --prove-vacuity  every mutant must report MISSED with no tests
 *   node services/api/test/mutate/asnMutants.mjs --prove-floor    the floor refuses on its arms; runs no tests
 *   ... --only=<id>,<id>                                           run only the named entries; an unknown id refuses
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
const OUT = resolve(API, "..", "..", ".build", "mutate-asn");

export const MIN_MUTATIONS = 69;
export const SUBJECTS = ["src/der.ts", "src/x509.ts", "src/appleJws.ts", "src/asnNotification.ts", "src/entitlementStore.ts",
  "src/asn.ts"];
const TESTS = ["test/asnVerify.test.ts", "test/asnState.test.ts", "test/asnRootPin.test.ts"];

const m = (id, file, find, replace) => ({ id, file: `src/${file}`, find, replace });
const VALID = "!(cert.notBefore <= now && now <= cert.notAfter)";
export const MUTATIONS = [
  m("der-long-length", "der.ts", "if (length & 0x80) {", "if (false) {"),
  m("der-trailing-accepted", "der.ts", "if (next !== bytes.length) throw new DerError(\"trailing bytes\");", ""),
  m("der-utc-century", "der.ts", "year += year < 50 ? 2000 : 1900;", "year += 1900;"),
  m("der-utc-century-boundary", "der.ts", "year += year < 50 ? 2000 : 1900;", "year += year < 26 ? 2000 : 1900;"),
  m("der-generalized-refused", "der.ts", "tlv.tag === 0x18 ?", "false ?"),
  m("x509-sha384-as-256", "x509.ts", "[OID_ECDSA_SHA384]: \"SHA-384\"", "[OID_ECDSA_SHA384]: \"SHA-256\""),
  m("x509-issuer-unchecked", "x509.ts", " || !sameBytes(child.issuer, parent.subject)", ""),
  m("x509-sha256-as-384", "x509.ts", "[OID_ECDSA_SHA256]: \"SHA-256\"", "[OID_ECDSA_SHA256]: \"SHA-384\""),
  m("x509-same-bytes-length-only", "x509.ts", "for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;", ""),
  m("x509-p384-size", "x509.ts", "{ name: \"P-384\", size: 48 }", "{ name: \"P-384\", size: 32 }"),
  m("x509-extension-oid-lost", "x509.ts", "extensions.push(oidText(expectTag(children(expectTag(ext, 0x30))[0], 0x06).value));",
    "extensions.push(\"0\");"),
  m("x509-tbs-content-only", "x509.ts", "tbs: tbs.raw,", "tbs: tbs.value,"),
  m("jws-root-unchecked", "appleJws.ts", "if ((await sha256Hex(root.der)) !== trust.rootSha256)", "if (false)"),
  m("jws-root-pin-literal", "appleJws.ts", "APPLE_ROOT_CA_G3_SHA256 = \"63343abf", "APPLE_ROOT_CA_G3_SHA256 = \"73343abf"),
  m("jws-not-before-exclusive", "appleJws.ts", "cert.notBefore <= now", "cert.notBefore < now"),
  m("jws-not-after-exclusive", "appleJws.ts", "now <= cert.notAfter", "now < cert.notAfter"),
  m("jws-not-before-ignored", "appleJws.ts", VALID, "!(now <= cert.notAfter)"),
  m("jws-not-after-ignored", "appleJws.ts", VALID, "!(cert.notBefore <= now)"),
  m("jws-validity-leaf-only", "appleJws.ts", "for (const cert of certs) if", "for (const cert of [leaf]) if"),
  m("jws-validity-no-root", "appleJws.ts", "for (const cert of certs) if", "for (const cert of [leaf, intermediate]) if"),
  m("jws-wwdr-oid-unchecked", "appleJws.ts", "if (!intermediate.extensions.includes(OID_APPLE_WWDR_INTERMEDIATE))", "if (false)"),
  m("jws-leaf-oid-unchecked", "appleJws.ts", "if (!leaf.extensions.includes(OID_APPLE_STORE_LEAF))", "if (false)"),
  m("jws-intermediate-sig-unchecked", "appleJws.ts", "if (!(await signedBy(intermediate, root)))", "if (false)"),
  m("jws-leaf-sig-unchecked", "appleJws.ts", "if (!(await signedBy(leaf, intermediate)))", "if (false)"),
  m("jws-x5c-two-ok", "appleJws.ts", "x5c.length !== 3", "x5c.length < 2"),
  m("jws-x5c-four-ok", "appleJws.ts", "x5c.length !== 3", "x5c.length < 3"),
  m("jws-alg-only-none-refused", "appleJws.ts", "if (header.alg !== \"ES256\")", "if (header.alg === \"none\")"),
  m("jws-alg-any-es", "appleJws.ts", "if (header.alg !== \"ES256\")", "if (!String(header.alg).startsWith(\"ES\"))"),
  m("jws-sig-length-unchecked", "appleJws.ts", "if (signature.length !== 64) reject", "if (false) reject"),
  m("jws-bad-signature-accepted", "appleJws.ts", "if (!ok) reject(\"bad signature\");", ""),
  m("jws-signing-input-body-only", "appleJws.ts", "encode(`${head}.${body}`)", "encode(`${body}`)"),
  m("asn-bundle-literal", "asnNotification.ts", "APP_BUNDLE_ID = \"com.phineasfritsch.scenicdrive\"", "APP_BUNDLE_ID = \"com.phineasfritsch.scenic\""),
  m("asn-subscribed-dropped", "asnNotification.ts", "[\"SUBSCRIBED\", \"DID_RENEW\", \"OFFER_REDEEMED\"]", "[\"DID_RENEW\", \"OFFER_REDEEMED\"]"),
  m("asn-did-renew-dropped", "asnNotification.ts", "[\"SUBSCRIBED\", \"DID_RENEW\", \"OFFER_REDEEMED\"]", "[\"SUBSCRIBED\", \"OFFER_REDEEMED\"]"),
  m("asn-offer-redeemed-dropped", "asnNotification.ts", "[\"SUBSCRIBED\", \"DID_RENEW\", \"OFFER_REDEEMED\"]", "[\"SUBSCRIBED\", \"DID_RENEW\"]"),
  m("asn-expired-dropped", "asnNotification.ts", "[\"EXPIRED\", \"REFUND\", \"REVOKE\", \"GRACE_PERIOD_EXPIRED\"]", "[\"REFUND\", \"REVOKE\", \"GRACE_PERIOD_EXPIRED\"]"),
  m("asn-refund-dropped", "asnNotification.ts", "[\"EXPIRED\", \"REFUND\", \"REVOKE\", \"GRACE_PERIOD_EXPIRED\"]", "[\"EXPIRED\", \"REVOKE\", \"GRACE_PERIOD_EXPIRED\"]"),
  m("asn-revoke-dropped", "asnNotification.ts", "[\"EXPIRED\", \"REFUND\", \"REVOKE\", \"GRACE_PERIOD_EXPIRED\"]", "[\"EXPIRED\", \"REFUND\", \"GRACE_PERIOD_EXPIRED\"]"),
  m("asn-grace-expired-dropped", "asnNotification.ts", "[\"EXPIRED\", \"REFUND\", \"REVOKE\", \"GRACE_PERIOD_EXPIRED\"]", "[\"EXPIRED\", \"REFUND\", \"REVOKE\"]"),
  m("asn-grace-any-subtype", "asnNotification.ts", "type === \"DID_FAIL_TO_RENEW\" && subtype === \"GRACE_PERIOD\"", "type === \"DID_FAIL_TO_RENEW\""),
  m("asn-subtype-dropped", "asnNotification.ts", "const subtype = typeof payload.subtype === \"string\" ? payload.subtype : null;", "const subtype = null;"),
  m("asn-sandbox-always", "asnNotification.ts", "if (environment === \"Sandbox\" && !policy.allowSandbox) return null;", ""),
  m("asn-sandbox-never", "asnNotification.ts", "if (environment === \"Sandbox\" && !policy.allowSandbox) return null;", "if (environment === \"Sandbox\") return null;"),
  m("asn-bundle-unchecked", "asnNotification.ts", "if (bundleId !== policy.bundleId) return null;", ""),
  m("asn-environment-unchecked", "asnNotification.ts", "if (environment !== \"Production\" && environment !== \"Sandbox\") bad(\"unknown environment\");", ""),
  m("asn-expires-ignored", "asnNotification.ts", "activeUntil = epochMs(expiresDate, \"expiresDate\");", "activeUntil = null;"),
  m("asn-grace-uses-expires", "asnNotification.ts", "activeUntil = epochMs(renewal.gracePeriodExpiresDate, \"gracePeriodExpiresDate\");",
    "activeUntil = epochMs(expiresDate, \"expiresDate\");"),
  m("asn-inactive-keeps-until", "asnNotification.ts", "} else if (status === \"active\" && expiresDate !== undefined) {", "} else if (expiresDate !== undefined) {"),
  m("asn-renewal-unverified", "asnNotification.ts", "const renewal = await verifyAppleJws(signedRenewalInfo, policy);",
    "if (typeof signedRenewalInfo !== \"string\") bad(\"no renewal\"); const renewal = JSON.parse(atob(signedRenewalInfo.split(\".\")[1]!.replace(/-/g, \"+\").replace(/_/g, \"/\"))) as Record<string, unknown>;"),
  m("asn-token-case-kept", "asnNotification.ts", "appAccountToken.toLowerCase()", "appAccountToken"),
  m("asn-negative-epoch-ok", "asnNotification.ts", " || value < 0)", ")"),
  m("asn-empty-otid-ok", "asnNotification.ts", " || originalTransactionId.length === 0", ""),
  m("store-replay-lands", "entitlementStore.ts", "WHERE excluded.signed_date > entitlements.signed_date", "WHERE excluded.signed_date >= entitlements.signed_date"),
  m("store-unguarded", "entitlementStore.ts", " WHERE excluded.signed_date > entitlements.signed_date", ""),
  m("store-status-kept", "entitlementStore.ts", "status = excluded.status,", ""),
  m("store-until-kept", "entitlementStore.ts", "active_until = excluded.active_until,", ""),
  m("read-null-token-matches", "entitlementStore.ts", "WHERE app_account_token = ?1\"", "WHERE app_account_token = ?1 OR app_account_token IS NULL\""),
  m("read-until-inclusive", "entitlementStore.ts", "nowMs < r.active_until", "nowMs <= r.active_until"),
  m("read-earliest-end", "entitlementStore.ts", "Math.max(", "Math.min("),
  m("read-open-ignored", "entitlementStore.ts", "const open = live.some((r) => r.active_until === null);", "const open = false;"),
  m("read-none-is-inactive", "entitlementStore.ts", "return { status: \"none\", active_until: null };", "return { status: \"inactive\", active_until: null };"),
  m("asn-sandbox-truthy", "asn.ts", "allowSandbox: env.ASN_ALLOW_SANDBOX === \"1\",", "allowSandbox: !!env.ASN_ALLOW_SANDBOX,"),
  m("asn-root-pin-from-env", "asn.ts", "rootSha256: APPLE_ROOT_CA_G3_SHA256,",
    "rootSha256: (env as unknown as Record<string, string | undefined>).ASN_ROOT_SHA256 ?? APPLE_ROOT_CA_G3_SHA256,"),
  m("asn-clock-frozen", "asn.ts", "now: () => new Date(),", "now: () => new Date(0),"),
  m("asn-d1-error-acknowledged", "asn.ts", "} catch {\n    return json({ error: \"entitlement_unavailable\" }, 503);\n  }\n  return json({ received: true });",
    "} catch {\n    return json({ received: true });\n  }\n  return json({ received: true });"),
  m("asn-rejected-acknowledged", "asn.ts", "if (e instanceof JwsRejected) return INVALID();", "if (e instanceof JwsRejected) return json({ received: true });"),
  m("entitlement-token-case", "asn.ts", "(req.headers.get(ACCOUNT_TOKEN_HEADER) ?? \"\").toLowerCase();", "(req.headers.get(ACCOUNT_TOKEN_HEADER) ?? \"\");"),
  m("entitlement-uuid-unanchored", "asn.ts", "[0-9a-f]{12}$/;", "[0-9a-f]{12}/;"),
  m("entitlement-header-name", "asn.ts", "ACCOUNT_TOKEN_HEADER = \"x-scenic-account-token\"", "ACCOUNT_TOKEN_HEADER = \"x-scenic-device\""),
];

export const EQUIVALENT = [
  { id: "der-run-past-accepted", file: "src/der.ts", find: "if (end > bytes.length) throw new DerError(\"element runs past its parent\");",
    witness: "without the check a truncated element is clamped by subarray instead of refused, but every byte a certificate "
      + "carries is covered by a check that the clamp breaks: a cut in the leaf or intermediate shortens the TBS or the "
      + "signature value, so ECDSA verification by the parent's key fails; a cut in the root changes its SHA-256, so the pin "
      + "fails - both 400 with nothing written. Seen in the full run at d711ea6: MISSED, and the row 'leaf certificate cut "
      + "by one byte' answers 400 either way. The check stays so the reader refuses malformed DER at the first byte." },
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
      ["a subject unmutated", floorRefusal(MUTATIONS.filter((x) => x.file !== "src/asn.ts").concat(
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
