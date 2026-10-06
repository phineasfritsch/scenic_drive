/**
 * T-0278 R1, R5, R7: what a verified attestation writes and answers - the key row, the challenge consumed, and an
 * HS256 session JWT equal to the test's own signing of the ruled claims - at every bound (challenge expiry,
 * certificate validity, the aaguid flag, the secret's length), single use (replay, an already-attested key), and the
 * shipped ROUTES: /attest/challenge issues and prunes, /attest with the pinned Apple root refuses the test chain,
 * and without the secret both routes are 503 with nothing written. Answers and tables are compared WHOLE.
 */
import { env } from "cloudflare:test";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { APPLE_APP_ATTEST_ROOT_CA } from "../src/appAttest";
import { attestDepsFromEnv } from "../src/attest";
import { LIVE_CHALLENGE } from "../src/attestStore";
import { ROUTES, type Env } from "../src/index";
import { b64url } from "./appleChain";
import {
  AAGUID_DEVELOP, ACCOUNT, attestation, bodyOf, CHALLENGE, DEVICE, freshAttestTables, mintJwt, NOW, OTHER_CHALLENGE, postAttest, seedChallenge,
  SECRET, sha, tables, testDeps, type Attested,
} from "./attestHarness";

const REFUSED = { status: 400, json: { error: "invalid_attestation" } };
const UNAVAILABLE = { status: 503, json: { error: "attest_unavailable" } };
const S = NOW / 1000;
const hex = (b: Uint8Array) => Array.from(b, (x) => (x < 16 ? "0" : "") + x.toString(16)).join("");

const keyRow = (a: Attested, over: Record<string, unknown> = {}) =>
  ({ key_id: a.keyId, device_id: DEVICE, public_key: a.publicKeyHex, environment: "production", attested_at: NOW, ...over });

async function granted(claims: Record<string, unknown>) {
  return { status: 200, json: { token: await mintJwt(claims), expires_at: "2026-10-06T13:00:00.000Z" } };
}

async function route(path: "/attest" | "/attest/challenge", e: Partial<Env>, init: RequestInit = { method: "POST" }) {
  const req = new Request(`https://scenic-api.test${path}`, init);
  const response = await ROUTES[path]!(req, { ...(env as unknown as Env), ...e }, new URL(req.url));
  return { status: response.status, json: (await response.json()) as Record<string, unknown> };
}

beforeEach(async () => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  await freshAttestTables();
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.useRealTimers();
});

describe("a verified attestation commits the key, consumes the challenge and answers the session JWT", () => {
  it("production aaguid, no account token: {iss, sub, iat, exp} with exp = iat + 3600", async () => {
    await seedChallenge(CHALLENGE, NOW + 60_000);
    const a = await attestation();
    expect({ answer: await postAttest(bodyOf(a), testDeps(a)), tables: await tables() }).toEqual({
      answer: await granted({ iss: "scenic-api", sub: DEVICE, iat: S, exp: S + 3600 }),
      tables: { challenges: [], keys: [keyRow(a)] },
    });
  });

  it("an upper-case device and account token are lowercased; act carries the account token", async () => {
    await seedChallenge(CHALLENGE, NOW + 60_000);
    const a = await attestation();
    const answer = await postAttest(bodyOf(a, { device: DEVICE.toUpperCase(), appAccountToken: ACCOUNT.toUpperCase() }), testDeps(a));
    expect({ answer, tables: await tables() }).toEqual({
      answer: await granted({ iss: "scenic-api", sub: DEVICE, iat: S, exp: S + 3600, act: ACCOUNT }),
      tables: { challenges: [], keys: [keyRow(a)] },
    });
  });

  it("appattestdevelop is accepted under APP_ATTEST_ALLOW_DEVELOP=1 and stored as development", async () => {
    await seedChallenge(CHALLENGE, NOW + 60_000);
    const a = await attestation({ aaguid: AAGUID_DEVELOP });
    expect({ answer: await postAttest(bodyOf(a), testDeps(a, { APP_ATTEST_ALLOW_DEVELOP: "1" })), tables: await tables() }).toEqual({
      answer: await granted({ iss: "scenic-api", sub: DEVICE, iat: S, exp: S + 3600 }),
      tables: { challenges: [], keys: [keyRow(a, { environment: "development" })] },
    });
  });

  it("a challenge expiring 1 ms after now is live; one expiring at now is refused with nothing written", async () => {
    const a = await attestation();
    await seedChallenge(CHALLENGE, NOW);
    expect({ answer: await postAttest(bodyOf(a), testDeps(a)), tables: await tables() })
      .toEqual({ answer: REFUSED, tables: { challenges: [{ challenge: CHALLENGE, expires_at: NOW }], keys: [] } });
    await freshAttestTables();
    await seedChallenge(CHALLENGE, NOW + 1);
    expect((await postAttest(bodyOf(a), testDeps(a))).status).toBe(200);
    expect(await tables()).toEqual({ challenges: [], keys: [keyRow(a)] });
  });

  it("every certificate valid from now and until now is accepted (the validity bounds are inclusive)", async () => {
    await seedChallenge(CHALLENGE, NOW + 60_000);
    const at = { notBefore: NOW, notAfter: NOW };
    const a = await attestation({ leaf: at, intermediate: at, root: at });
    expect((await postAttest(bodyOf(a), testDeps(a))).status).toBe(200);
  });

  it("authData of exactly 87 bytes (no COSE key) is accepted", async () => {
    await seedChallenge(CHALLENGE, NOW + 60_000);
    const a = await attestation({ authData: (d) => d.slice(0, 87) });
    expect((await postAttest(bodyOf(a), testDeps(a))).status).toBe(200);
  });

  it("a replay of an accepted attestation is refused and changes nothing", async () => {
    await seedChallenge(CHALLENGE, NOW + 60_000);
    const a = await attestation();
    await postAttest(bodyOf(a), testDeps(a));
    const after = await tables();
    expect({ answer: await postAttest(bodyOf(a), testDeps(a)), tables: await tables() }).toEqual({ answer: REFUSED, tables: after });
  });

  it("an already-attested key is refused and its live challenge is not consumed", async () => {
    await seedChallenge(CHALLENGE, NOW + 60_000);
    const a = await attestation();
    const seeded = keyRow(a, { device_id: "11111111-2222-4333-8444-555555555555", attested_at: NOW - 1 });
    await env.DB.prepare("INSERT INTO attested_keys VALUES (?1, ?2, ?3, ?4, ?5)")
      .bind(seeded.key_id, seeded.device_id, seeded.public_key, seeded.environment, seeded.attested_at).run();
    expect({ answer: await postAttest(bodyOf(a), testDeps(a)), tables: await tables() }).toEqual({
      answer: REFUSED, tables: { challenges: [{ challenge: CHALLENGE, expires_at: NOW + 60_000 }], keys: [seeded] },
    });
  });

  it("a secret of 31 characters is absent (503, nothing written); 32 characters serve", async () => {
    await seedChallenge(CHALLENGE, NOW + 60_000);
    const a = await attestation();
    expect({ answer: await postAttest(bodyOf(a), testDeps(a, { SESSION_JWT_SECRET: SECRET.slice(0, 31) })), tables: await tables() })
      .toEqual({ answer: UNAVAILABLE, tables: { challenges: [{ challenge: CHALLENGE, expires_at: NOW + 60_000 }], keys: [] } });
    expect((await postAttest(bodyOf(a), testDeps(a, { SESSION_JWT_SECRET: SECRET.slice(0, 32) }))).status).toBe(200);
  });
});

/**
 * env.DB, except that `between` runs after the shipped LIVE_CHALLENGE read has answered and before the commit batch:
 * what a concurrent request does in that gap. Every statement still runs against the real D1.
 */
function interleaved(between: () => Promise<unknown>): D1Database {
  const db = env.DB;
  return {
    prepare: (sql: string) => (sql !== LIVE_CHALLENGE ? db.prepare(sql) : {
      bind: (...args: unknown[]) => ({ first: async () => { const row = await db.prepare(sql).bind(...args).first(); await between(); return row; } }),
    }),
    batch: (statements: D1PreparedStatement[]) => db.batch(statements),
  } as unknown as D1Database;
}

describe("the commit batch is the authority: a challenge gone or expired after the live read commits nothing (R1)", () => {
  const RIVAL = { key_id: "rival-key", device_id: DEVICE, public_key: "00", environment: "production", attested_at: NOW - 1 };
  const rivalCommits = () => env.DB.batch([
    env.DB.prepare("INSERT INTO attested_keys (key_id, device_id, public_key, environment, attested_at) VALUES (?1, ?2, ?3, ?4, ?5)")
      .bind(RIVAL.key_id, RIVAL.device_id, RIVAL.public_key, RIVAL.environment, RIVAL.attested_at),
    env.DB.prepare("DELETE FROM attest_challenges WHERE challenge = ?1").bind(CHALLENGE),
  ]);
  const expiresAt = (at: number) => () => env.DB.prepare("UPDATE attest_challenges SET expires_at = ?1 WHERE challenge = ?2").bind(at, CHALLENGE).run();

  it("a concurrent attestation consumes the challenge after the read: 400, the rival key stands, another live challenge is untouched", async () => {
    await seedChallenge(CHALLENGE, NOW + 60_000);
    await seedChallenge(OTHER_CHALLENGE, NOW + 60_000);
    const a = await attestation();
    expect({ answer: await postAttest(bodyOf(a), { ...testDeps(a), db: interleaved(rivalCommits) }), tables: await tables() }).toEqual({
      answer: REFUSED, tables: { challenges: [{ challenge: OTHER_CHALLENGE, expires_at: NOW + 60_000 }], keys: [RIVAL] },
    });
  });

  it("the batch sees the challenge expiring at now: 400 and nothing written (bound)", async () => {
    await seedChallenge(CHALLENGE, NOW + 60_000);
    const a = await attestation();
    expect({ answer: await postAttest(bodyOf(a), { ...testDeps(a), db: interleaved(expiresAt(NOW)) }), tables: await tables() })
      .toEqual({ answer: REFUSED, tables: { challenges: [{ challenge: CHALLENGE, expires_at: NOW }], keys: [] } });
  });

  it("the batch sees the challenge expiring 1 ms after now: the key commits and the challenge is consumed (bound)", async () => {
    await seedChallenge(CHALLENGE, NOW + 60_000);
    const a = await attestation();
    expect({ answer: await postAttest(bodyOf(a), { ...testDeps(a), db: interleaved(expiresAt(NOW + 1)) }), tables: await tables() }).toEqual({
      answer: await granted({ iss: "scenic-api", sub: DEVICE, iat: S, exp: S + 3600 }), tables: { challenges: [], keys: [keyRow(a)] },
    });
  });
});

describe("the shipped ROUTES['/attest/challenge'] and ROUTES['/attest']", () => {
  it("/attest/challenge issues 32 random bytes as base64url, live 300 s, and prunes the expired", async () => {
    await seedChallenge("expired-at-now", NOW);
    await seedChallenge("live-for-1-ms", NOW + 1);
    vi.spyOn(crypto, "getRandomValues").mockImplementation(<T extends ArrayBufferView | null>(array: T) => {
      (array as unknown as Uint8Array).fill(7);
      return array;
    });
    const sevens = b64url(new Uint8Array(32).fill(7));
    expect({ answer: await route("/attest/challenge", { SESSION_JWT_SECRET: SECRET }), tables: await tables() }).toEqual({
      answer: { status: 200, json: { challenge: sevens, expires_at: "2026-10-06T12:05:00.000Z" } },
      tables: { challenges: [{ challenge: sevens, expires_at: NOW + 300_000 }, { challenge: "live-for-1-ms", expires_at: NOW + 1 }], keys: [] },
    });
  });

  it("an issued challenge attests once: the second attestation over it is refused", async () => {
    const { json } = await route("/attest/challenge", { SESSION_JWT_SECRET: SECRET });
    const challenge = json.challenge as string;
    const a = await attestation({ challenge });
    expect((await postAttest(bodyOf(a, { challenge }), testDeps(a))).status).toBe(200);
    const b = await attestation({ challenge });
    expect(await postAttest(bodyOf(b, { challenge }), testDeps(b))).toEqual(REFUSED);
    expect(await tables()).toEqual({ challenges: [], keys: [keyRow(a)] });
  });

  it("without SESSION_JWT_SECRET both routes are 503 attest_unavailable and nothing is written", async () => {
    await seedChallenge(CHALLENGE, NOW + 60_000);
    const a = await attestation();
    const post = { method: "POST", body: JSON.stringify(bodyOf(a)) };
    expect([await route("/attest/challenge", { SESSION_JWT_SECRET: undefined }), await route("/attest", { SESSION_JWT_SECRET: undefined }, post)])
      .toEqual([UNAVAILABLE, UNAVAILABLE]);
    expect(await tables()).toEqual({ challenges: [{ challenge: CHALLENGE, expires_at: NOW + 60_000 }], keys: [] });
  });

  it("GET on either route is 405", async () => {
    const get = { method: "GET" };
    expect([await route("/attest/challenge", { SESSION_JWT_SECRET: SECRET }, get), await route("/attest", { SESSION_JWT_SECRET: SECRET }, get)])
      .toEqual([{ status: 405, json: { error: "POST only" } }, { status: 405, json: { error: "POST only" } }]);
  });

  it("the pinned Apple root refuses a chain valid in every respect but its self-made root (zero state change)", async () => {
    await seedChallenge(CHALLENGE, NOW + 60_000);
    const a = await attestation();
    const answer = await route("/attest", { SESSION_JWT_SECRET: SECRET }, { method: "POST", body: JSON.stringify(bodyOf(a)) });
    expect({ answer, tables: await tables() })
      .toEqual({ answer: REFUSED, tables: { challenges: [{ challenge: CHALLENGE, expires_at: NOW + 60_000 }], keys: [] } });
  });

  it("the shipped root is Apple's App Attestation Root CA by its measured SHA-256 (Log R2)", async () => {
    const der = Uint8Array.from(atob(APPLE_APP_ATTEST_ROOT_CA), (c) => c.charCodeAt(0));
    const deps = attestDepsFromEnv(env as unknown as Env);
    expect([hex(await sha(der)), deps.rootSha256, hex(await sha(deps.rootDer))]).toEqual(Array(3)
      .fill("1cb9823ba28ba6ad2d33a006941de2ae4f513ef1d4e831b9f7e0fa7b6242c932"));
  });
});
