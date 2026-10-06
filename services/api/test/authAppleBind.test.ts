/**
 * T-0287 R4, R6 (P-PRIV-04): the JWKS cache (TTL bound, one refetch for an unknown kid only past the min-age bound,
 * never a fallback key, a failing fetch 503 with the cache and every table unchanged) and the bind (the authorization
 * code exchanged only with the owner's client secret, the refresh token stored only from a 200 that carries one, the
 * rebinding rules, act carried and apple added to the session JWT). Answers, tables and Apple calls compared WHOLE.
 */
import { env } from "cloudflare:test";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { emptyJwksCache, type JwksCache } from "../src/appleJwks";
import { verifySession } from "../src/sessionJwt";
import {
  ACCOUNT, allTables, APPLE_USER, AUTH_CODE, CLIENT_SECRET, DEVICE, exchangeCall, fakeAppleFetch, freshAllTables, grantedSession,
  identityClaims, jsonResponse, keysCall, NOW, OTHER_APPLE_USER, postApple, rsaKey, S, SECRET, sessionToken, signJws, siwaDeps,
  type FakeApple, type TestKey,
} from "./siwaHarness";

const TTL = 3_600_000;
const MIN_AGE = 60_000;
let K1: TestKey, K2: TestKey;

beforeAll(async () => {
  [K1, K2] = await Promise.all([rsaKey("K1"), rsaKey("K2")]);
});

beforeEach(async () => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  await freshAllTables();
});

afterEach(() => {
  vi.useRealTimers();
});

async function cached(keys: TestKey[], fetchedAtMs: number): Promise<JwksCache> {
  const map = new Map<string, CryptoKey>();
  for (const k of keys) {
    map.set(k.kid, await crypto.subtle.importKey("jwk", { kty: "RSA", n: k.jwk.n as string, e: k.jwk.e as string, alg: "RS256", ext: true },
      { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"]));
  }
  return { keys: map, fetchedAtMs };
}

async function signIn(o: { served?: TestKey[]; signer?: TestKey; cache?: JwksCache; spec?: FakeApple; secret?: boolean; session?: Record<string, unknown> } = {}) {
  const bearer = await sessionToken(o.session ?? {});
  const apple = fakeAppleFetch(o.served ?? [K1], o.spec ?? {});
  const signer = o.signer ?? K1;
  const identityToken = await signJws({ alg: "RS256", kid: signer.kid }, await identityClaims(bearer), signer.privateKey);
  const deps = siwaDeps(apple.fetchImpl, o.secret ? { APPLE_CLIENT_SECRET: CLIENT_SECRET } : {}, o.cache ?? emptyJwksCache());
  const got = await postApple(deps, { identityToken, authorizationCode: AUTH_CODE }, bearer);
  return { got, calls: apple.calls, accounts: (await allTables()).apple_accounts, cache: deps.jwks };
}

const bound = (refresh: string | null, sub = APPLE_USER) => [{ device_id: DEVICE, apple_sub: sub, refresh_token: refresh, bound_at: NOW }];
const UNAVAILABLE = { status: 503, json: { error: "apple_unavailable" } };
const REFUSED = { status: 400, json: { error: "invalid_identity_token" } };

describe("the JWKS cache (R4)", () => {
  it("a cache fetched TTL - 1 ms ago serves without a fetch (bound)", async () => {
    const r = await signIn({ cache: await cached([K1], NOW - TTL + 1) });
    expect({ got: r.got, calls: r.calls }).toEqual({ got: await grantedSession({ apple: APPLE_USER }), calls: [] });
  });

  it("a cache fetched exactly TTL ago is refetched (bound)", async () => {
    const r = await signIn({ cache: await cached([K1], NOW - TTL) });
    expect({ got: r.got, calls: r.calls, at: r.cache.fetchedAtMs }).toEqual({ got: await grantedSession({ apple: APPLE_USER }), calls: [keysCall], at: NOW });
  });

  it("an unknown kid in a set MIN_AGE old buys one refetch, which finds the rotated key", async () => {
    const r = await signIn({ served: [K1, K2], signer: K2, cache: await cached([K1], NOW - MIN_AGE) });
    expect({ got: r.got, calls: r.calls }).toEqual({ got: await grantedSession({ apple: APPLE_USER }), calls: [keysCall] });
  });

  it("an unknown kid in a set MIN_AGE - 1 ms old is refused without a fetch (bound)", async () => {
    const r = await signIn({ served: [K1, K2], signer: K2, cache: await cached([K1], NOW - MIN_AGE + 1) });
    expect({ got: r.got, calls: r.calls, accounts: r.accounts }).toEqual({ got: REFUSED, calls: [], accounts: [] });
  });

  it("an unknown kid still absent after the one refetch is refused - no second fetch, no fallback key", async () => {
    const r = await signIn({ served: [K1], signer: K2, cache: await cached([K1], NOW - MIN_AGE) });
    expect({ got: r.got, calls: r.calls, accounts: r.accounts }).toEqual({ got: REFUSED, calls: [keysCall], accounts: [] });
  });

  it("a kid listed twice is dropped: refused", async () => {
    const r = await signIn({ served: [K1, { ...K2, jwk: { ...K2.jwk, kid: "K1" } }] });
    expect({ got: r.got, calls: r.calls, accounts: r.accounts }).toEqual({ got: REFUSED, calls: [keysCall], accounts: [] });
  });

  const FAILURES: [string, FakeApple][] = [
    ["the JWKS answers 500", { keys: () => jsonResponse({ keys: [] }, 500) }],
    ["the JWKS fetch throws", { keys: () => { throw new Error("offline"); } }],
    ["the JWKS is not JSON", { keys: () => new Response("<html>", { status: 200 }) }],
    ["the JWKS has no keys array", { keys: () => jsonResponse({ keys: {} }) }],
  ];
  for (const [name, spec] of FAILURES) {
    it(`503 apple_unavailable, nothing written, the cache unchanged: ${name}`, async () => {
      const empty = await signIn({ spec });
      const stale = await cached([K1], NOW - TTL);
      const expired = await signIn({ spec, cache: stale });
      expect({ empty: [empty.got, empty.calls, empty.accounts, empty.cache], expired: [expired.got, expired.calls, expired.accounts, expired.cache.fetchedAtMs] })
        .toEqual({ empty: [UNAVAILABLE, [keysCall], [], emptyJwksCache()], expired: [UNAVAILABLE, [keysCall], [], NOW - TTL] });
    });
  }
});

describe("the bind: exchange, refresh token, rebinding and the session JWT (R6)", () => {
  it("without the client secret: no exchange, refresh_token NULL", async () => {
    const r = await signIn();
    expect({ got: r.got, calls: r.calls, accounts: r.accounts }).toEqual({ got: await grantedSession({ apple: APPLE_USER }), calls: [keysCall], accounts: bound(null) });
  });

  it("with the client secret: the code is exchanged and the refresh token stored", async () => {
    const r = await signIn({ secret: true });
    expect({ got: r.got, calls: r.calls, accounts: r.accounts }).toEqual({ got: await grantedSession({ apple: APPLE_USER }), calls: [keysCall, exchangeCall()], accounts: bound("r.fresh") });
  });

  const EXCHANGE_FAILS: [string, FakeApple][] = [
    ["the exchange answers 400", { exchange: () => jsonResponse({ error: "invalid_grant" }, 400) }],
    ["the exchange throws", { exchange: () => { throw new Error("offline"); } }],
    ["a 200 without a refresh_token", { exchange: () => jsonResponse({ access_token: "a" }) }],
    ["a 200 whose refresh_token is not a string", { exchange: () => jsonResponse({ refresh_token: 7 }) }],
    ["a 200 whose refresh_token is empty", { exchange: () => jsonResponse({ refresh_token: "" }) }],
  ];
  for (const [name, spec] of EXCHANGE_FAILS) {
    it(`bound with refresh_token NULL: ${name}`, async () => {
      const r = await signIn({ secret: true, spec });
      expect({ got: r.got, calls: r.calls, accounts: r.accounts }).toEqual({ got: await grantedSession({ apple: APPLE_USER }), calls: [keysCall, exchangeCall()], accounts: bound(null) });
    });
  }

  it("rebinding to the same Apple user without a new token keeps the stored one", async () => {
    await env.DB.prepare("INSERT INTO apple_accounts VALUES (?1, ?2, 'r.old', 1)").bind(DEVICE, APPLE_USER).run();
    const r = await signIn({ secret: true, spec: EXCHANGE_FAILS[0]![1] });
    expect(r.accounts).toEqual(bound("r.old"));
  });

  it("rebinding to another Apple user replaces the sub and never keeps the old user's token", async () => {
    await env.DB.prepare("INSERT INTO apple_accounts VALUES (?1, ?2, 'r.old', 1)").bind(DEVICE, OTHER_APPLE_USER).run();
    const failed = await signIn({ secret: true, spec: EXCHANGE_FAILS[0]![1] });
    await env.DB.prepare("UPDATE apple_accounts SET apple_sub = ?1, refresh_token = 'r.old'").bind(OTHER_APPLE_USER).run();
    const fresh = await signIn({ secret: true });
    expect([failed.accounts, fresh.accounts]).toEqual([bound(null), bound("r.fresh")]);
  });

  it("act is carried from the session and apple added; the answer verifies through the shipped verifier", async () => {
    const r = await signIn({ session: { act: ACCOUNT } });
    const token = (r.got.json as { token: string }).token;
    expect({ got: r.got, claims: await verifySession(SECRET, token, NOW) })
      .toEqual({ got: await grantedSession({ act: ACCOUNT, apple: APPLE_USER }), claims: { sub: DEVICE, act: ACCOUNT, apple: APPLE_USER } });
  });

  it("a session JWT whose apple claim is not an Apple user id does not verify", async () => {
    const bad = await sessionToken({ apple: "has/slash" });
    const good = await sessionToken({ apple: APPLE_USER });
    expect([await verifySession(SECRET, bad, NOW), await verifySession(SECRET, good, NOW)]).toEqual([null, { sub: DEVICE, apple: APPLE_USER }]);
  });

  it("without SESSION_JWT_SECRET, or one of 31 characters: 503 auth_unavailable, no Apple call, nothing written", async () => {
    const out = [];
    for (const secret of [undefined, "s".repeat(31)]) {
      const apple = fakeAppleFetch([K1]);
      const deps = siwaDeps(apple.fetchImpl, { SESSION_JWT_SECRET: secret });
      const bearer = await sessionToken();
      const identityToken = await signJws({ alg: "RS256", kid: "K1" }, await identityClaims(bearer), K1.privateKey);
      out.push([await postApple(deps, { identityToken, authorizationCode: AUTH_CODE }, bearer), apple.calls, (await allTables()).apple_accounts]);
    }
    expect(out).toEqual([[{ status: 503, json: { error: "auth_unavailable" } }, [], []], [{ status: 503, json: { error: "auth_unavailable" } }, [], []]]);
  });

  it("a GET is 405 with no Apple call", async () => {
    const apple = fakeAppleFetch([K1]);
    expect([await postApple(siwaDeps(apple.fetchImpl), null, await sessionToken(), "GET"), apple.calls]).toEqual([{ status: 405, json: { error: "POST only" } }, []]);
  });
});
