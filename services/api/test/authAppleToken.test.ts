/**
 * T-0287 R1, R2, R3, R5 (P-PRIV-04): POST /auth/apple verifies the identity token per Apple's steps. Every defect row
 * is refused 400 invalid_identity_token over BOTH table variants (empty, and a user already bound) with every table
 * compared WHOLE to its state before and the Apple calls recorded WHOLE (no exchange, the JWKS only when a kid was
 * read); every bound is a pair of rows, the accepted side answering the session JWT the test signs itself.
 */
import { env } from "cloudflare:test";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import {
  ACCOUNT, allTables, APPLE_USER, AUTH_CODE, DEVICE, fakeAppleFetch, freshAllTables, grantedSession, identityClaims, keysCall, mintJwt,
  NOW, OTHER_APPLE_USER, postApple, rsaKey, S, sessionToken, sha256Hex, signJws, siwaDeps, type AppleCall, type TestKey,
} from "./siwaHarness";

const REFUSED = { status: 400, json: { error: "invalid_identity_token" } };
const HEADER = { alg: "RS256", kid: "K1" };
let K1: TestKey, OUTSIDER: TestKey, SMALL: TestKey, RS512: TestKey, ENC: TestKey;

beforeAll(async () => {
  [K1, OUTSIDER, SMALL, RS512, ENC] = await Promise.all([rsaKey("K1"), rsaKey("K1"), rsaKey("SMALL", 1024),
    rsaKey("K3", 2048, { alg: "RS512" }), rsaKey("K4", 2048, { use: "enc" })]);
});

beforeEach(async () => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  await freshAllTables();
});

afterEach(() => {
  vi.useRealTimers();
});

const VARIANTS: [string, () => Promise<void>][] = [
  ["empty tables", async () => {}],
  ["the device already bound, keyed and entitled", async () => {
    await env.DB.prepare("INSERT INTO apple_accounts VALUES (?1, ?2, ?3, ?4)").bind(DEVICE, OTHER_APPLE_USER, "r.old", NOW - 1000).run();
    await env.DB.prepare("INSERT INTO attested_keys VALUES ('k', ?1, '04', 'production', 1)").bind(DEVICE).run();
    await env.DB.prepare("INSERT INTO entitlements VALUES ('t1', ?1, 'Production', 'p', 'active', NULL, 'SUBSCRIBED', NULL, 1)").bind(ACCOUNT).run();
  }],
];

/** A valid token whose total length is exactly `length` (a pad claim sized to it); throws when none is found. */
async function tokenOfLength(bearer: string, length: number): Promise<string> {
  for (let spaces = 0; spaces < 4; spaces += 1) {
    const header = `{"alg":"RS256",${" ".repeat(spaces)}"kid":"K1"}`;
    const base = (await signJws(header, await identityClaims(bearer, { pad: "" }), K1.privateKey)).length;
    const start = Math.max(0, Math.floor(((length - base) * 3) / 4) - 4);
    for (let n = start; n < start + 12; n += 1) {
      const t = await signJws(header, await identityClaims(bearer, { pad: "x".repeat(n) }), K1.privateKey);
      if (t.length === length) return t;
    }
  }
  throw new Error(`no token of length ${length}`);
}

interface Row { name: string; keys: boolean; make: (bearer: string) => Promise<unknown> }
const body = (identityToken: unknown, authorizationCode: unknown = AUTH_CODE) => ({ identityToken, authorizationCode });
const token = async (bearer: string, over: Record<string, unknown> = {}, header: Record<string, unknown> | string = HEADER, key = K1.privateKey) =>
  signJws(header, await identityClaims(bearer, over), key);
const claim = (name: string, over: Record<string, unknown>): Row => ({ name, keys: true, make: async (b) => body(await token(b, over)) });
const head = (name: string, header: Record<string, unknown> | string): Row => ({ name, keys: false, make: async (b) => body(await token(b, {}, header)) });

const DEFECTS: Row[] = [
  { name: "a body that is not JSON", keys: false, make: async () => "{" },
  { name: "a body that is an array", keys: false, make: async (b) => [await token(b)] },
  { name: "authorizationCode missing", keys: false, make: async (b) => ({ identityToken: await token(b) }) },
  { name: "a key outside {identityToken, authorizationCode}", keys: false, make: async (b) => ({ ...body(await token(b)), nonce: "n" }) },
  { name: "identityToken not a string", keys: false, make: async () => body(7) },
  { name: "authorizationCode of 513 characters (bound)", keys: false, make: async (b) => body(await token(b), "a".repeat(513)) },
  { name: "authorizationCode empty", keys: false, make: async (b) => body(await token(b), "") },
  { name: "authorizationCode with a space", keys: false, make: async (b) => body(await token(b), "c0de x") },
  { name: "identityToken of 8193 characters (bound)", keys: false, make: async (b) => body(await tokenOfLength(b, 8193)) },
  { name: "two segments", keys: false, make: async (b) => body((await token(b)).split(".").slice(0, 2).join(".")) },
  { name: "four segments", keys: false, make: async (b) => body(`${await token(b)}.AAAA`) },
  { name: "a '+' in the payload segment", keys: false, make: async (b) => { const [h, p, s] = (await token(b)).split("."); return body(`${h}.+${p}.${s}`); } },
  head("alg none", { alg: "none", kid: "K1" }),
  head("alg HS256", { alg: "HS256", kid: "K1" }),
  head("alg ES256", { alg: "ES256", kid: "K1" }),
  head("alg RS512", { alg: "RS512", kid: "K1" }),
  head("alg missing", { kid: "K1" }),
  head("kid missing", { alg: "RS256" }),
  head("kid a number", { alg: "RS256", kid: 1 }),
  head("kid empty", { alg: "RS256", kid: "" }),
  head("a jku header", { alg: "RS256", kid: "K1", jku: "https://attacker.example/keys" }),
  head("typ JWS", { alg: "RS256", kid: "K1", typ: "JWS" }),
  head("a header that is not JSON", "{"),
  head("a header that is an array", "[\"RS256\"]"),
  { name: "an unknown kid: no fallback to the only key", keys: true, make: async (b) => body(await token(b, {}, { alg: "RS256", kid: "K9" })) },
  { name: "another key's signature under Apple's kid", keys: true, make: async (b) => body(await token(b, {}, HEADER, OUTSIDER.privateKey)) },
  { name: "a signature with one byte changed", keys: true, make: async (b) => { const [h, p, s] = (await token(b)).split("."); return body(`${h}.${p}.${s!.startsWith("A") ? "B" : "A"}${s!.slice(1)}`); } },
  { name: "a signature that is not base64url of whole bytes", keys: true, make: async (b) => body(`${await token(b)}A`) },
  { name: "a 1024-bit key Apple's set lists is not usable", keys: true, make: async (b) => body(await token(b, {}, { alg: "RS256", kid: "SMALL" }, SMALL.privateKey)) },
  { name: "a key listed with alg RS512 is not usable", keys: true, make: async (b) => body(await token(b, {}, { alg: "RS256", kid: "K3" }, RS512.privateKey)) },
  { name: "a key listed with use enc is not usable", keys: true, make: async (b) => body(await token(b, {}, { alg: "RS256", kid: "K4" }, ENC.privateKey)) },
  claim("iss over http", { iss: "http://appleid.apple.com" }),
  claim("iss with a trailing slash", { iss: "https://appleid.apple.com/" }),
  claim("iss missing", { iss: undefined }),
  claim("aud another bundle", { aud: "com.phineasfritsch.other" }),
  claim("aud an array holding the bundle", { aud: ["com.phineasfritsch.scenicdrive"] }),
  claim("exp = now (bound)", { exp: S }),
  claim("exp missing", { exp: undefined }),
  claim("exp a string", { exp: String(S + 600) }),
  claim("exp a fraction", { exp: S + 600.5 }),
  claim("exp true", { exp: true }),
  claim("iat = now + 61 (bound)", { iat: S + 61 }),
  claim("iat = now - 601 (bound)", { iat: S - 601 }),
  claim("iat missing", { iat: undefined }),
  claim("iat null", { iat: null }),
  claim("sub missing", { sub: undefined }),
  claim("sub empty", { sub: "" }),
  claim("sub of 65 characters (bound)", { sub: "1".repeat(65) }),
  claim("sub with a slash", { sub: "001234/abc" }),
  claim("sub a number", { sub: 1234 }),
  claim("nonce missing", { nonce: undefined }),
  { name: "nonce of another session", keys: true, make: async (b) => body(await token(b, { nonce: await sha256Hex(await sessionToken({}, S - 1)) })) },
  { name: "nonce in upper-case hex", keys: true, make: async (b) => body(await token(b, { nonce: (await sha256Hex(b)).toUpperCase() })) },
  claim("nonce the raw session token, unhashed", { nonce: "PLACEHOLDER" }),
  { name: "a payload that is not JSON", keys: true, make: async () => body(await signJws(HEADER, "{", K1.privateKey)) },
  { name: "a payload that is an array", keys: true, make: async () => body(await signJws(HEADER, "[]", K1.privateKey)) },
];

async function refusal(row: Row, seed: () => Promise<void>) {
  await freshAllTables();
  await seed();
  const before = await allTables();
  const bearer = await sessionToken();
  const apple = fakeAppleFetch([K1, SMALL, RS512, ENC]);
  let made = await row.make(bearer);
  if (row.name === "nonce the raw session token, unhashed") made = body(await token(bearer, { nonce: bearer }));
  const answer = await postApple(siwaDeps(apple.fetchImpl), made, bearer);
  return { answer, tables: await allTables(), calls: apple.calls, before };
}

describe("every identity-token defect is refused with zero state change (R2, R5, P-PRIV-04)", () => {
  it("the variants differ: a row that ignored the seeded user would be seen", async () => {
    const states = [];
    for (const [, seed] of VARIANTS) { await freshAllTables(); await seed(); states.push(await allTables()); }
    expect(states[0]).not.toEqual(states[1]);
  });

  for (const row of DEFECTS) {
    it(`refused: ${row.name}`, async () => {
      for (const [variant, seed] of VARIANTS) {
        const got = await refusal(row, seed);
        const calls: AppleCall[] = row.keys ? [keysCall] : [];
        expect({ variant, answer: got.answer, tables: got.tables, calls: got.calls })
          .toEqual({ variant, answer: REFUSED, tables: got.before, calls });
      }
    });
  }
});

describe("the caller must hold a session JWT (R1)", () => {
  const BEARERS: [string, () => Promise<string | null>][] = [
    ["no Authorization header", async () => null],
    ["a Bearer that is not a JWT", async () => "not-a-jwt"],
    ["a session signed with another secret", async () => mintJwt({ iss: "scenic-api", sub: DEVICE, iat: S, exp: S + 3600 }, "another-secret-0123456789abcdef-xyz")],
    ["a session that expired at now", async () => sessionToken({}, S - 3600)],
  ];
  for (const [name, make] of BEARERS) {
    it(`401, nothing written, no Apple call: ${name}`, async () => {
      const bearer = await sessionToken();
      const apple = fakeAppleFetch([K1]);
      const got = await postApple(siwaDeps(apple.fetchImpl), body(await token(bearer)), await make());
      const empty = Object.fromEntries(Object.keys(await allTables()).map((k) => [k, []]));
      expect({ got, tables: await allTables(), calls: apple.calls }).toEqual({ got: { status: 401, json: { error: "unauthorized" } }, tables: empty, calls: [] });
    });
  }
});

describe("every bound's accepted side binds the Apple sub and answers the session JWT (R5, R6)", () => {
  const ACCEPTED: [string, (bearer: string) => Promise<unknown>, string][] = [
    ["exp = now + 1", async (b) => body(await token(b, { exp: S + 1 })), APPLE_USER],
    ["iat = now + 60", async (b) => body(await token(b, { iat: S + 60 })), APPLE_USER],
    ["iat = now - 600", async (b) => body(await token(b, { iat: S - 600 })), APPLE_USER],
    ["sub of 64 characters", async (b) => body(await token(b, { sub: "1".repeat(64) })), "1".repeat(64)],
    ["authorizationCode of 512 characters", async (b) => body(await token(b), "a".repeat(512)), APPLE_USER],
    ["identityToken of exactly 8192 characters", async (b) => body(await tokenOfLength(b, 8192)), APPLE_USER],
    ["typ JWT in the header", async (b) => body(await token(b, {}, { alg: "RS256", kid: "K1", typ: "JWT" })), APPLE_USER],
    ["header keys in the other order", async (b) => body(await token(b, {}, "{\"kid\":\"K1\",\"alg\":\"RS256\"}")), APPLE_USER],
    ["only the required claims", async (b) => body(await signJws(HEADER, { iss: "https://appleid.apple.com", aud: "com.phineasfritsch.scenicdrive",
      exp: S + 600, iat: S, sub: APPLE_USER, nonce: await sha256Hex(b) }, K1.privateKey)), APPLE_USER],
  ];
  for (const [name, make, sub] of ACCEPTED) {
    it(`accepted: ${name}`, async () => {
      const bearer = await sessionToken();
      const apple = fakeAppleFetch([K1, SMALL, RS512, ENC]);
      const made = await make(bearer);
      const got = await postApple(siwaDeps(apple.fetchImpl), made, bearer);
      const tables = await allTables();
      expect({ got, accounts: tables.apple_accounts, calls: apple.calls }).toEqual({
        got: await grantedSession({ apple: sub }),
        accounts: [{ device_id: DEVICE, apple_sub: sub, refresh_token: null, bound_at: NOW }],
        calls: [keysCall],
      });
    });
  }
});
