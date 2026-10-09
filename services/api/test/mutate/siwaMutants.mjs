#!/usr/bin/env node
/**
 * Mutation population for T-0287: appleJwks.ts (the JWKS cache - TTL, the one refetch past its min age, no fallback
 * key, usable keys only, a failing fetch leaving the cache), appleIdentity.ts (Apple's identity-token steps - header,
 * RS256 signature, iss, aud, exp/iat bounds, sub, the session-bound nonce), accountStore.ts (the bind and the one-batch
 * deletion over every user-keyed table), account.ts (the two routes), appleClient.ts (Apple's form posts) and
 * sessionJwt.ts (the apple claim). The runner is assertMutants.mjs's (T-0280), because touches: is services/api/ and
 * check-mutate-population.py reads Sources/ and services/etl/etl/ only.
 *
 *   node services/api/test/mutate/siwaMutants.mjs                  run the population
 *   node services/api/test/mutate/siwaMutants.mjs --prove-vacuity  every mutant must report MISSED with no tests
 *   node services/api/test/mutate/siwaMutants.mjs --prove-floor    the floor refuses on its arms; runs no tests
 *   ... --only=<id>,<id>                                            run only the named entries; an unknown id refuses
 *   ... --with-pin                                                  also run identityVerifierPin.test.ts (T-0287 rv3): the
 *       content pin fails on ANY edit of the verifier, so the population runs without it and every mutant must be
 *       caught by behaviour; --with-pin shows a mutant red by the pin too
 *
 * WHAT COUNTS. CAUGHT only when vitest's JSON report names a FAILED test. A run that fails with no named failure is a
 * TRAP and does not count. An anchor that does not occur exactly once is STALE and the run refuses before mutating
 * anything. Pass condition: caught == MUTATIONS.length. THE FLOOR is literal: MIN_MUTATIONS, and every SUBJECT is
 * mutated by at least one entry. A SQL mutant keeps every ?N bound, so it is caught by its answer, never by a
 * bind-count error (T-0278 S1's lesson). The tree is checked clean before the first mutant and every file is restored.
 */
import { spawnSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const API = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const OUT = resolve(API, "..", "..", ".build", "mutate-siwa");

export const MIN_MUTATIONS = 136;
/** T-0291: the attacker's public modulus for rv4-keys-attacker-jwk (2048 bits, base64url; its private half is discarded). */
const RV4_N = "3nrQ6bwDGzN394X5_0ls0xUZAQAjeNUO5m6aIeQXS30RBAdFF5ysukMbZHLi74ARGizNxgmEpdoLtzBBYPjR4FSV_OTnFKIwhlHVqu8I3zPhC84XewPY0iW_b6nzibasfYsJoFt4yATvmf-xM91130GQuS9NIhzgAilsBEY5-q1WL5OlDGtCradrgD5Ugy7tmE87Nx0SavteiTBipN71Uvw1YkzqJ-nInrDbELBAqbwOBei81d9WBWhvmd7TvghpLvNS1Axbw0CF55gulGA9FqB-vwTe-KcjWcXTtNfFtFEWi1jRARwbZ5prl2-Kdnq_jjsaOGRhkyObP8zaalgXtw";
export const SUBJECTS = ["src/appleJwks.ts", "src/appleIdentity.ts", "src/accountStore.ts", "src/account.ts", "src/appleClient.ts", "src/sessionJwt.ts", "src/planSweep.ts"];
const TESTS = ["test/authAppleToken.test.ts", "test/authAppleFields.test.ts", "test/authAppleBind.test.ts", "test/accountDelete.test.ts", "test/accountDeletePlans.test.ts", "test/requestReadSites.test.ts", "test/routes.test.ts"];
const PIN_TEST = "test/identityVerifierPin.test.ts";
let runTests = TESTS;

const m = (id, file, find, replace) => ({ id, file: `src/${file}`, find, replace });
export const MUTATIONS = [
  m("jwks-ttl-exclusive", "appleJwks.ts", "nowMs - cache.fetchedAtMs >= APPLE_JWKS_TTL_MS", "nowMs - cache.fetchedAtMs > APPLE_JWKS_TTL_MS"),
  m("jwks-ttl-never", "appleJwks.ts", "if (cache.keys === null || nowMs - cache.fetchedAtMs >= APPLE_JWKS_TTL_MS)", "if (cache.keys === null)"),
  m("jwks-ttl-plus-1", "appleJwks.ts", "APPLE_JWKS_TTL_MS = 3_600_000;", "APPLE_JWKS_TTL_MS = 3_600_001;"),
  m("jwks-minage-exclusive", "appleJwks.ts", ">= APPLE_JWKS_REFETCH_MIN_AGE_MS", "> APPLE_JWKS_REFETCH_MIN_AGE_MS"),
  m("jwks-minage-minus-1", "appleJwks.ts", "APPLE_JWKS_REFETCH_MIN_AGE_MS = 60_000;", "APPLE_JWKS_REFETCH_MIN_AGE_MS = 59_999;"),
  m("jwks-no-refetch", "appleJwks.ts", "if (key === undefined && nowMs - cache.fetchedAtMs >= APPLE_JWKS_REFETCH_MIN_AGE_MS) {", "if (false) {"),
  m("jwks-refetch-found-kid", "appleJwks.ts", "if (key === undefined && nowMs", "if (nowMs"),
  m("jwks-fallback-key", "appleJwks.ts", "return key ?? null;", "return key ?? cache.keys!.values().next().value ?? null;"),
  m("jwks-status-unchecked", "appleJwks.ts", "if (response.status !== 200) throw", "if (false) throw"),
  m("jwks-keys-not-array", "appleJwks.ts", " || !Array.isArray((body as { keys?: unknown }).keys)", ""),
  m("jwks-kty-unchecked", "appleJwks.ts", "if (kty !== \"RSA\" || alg", "if (alg"),
  m("jwks-alg-unchecked", "appleJwks.ts", "alg !== \"RS256\" || (use", "(use"),
  m("jwks-use-unchecked", "appleJwks.ts", "(use !== undefined && use !== \"sig\")", "false"),
  m("jwks-use-required", "appleJwks.ts", "(use !== undefined && use !== \"sig\")", "(use !== \"sig\")"),
  m("jwks-modulus-1024", "appleJwks.ts", "MIN_RSA_MODULUS_BITS = 2048;", "MIN_RSA_MODULUS_BITS = 1024;"),
  m("jwks-modulus-unchecked", "appleJwks.ts", "if (modulusBits(fromB64url(n)) < MIN_RSA_MODULUS_BITS) return null;", ""),
  m("jwks-modulus-bits-short", "appleJwks.ts", "(32 - Math.clz32(n[at]!))", "(31 - Math.clz32(n[at]!))"),
  m("jwks-duplicates-kept", "appleJwks.ts", "for (const kid of twice) found.delete(kid);", ""),
  m("jwks-cache-touched-on-failure", "appleJwks.ts", "  let body: unknown;\n  try {", "  let body: unknown;\n  cache.fetchedAtMs = nowMs;\n  try {"),
  m("id-length-unchecked", "appleIdentity.ts", "if (token.length > IDENTITY_TOKEN_MAX_LENGTH) reject(\"token is too long\");", ""),
  m("id-length-8193", "appleIdentity.ts", "IDENTITY_TOKEN_MAX_LENGTH = 8192;", "IDENTITY_TOKEN_MAX_LENGTH = 8193;"),
  m("id-header-keys-unchecked", "appleIdentity.ts", "if (!Object.keys(header).every((k) => HEADER_KEYS.includes(k))) reject(\"header carries a key it may not\");", ""),
  m("id-alg-unchecked", "appleIdentity.ts", "if (header.alg !== \"RS256\") reject(\"alg is not RS256\");", ""),
  m("id-typ-unchecked", "appleIdentity.ts", "if (\"typ\" in header && header.typ !== \"JWT\") reject(\"typ is not JWT\");", ""),
  m("id-typ-required", "appleIdentity.ts", "if (\"typ\" in header && header.typ", "if (header.typ"),
  m("id-kid-empty-read", "appleIdentity.ts", " || kid.length === 0) reject", ") reject"),
  m("id-signature-unchecked", "appleIdentity.ts", "if (!valid) reject(\"signature is not Apple's\");", ""),
  m("id-signature-over-payload-only", "appleIdentity.ts", "utf8(`${parts[1]}.${parts[2]}`)", "utf8(`${parts[2]}`)"),
  m("id-iss-unchecked", "appleIdentity.ts", "if (iss !== APPLE_ISSUER) reject(\"iss is not Apple\");", ""),
  m("id-iss-prefix", "appleIdentity.ts", "iss !== APPLE_ISSUER", "!String(iss).startsWith(APPLE_ISSUER)"),
  m("id-iss-suffix", "appleIdentity.ts", "iss !== APPLE_ISSUER", "typeof iss !== \"string\" || !iss.endsWith(APPLE_ISSUER)"),
  m("id-iss-contained", "appleIdentity.ts", "iss !== APPLE_ISSUER", "typeof iss !== \"string\" || !APPLE_ISSUER.includes(iss)"),
  m("id-aud-unchecked", "appleIdentity.ts", "if (aud !== APP_BUNDLE_ID) reject(\"aud is not this app\");", ""),
  m("id-aud-stringified", "appleIdentity.ts", "aud !== APP_BUNDLE_ID", "String(aud) !== APP_BUNDLE_ID"),
  m("id-aud-prefix", "appleIdentity.ts", "aud !== APP_BUNDLE_ID", "typeof aud !== \"string\" || !aud.startsWith(APP_BUNDLE_ID)"),
  m("id-aud-contained", "appleIdentity.ts", "aud !== APP_BUNDLE_ID", "typeof aud !== \"string\" || !APP_BUNDLE_ID.includes(aud)"),
  m("id-exp-not-integer", "appleIdentity.ts", "!Number.isSafeInteger(exp) || ", ""),
  m("id-iat-not-integer", "appleIdentity.ts", " || !Number.isSafeInteger(iat)", ""),
  m("id-exp-inclusive", "appleIdentity.ts", "!(now < (exp as number))", "!(now <= (exp as number))"),
  m("id-skew-61", "appleIdentity.ts", "APPLE_CLOCK_SKEW_S = 60;", "APPLE_CLOCK_SKEW_S = 61;"),
  m("id-skew-unchecked", "appleIdentity.ts", "if (!((iat as number) <= now + APPLE_CLOCK_SKEW_S)) reject(\"issued in the future\");", ""),
  m("id-age-601", "appleIdentity.ts", "APPLE_TOKEN_MAX_AGE_S = 600;", "APPLE_TOKEN_MAX_AGE_S = 601;"),
  m("id-age-unchecked", "appleIdentity.ts", "if (!(now - (iat as number) <= APPLE_TOKEN_MAX_AGE_S)) reject(\"issued too long ago\");", ""),
  m("id-sub-unchecked", "appleIdentity.ts", "if (typeof sub !== \"string\" || !APPLE_SUB.test(sub)) reject(\"sub is not an Apple user id\");", ""),
  m("id-sub-65", "appleIdentity.ts", "APPLE_SUB = /^[A-Za-z0-9.]{1,64}$/;", "APPLE_SUB = /^[A-Za-z0-9.]{1,65}$/;"),
  m("id-sub-unanchored", "appleIdentity.ts", "APPLE_SUB = /^[A-Za-z0-9.]{1,64}$/;", "APPLE_SUB = /[A-Za-z0-9.]{1,64}/;"),
  m("id-nonce-unchecked", "appleIdentity.ts", "if (nonce !== expectedNonce) reject(\"nonce is not this session's\");", ""),
  m("id-nonce-case-folded", "appleIdentity.ts", "nonce !== expectedNonce", "String(nonce).toLowerCase() !== expectedNonce"),
  m("id-nonce-substring", "appleIdentity.ts", "nonce !== expectedNonce", "typeof nonce !== \"string\" || !nonce.includes(expectedNonce)"),
  m("id-nonce-contained", "appleIdentity.ts", "nonce !== expectedNonce", "typeof nonce !== \"string\" || !expectedNonce.includes(nonce)"),
  m("id-nonce-over-payload", "appleIdentity.ts", "utf8(sessionToken)", "utf8(sessionToken.split(\".\")[1]!)"),
  m("id-nonce-raw", "appleIdentity.ts", "return Array.from(digest, (b) => b.toString(16).padStart(2, \"0\")).join(\"\");", "return sessionToken;"),
  m("id-alg-prefix", "appleIdentity.ts", "header.alg !== \"RS256\"", "typeof header.alg !== \"string\" || !header.alg.startsWith(\"RS256\")"),
  m("id-typ-typeof-string", "appleIdentity.ts", "\"typ\" in header && header.typ", "typeof header.typ === \"string\" && header.typ"),
  m("id-typ-case-folded", "appleIdentity.ts", "header.typ !== \"JWT\"", "String(header.typ).toUpperCase() !== \"JWT\""),
  m("id-kid-case-folded", "appleIdentity.ts", "keyFor(kid as string)", "keyFor((kid as string).toUpperCase())"),
  m("id-header-extra-null", "appleIdentity.ts", "HEADER_KEYS.includes(k))", "HEADER_KEYS.includes(k) || header[k] === null)"),
  m("id-iss-case-folded", "appleIdentity.ts", "if (iss !== APPLE_ISSUER)", "if (String(iss).toLowerCase() !== APPLE_ISSUER)"),
  m("id-aud-case-folded", "appleIdentity.ts", "if (aud !== APP_BUNDLE_ID)", "if (typeof aud !== \"string\" || aud.toLowerCase() !== APP_BUNDLE_ID)"),
  m("id-nonce-stringified", "appleIdentity.ts", "if (nonce !== expectedNonce)", "if (String(nonce) !== expectedNonce)"),
  m("id-sub-array-stringified", "appleIdentity.ts", "typeof sub !== \"string\" || !APPLE_SUB.test(sub)", "(typeof sub !== \"string\" && !Array.isArray(sub)) || !APPLE_SUB.test(String(sub))"),
  m("id-exp-array-unwrapped", "appleIdentity.ts", "!Number.isSafeInteger(exp) ||", "!Number.isSafeInteger(Array.isArray(exp) ? exp[0] : exp) ||"),
  m("id-iat-array-unwrapped", "appleIdentity.ts", "|| !Number.isSafeInteger(iat)", "|| !Number.isSafeInteger(Array.isArray(iat) ? iat[0] : iat)"),
  m("id-claims-null-refused", "appleIdentity.ts", "const { iss, aud, exp, iat, sub, nonce } = claims;", "const { iss, aud, exp, iat, sub, nonce } = claims;\n  if (Object.values(claims).some((v) => v === null)) reject(\"a claim is null\");"),
  m("rv2-kid-trimmed", "appleIdentity.ts", "keyFor(kid as string)", "keyFor((kid as string).trim())"),
  m("rv2-iss-trimmed", "appleIdentity.ts", "iss !== APPLE_ISSUER", "typeof iss !== \"string\" || iss.trim() !== APPLE_ISSUER"),
  m("rv2-nonce-trimmed", "appleIdentity.ts", "nonce !== expectedNonce", "typeof nonce !== \"string\" || nonce.trim() !== expectedNonce"),
  m("rv2-typ-trimmed", "appleIdentity.ts", "\"typ\" in header && header.typ !== \"JWT\"", "\"typ\" in header && (typeof header.typ !== \"string\" || header.typ.trim() !== \"JWT\")"),
  m("id-iss-nfkc", "appleIdentity.ts", "iss !== APPLE_ISSUER", "typeof iss !== \"string\" || iss.normalize(\"NFKC\") !== APPLE_ISSUER"),
  m("id-iss-lowercased", "appleIdentity.ts", "iss !== APPLE_ISSUER", "typeof iss !== \"string\" || iss.toLowerCase() !== APPLE_ISSUER"),
  m("id-aud-zero-width-stripped", "appleIdentity.ts", "aud !== APP_BUNDLE_ID", "typeof aud !== \"string\" || aud.replace(/[\\u200b-\\u200d\\u2060]/g, \"\") !== APP_BUNDLE_ID"),
  m("id-nonce-nul-truncated", "appleIdentity.ts", "nonce !== expectedNonce", "typeof nonce !== \"string\" || nonce.split(\"\\0\")[0] !== expectedNonce"),
  m("rv3-aud-regex-dot", "appleIdentity.ts", "if (aud !== APP_BUNDLE_ID)", "if (typeof aud !== \"string\" || !new RegExp(\"^\" + APP_BUNDLE_ID + \"$\").test(aud))"),
  m("rv3-iss-regex-dot", "appleIdentity.ts", "if (iss !== APPLE_ISSUER)", "if (typeof iss !== \"string\" || !new RegExp(\"^\" + APPLE_ISSUER + \"$\").test(iss))"),
  m("store-bind-replaces-token", "accountStore.ts", "refresh_token = COALESCE(excluded.refresh_token,\n  CASE WHEN apple_accounts.apple_sub = excluded.apple_sub THEN apple_accounts.refresh_token END),", "refresh_token = excluded.refresh_token,"),
  m("store-bind-keeps-any-token", "accountStore.ts", "CASE WHEN apple_accounts.apple_sub = excluded.apple_sub THEN apple_accounts.refresh_token END", "apple_accounts.refresh_token"),
  m("store-bind-keeps-sub", "accountStore.ts", "apple_sub = excluded.apple_sub, bound_at", "apple_sub = apple_accounts.apple_sub, bound_at"),
  m("store-subs-claim-ignored", "accountStore.ts", "UNION SELECT ?2 WHERE ?2 IS NOT NULL", "UNION SELECT ?2 WHERE ?2 IS NULL"),
  m("store-subs-binding-ignored", "accountStore.ts", "SELECT apple_sub FROM apple_accounts WHERE device_id = ?1 UNION", "SELECT apple_sub FROM apple_accounts WHERE device_id = ?1 AND 0 UNION"),
  m("store-devices-of-subs-ignored", "accountStore.ts", "UNION SELECT device_id FROM apple_accounts WHERE apple_sub IN", "UNION SELECT device_id FROM apple_accounts WHERE 0 AND apple_sub IN"),
  m("store-bindings-device-only", "accountStore.ts", "WHERE apple_sub IN (${USER_SUBS}) ORDER BY", "WHERE device_id = ?1 AND (?2 IS NULL OR 1) ORDER BY"),
  m("store-bindings-order", "accountStore.ts", "ORDER BY device_id", "ORDER BY device_id DESC"),
  m("store-sign-counts-kept", "accountStore.ts", "DELETE FROM attest_sign_counts WHERE key_id IN", "DELETE FROM attest_sign_counts WHERE 0 AND key_id IN"),
  m("store-keys-kept", "accountStore.ts", "DELETE FROM attested_keys WHERE device_id IN", "DELETE FROM attested_keys WHERE 0 AND device_id IN"),
  m("store-challenge-counts-kept", "accountStore.ts", "DELETE FROM attest_challenge_counts WHERE bucket IN", "DELETE FROM attest_challenge_counts WHERE 0 AND bucket IN"),
  m("store-challenge-counts-prefix", "accountStore.ts", "'device:' || device", "'device' || device"),
  m("store-entitlements-kept", "accountStore.ts", "\"DELETE FROM entitlements WHERE app_account_token = ?1\"", "\"DELETE FROM entitlements WHERE app_account_token = ?1 AND 0\""),
  m("store-entitlements-tokenless-too", "accountStore.ts", "\"DELETE FROM entitlements WHERE app_account_token = ?1\"", "\"DELETE FROM entitlements WHERE app_account_token = ?1 OR app_account_token IS NULL\""),
  m("store-bindings-kept", "accountStore.ts", "DELETE FROM apple_accounts WHERE apple_sub IN", "DELETE FROM apple_accounts WHERE 0 AND apple_sub IN"),
  m("store-bindings-deleted-first", "accountStore.ts", "    db.prepare(DELETE_SIGN_COUNTS).bind(user.deviceId, user.appleSub),", "    db.prepare(DELETE_BINDINGS).bind(user.deviceId, user.appleSub),\n    db.prepare(DELETE_SIGN_COUNTS).bind(user.deviceId, user.appleSub),"),
  m("acct-apple-unauthenticated", "account.ts", "const session = await caller(req, deps.secret, nowMs);\n  if (session === null) return UNAUTHORIZED();", "const session = (await caller(req, deps.secret, nowMs))!;"),
  m("acct-delete-unauthenticated", "account.ts", "const session = await caller(req, deps.secret, deps.now().getTime());\n  if (session === null) return UNAUTHORIZED();", "const session = (await caller(req, deps.secret, deps.now().getTime()))!;"),
  m("acct-apple-without-secret", "account.ts", "if (deps.secret === null) return UNAVAILABLE();\n  const nowMs", "const nowMs"),
  m("acct-body-keys-unchecked", "account.ts", "if (Object.keys(body).sort().join() !== BODY_KEYS.join()) return INVALID();", ""),
  m("acct-code-unchecked", "account.ts", "typeof authorizationCode !== \"string\" || !AUTHORIZATION_CODE.test(authorizationCode)", "typeof authorizationCode !== \"string\""),
  m("acct-code-513", "account.ts", "AUTHORIZATION_CODE = /^[A-Za-z0-9._-]{1,512}$/;", "AUTHORIZATION_CODE = /^[A-Za-z0-9._-]{1,513}$/;"),
  m("acct-code-empty", "account.ts", "AUTHORIZATION_CODE = /^[A-Za-z0-9._-]{1,512}$/;", "AUTHORIZATION_CODE = /^[A-Za-z0-9._-]{0,512}$/;"),
  m("acct-nonce-of-sub", "account.ts", "await sessionNonce(session.token)", "await sessionNonce(session.claims.sub)"),
  m("acct-apple-down-as-invalid", "account.ts", "if (e instanceof AppleUnavailable) return APPLE_DOWN();", "if (e instanceof AppleUnavailable) return INVALID();"),
  m("acct-exchange-without-secret", "account.ts", "if (deps.clientSecret === null) return null;", ""),
  m("acct-exchange-status-unchecked", "account.ts", "if (response.status !== 200) return null;", ""),
  m("acct-exchange-empty-token", "account.ts", "token.length > 0 ? token : null", "token.length >= 0 ? token : null"),
  m("acct-token-not-stored", "account.ts", "await bindApple(deps.db, session.claims.sub, appleSub, refreshToken, nowMs);", "await bindApple(deps.db, session.claims.sub, appleSub, null, nowMs);"),
  m("acct-act-dropped", "account.ts", "act === undefined ? { sub, apple: appleSub } : { sub, act, apple: appleSub }", "{ sub, apple: appleSub }"),
  m("acct-apple-dropped", "account.ts", "act === undefined ? { sub, apple: appleSub } : { sub, act, apple: appleSub }", "act === undefined ? { sub } : { sub, act }"),
  m("acct-pending-always", "account.ts", "let pending = false;", "let pending = bindings.length > 0;"),
  m("acct-pending-ignores-null-token", "account.ts", "if (secret === null || binding.refreshToken === null || ", "if (secret === null || "),
  m("acct-pending-ignores-secret", "account.ts", "if (secret === null || binding", "if (binding"),
  m("acct-revoke-any-non-5xx", "account.ts", ".status === 200;", ".status < 500;"),
  m("acct-revoke-throw-aborts", "account.ts", ".status === 200;\n  } catch {\n    return false;", ".status === 200;\n  } catch (e) {\n    throw e;"),
  m("acct-delete-skipped", "account.ts", "await deleteUser(deps.db, user);", ""),
  m("acct-delete-act-ignored", "account.ts", "accountToken: session.claims.act ?? null", "accountToken: null"),
  m("acct-delete-apple-ignored", "account.ts", "appleSub: session.claims.apple ?? null", "appleSub: null"),
  m("acct-delete-method", "account.ts", "if (req.method !== \"DELETE\")", "if (req.method === \"GET\")"),
  m("client-hint-access", "appleClient.ts", "token_type_hint: \"refresh_token\"", "token_type_hint: \"access_token\""),
  m("client-grant-refresh", "appleClient.ts", "grant_type: \"authorization_code\"", "grant_type: \"refresh_token\""),
  m("client-revoke-no-secret", "appleClient.ts", "client_secret: secret, token,", "client_secret: \"\", token,"),
  m("client-revoke-url", "appleClient.ts", "\"https://appleid.apple.com/auth/revoke\"", "\"https://appleid.apple.com/auth/revoke/\""),
  m("rv4-keys-attacker-jwk", "appleClient.ts", "keys: () => fetchImpl(APPLE_JWKS_URL),", "keys: async () => {\n"
    + "      const r = await fetchImpl(APPLE_JWKS_URL);\n      if (r.status !== 200) return r;\n"
    + "      const b = (await r.json()) as { keys: unknown[] };\n"
    + `      b.keys.push({ kty: "RSA", alg: "RS256", use: "sig", kid: "rv4", n: "${RV4_N}", e: "AQAB" });\n`
    + "      return new Response(JSON.stringify(b), { status: 200, headers: r.headers });\n    },"),
  m("client-secret-never", "appleClient.ts", "CLIENT_SECRET = /^[A-Za-z0-9_-]+\\.[A-Za-z0-9_-]+\\.[A-Za-z0-9_-]+$/;", "CLIENT_SECRET = /^$/;"),
  m("sess-apple-unchecked", "sessionJwt.ts", "if (\"apple\" in claims && (typeof apple !== \"string\" || !APPLE_SUB.test(apple))) return null;", ""),
  m("sess-apple-not-signed", "sessionJwt.ts", ",\n    ...(claims.apple ? { apple: claims.apple } : {}) };", " };"),
  m("sess-apple-not-returned", "sessionJwt.ts", ", ...(typeof apple === \"string\" ? { apple } : {}) };", " };"),
  m("sess-apple-key-refused", "sessionJwt.ts", "filter((k) => k !== \"act\" && k !== \"apple\")", "filter((k) => k !== \"act\")"),
  // T-0326: DELETE /account sweeps PLANS (planSweep.ts) for every one of the user's devices (account.ts).
  m("sweep-stops-on-empty-page", "planSweep.ts", "if (page.list_complete) break;", "if (page.list_complete || page.keys.length === 0) break;"),
  m("sweep-ignores-cursor", "planSweep.ts", "kv.list(cursor === undefined ? { prefix } : { prefix, cursor })", "kv.list({ prefix })"),
  m("sweep-key-shape-prefix-only", "planSweep.ts", "name.startsWith(prefix) && PLAN_TOKEN.test(name.slice(prefix.length))", "name.startsWith(prefix)"),
  m("sweep-delete-failure-ignored", "planSweep.ts", "if (settled.some((s) => s.status === \"rejected\")) whole = false;", ""),
  m("sweep-list-failure-aborts", "planSweep.ts", "        whole = false;\n        break;\n      }\n      const mine", "        return false;\n      }\n      const mine"),
  m("sweep-no-cursor-complete", "planSweep.ts", "if (typeof page.cursor !== \"string\" || page.cursor === \"\") {\n        whole = false;", "if (typeof page.cursor !== \"string\" || page.cursor === \"\") {"),
  m("sweep-deletes-unbounded", "planSweep.ts", "mine.slice(0, PLAN_SWEEP_MAX_OPS - ops)", "mine"),
  m("sweep-list-bound-off-by-one", "planSweep.ts", "if (ops >= PLAN_SWEEP_MAX_OPS) return false;", "if (ops > PLAN_SWEEP_MAX_OPS) return false;"),
  m("sweep-bound-raised", "planSweep.ts", "PLAN_SWEEP_MAX_OPS = 900;", "PLAN_SWEEP_MAX_OPS = 1000;"),
  m("acct-sweep-session-device-only", "account.ts", "[user.deviceId, ...bindings.map((b) => b.deviceId)]", "[user.deviceId]"),
  m("acct-sweep-pending-dropped", "account.ts", "plans_pending: !swept", "plans_pending: false"),
  m("acct-sweep-unwired", "account.ts", "plans: env.PLANS ?? null", "plans: null"),
];

export const EQUIVALENT = [];

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
  const run = spawnSync(process.execPath, [bin, "run", ...runTests, "--reporter=json", `--outputFile=${report}`, ...extra],
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
      ["a subject unmutated", floorRefusal(MUTATIONS.filter((x) => x.file !== "src/account.ts").concat(
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
  if (argv.includes("--with-pin")) runTests = [...TESTS, PIN_TEST];
  const only = argv.find((a) => a.startsWith("--only="))?.slice("--only=".length).split(",") ?? null;
  const unknown = (only ?? []).filter((id) => !MUTATIONS.some((x) => x.id === id));
  if (only !== null && (only.length === 0 || unknown.length > 0)) { console.log(`REFUSING: unknown --only id(s) ${unknown.join(",")}`); return 2; }
  const run = only === null ? MUTATIONS : MUTATIONS.filter((x) => only.includes(x.id));
  const extra = prove ? ["-t", "^no test is named this$", "--passWithNoTests"] : [];
  console.log(`population mutations=${MUTATIONS.length} (floor ${MIN_MUTATIONS}) equivalent=${EQUIVALENT.length} `
    + `subjects=${SUBJECTS.length} tests=${runTests.length}${prove ? " PROVE-VACUITY" : ""}${only ? ` ONLY=${run.length}` : ""}`);
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
    console.log(`${v.padEnd(6)} ${x.id}${result.named.length ? ` by ${result.named.length}: "${result.named.join("\" | \"")}"` : ""}`);
  }
  console.log(`RESULT caught=${tally.CAUGHT} missed=${tally.MISSED} trap=${tally.TRAP} of ${run.length}`);
  if (prove) return tally.MISSED === run.length ? 0 : 1;
  return tally.CAUGHT === run.length ? 0 : 1;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) process.exit(main(process.argv.slice(2)));
