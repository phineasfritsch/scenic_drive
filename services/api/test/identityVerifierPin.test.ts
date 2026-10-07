/**
 * T-0287 rv3 B1 (P-PRIV-04): the identity-token verifier is closed STRUCTURALLY. Three review rounds each found one more
 * spelling of a looser-than-equality compare (trim, NFKC, an unescaped anchored RegExp) that a finite variant table did
 * not refuse. A whole-file SHA-256 content pin over every src module whose bytes decide whether an identity token is
 * accepted turns ANY edit there - however it is spelled - into a failure by name; an approved change edits the hash
 * table below in the same diff, where a reviewer sees it. The pinned files: appleIdentity.ts (Apple's steps),
 * appleJwks.ts (the kid-selected key), asnNotification.ts (APP_BUNDLE_ID, the aud) and account.ts (the route that hands
 * the verifier its nonce and its key lookup). Belt and braces for the reviewer: a whole-line WHITELIST of every line in
 * those files that names a token field, the issuer, the bundle id, the nonce or the key lookup, compared WHOLE (trimmed)
 * per file. FAIL-CLOSED: only lines that begin with two slashes are skipped; JSDoc lines are sites like code.
 */
import { describe, expect, it } from "vitest";

const SRC = import.meta.glob(["../src/account.ts", "../src/appleIdentity.ts", "../src/appleJwks.ts", "../src/asnNotification.ts"],
  { query: "?raw", import: "default", eager: true }) as Record<string, string>;
const text = (path: string) => SRC[path]!.replace(/\r\n/g, "\n");
const SITE = /\b(iss|aud|nonce|kid|alg|typ|sub|exp|iat|APPLE_ISSUER|APP_BUNDLE_ID|expectedNonce|sessionNonce|verifyIdentityToken|appleKey|keyFor)\b/;
const LINE_COMMENT = /^\/\//;
const LOCAL_IMPORT = /from "\.\/([A-Za-z0-9_]+)"/g;

async function sha256Hex(s: string): Promise<string> {
  const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s)));
  return Array.from(digest, (b) => b.toString(16).padStart(2, "0")).join("");
}

/** The approved bytes, LF-normalised. Changing a pinned file means changing its hash here, in the same diff. */
const APPROVED_SHA256: Record<string, string> = {
  "../src/account.ts": "3c0cadcb09780d85f00aca1dc11c87e53c2aabec7ec060bee3b203612a4a790e",
  "../src/appleIdentity.ts": "8d1a0bbe9ed785b48ffb60f79c14846e6cc37230077b1a3c976959a04f97aff6",
  "../src/appleJwks.ts": "05c3dcfdafe01558d6d6cffe2c35e890cb6416dc5e91ba2142d164572d58592f",
  "../src/asnNotification.ts": "84789852c589b83d863ace68087e39bf2fca65d14085e3defa0e70e00c093334",
};

/** Every line of the pinned files that names a token field, the issuer, the bundle id, the nonce or the key lookup. */
const APPROVED_SITES: Record<string, string[]> = {
  "../src/account.ts": [
    "* appleJwks.ts, the nonce the hash of the Bearer itself), exchanges the code for a refresh token only with the owner's",
    "* APPLE_CLIENT_SECRET, binds the Apple sub to the session's device and answers the session JWT re-signed with apple",
    "import { IdentityRejected, sessionNonce, verifyIdentityToken } from \"./appleIdentity\";",
    "import { AppleUnavailable, appleKey, emptyJwksCache, type JwksCache } from \"./appleJwks\";",
    "appleSub = await verifyIdentityToken(identityToken, await sessionNonce(session.token),",
    "(kid) => appleKey(kid, deps.jwks, () => deps.apple.keys(), nowMs), nowMs);",
    "await bindApple(deps.db, session.claims.sub, appleSub, refreshToken, nowMs);",
    "const { sub, act } = session.claims;",
    "const signed = await signSession(deps.secret, act === undefined ? { sub, apple: appleSub } : { sub, act, apple: appleSub }, nowMs);",
    "const user: AccountUser = { deviceId: session.claims.sub, appleSub: session.claims.apple ?? null, accountToken: session.claims.act ?? null };",
  ],
  "../src/appleIdentity.ts": [
    "* header is {alg, kid} plus at most typ \"JWT\", signed by the Apple key published under kid; iss APPLE_ISSUER; aud the",
    "* app's bundle id; now < exp; iat within APPLE_CLOCK_SKEW_S ahead and APPLE_TOKEN_MAX_AGE_S behind; sub an Apple user",
    "* id; nonce the lowercase-hex SHA256 of the caller's session JWT. Every defect throws IdentityRejected. Only sub is",
    "import { APP_BUNDLE_ID } from \"./asnNotification\";",
    "export const APPLE_ISSUER = \"https://appleid.apple.com\";",
    "const HEADER_KEYS = [\"alg\", \"kid\", \"typ\"];",
    "/** The nonce the app hashes into its request: lowercase hex SHA256 of the session JWT it holds (R3). */",
    "export async function sessionNonce(sessionToken: string): Promise<string> {",
    "/** The Apple sub of a valid token; `keyFor` answers the Apple key published under a kid, or null. */",
    "export async function verifyIdentityToken(token: string, expectedNonce: string,",
    "keyFor: (kid: string) => Promise<CryptoKey | null>, nowMs: number): Promise<string> {",
    "if (header.alg !== \"RS256\") reject(\"alg is not RS256\");",
    "if (\"typ\" in header && header.typ !== \"JWT\") reject(\"typ is not JWT\");",
    "const kid = header.kid;",
    "if (typeof kid !== \"string\" || kid.length === 0) reject(\"kid is not a string\");",
    "const key = (await keyFor(kid as string)) ?? reject(\"no Apple key has this kid\");",
    "const { iss, aud, exp, iat, sub, nonce } = claims;",
    "if (iss !== APPLE_ISSUER) reject(\"iss is not Apple\");",
    "if (aud !== APP_BUNDLE_ID) reject(\"aud is not this app\");",
    "if (!Number.isSafeInteger(exp) || !Number.isSafeInteger(iat)) reject(\"exp or iat is not an integer\");",
    "if (!(now < (exp as number))) reject(\"expired\");",
    "if (!((iat as number) <= now + APPLE_CLOCK_SKEW_S)) reject(\"issued in the future\");",
    "if (!(now - (iat as number) <= APPLE_TOKEN_MAX_AGE_S)) reject(\"issued too long ago\");",
    "if (typeof sub !== \"string\" || !APPLE_SUB.test(sub)) reject(\"sub is not an Apple user id\");",
    "if (nonce !== expectedNonce) reject(\"nonce is not this session's\");",
    "return sub as string;",
  ],
  "../src/appleJwks.ts": [
    "* selected by kid EQUALITY; a kid absent from a live cache buys ONE refetch, and only when the cached set is at least",
    "* MIN_RSA_MODULUS_BITS are usable; a kid listed twice is dropped (fail closed).",
    "const { kty, alg, use, kid, n, e } = entry as Record<string, unknown>;",
    "if (kty !== \"RSA\" || alg !== \"RS256\" || (use !== undefined && use !== \"sig\")) return null;",
    "if (typeof kid !== \"string\" || kid.length === 0) return null;",
    "const key = await crypto.subtle.importKey(\"jwk\", { kty: \"RSA\", n, e, alg: \"RS256\", ext: true },",
    "return [kid, key];",
    "for (const kid of twice) found.delete(kid);",
    "/** The key Apple publishes under `kid`, or null. Throws AppleUnavailable when a needed fetch fails. */",
    "export async function appleKey(kid: string, cache: JwksCache, fetchKeys: () => Promise<Response>, nowMs: number): Promise<CryptoKey | null> {",
    "let key = cache.keys!.get(kid);",
    "key = cache.keys!.get(kid);",
  ],
  "../src/asnNotification.ts": [
    "export const APP_BUNDLE_ID = \"com.phineasfritsch.scenicdrive\";",
  ],
};

describe("the identity-token verifier is pinned (T-0287 rv3 B1, P-PRIV-04)", () => {
  it("the identity-token verifier is exactly the approved bytes", async () => {
    const got: Record<string, string> = {};
    for (const path of Object.keys(SRC).sort()) got[path] = await sha256Hex(text(path));
    expect(got).toEqual(APPROVED_SHA256);
  });

  it("every line naming a token field, the issuer, the bundle id, the nonce or the key lookup is an approved site, file by file", () => {
    const got = Object.fromEntries(Object.keys(SRC).sort().map((path) => [path,
      text(path).split("\n").map((l) => l.trim()).filter((l) => !LINE_COMMENT.test(l) && SITE.test(l))]));
    expect(got).toEqual(APPROVED_SITES);
  });

  it("every src module the verifier and its key lookup import is pinned", () => {
    const imported = ["../src/appleIdentity.ts", "../src/appleJwks.ts"].flatMap((path) =>
      [...text(path).matchAll(LOCAL_IMPORT)].map((m) => `../src/${m[1]}.ts`));
    expect(imported.filter((path) => !(path in APPROVED_SHA256))).toEqual([]);
    expect(Object.keys(SRC).sort()).toEqual(Object.keys(APPROVED_SHA256));
  });
});
