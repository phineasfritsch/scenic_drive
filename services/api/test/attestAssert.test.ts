/**
 * T-0280 R2-R4: POST /attest/assert through the shipped ROUTES. An assertion by an attested key over a live challenge,
 * with a counter strictly above the stored one, stores that counter, consumes the challenge and answers a session JWT
 * for the key's STORED device; every defect is 400 invalid_assertion with all four tables unchanged. Answers and
 * tables are compared WHOLE, the stored counter as rows. No dep is replaced: the shipped wiring needs no root.
 */
import { env } from "cloudflare:test";
import { afterEach, beforeAll, beforeEach, describe, expect, it, vi } from "vitest";
import { KEY_FOR_ASSERTION } from "../src/attestStore";
import { b64 } from "./appleChain";
import { ACCOUNT, CHALLENGE, DEVICE, mintJwt, NOW, OTHER_CHALLENGE, seedChallenge, type W } from "./attestHarness";
import { allTables, assertion, freshAssertTables, interleaved, keyRow, post, route, seedKey, setCount, testKey, type AssertSpec, type TestKey } from "./assertHarness";

const OTHER_DEVICE = "7a6b5c4d-3e2f-4a1b-9c8d-0123456789ab";
const NEVER_ISSUED = "Q2hhbGxlbmdlLWlzc3VlZC1ieS10aGUtdGVzdC0wMDM";
const REFUSED = { status: 400, json: { error: "invalid_assertion" } };
const S = NOW / 1000;
let KEY: TestKey;
let FRESH: TestKey;
let OUTSIDER: TestKey;

async function granted(claims: Record<string, unknown>) {
  return { status: 200, json: { token: await mintJwt(claims), expires_at: "2026-10-06T13:00:00.000Z" } };
}

const assertBody = async (k: TestKey, spec: AssertSpec = {}, over: Record<string, unknown> = {}) =>
  ({ keyId: k.keyId, assertion: await assertion(k, spec), challenge: CHALLENGE, ...over });

const assert = (body: unknown, e = {}) => route("/attest/assert", e, post(body));

beforeAll(async () => {
  [KEY, FRESH, OUTSIDER] = [await testKey(), await testKey(), await testKey()];
});

beforeEach(async () => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  await freshAssertTables();
  await seedKey(KEY, DEVICE, 5);
  await seedKey(FRESH, OTHER_DEVICE);
  await seedChallenge(CHALLENGE, NOW + 60_000);
  await seedChallenge(OTHER_CHALLENGE, NOW + 60_000);
});

afterEach(() => {
  vi.useRealTimers();
});

const flip = (a: Uint8Array, at: number) => { const b = a.slice(); b[at]! ^= 1; return b; };
const ROWS: [string, () => Promise<unknown>][] = [
  ["replayed counter: 4 below the stored 5", () => assertBody(KEY, { counter: 4 })],
  ["equal counter: 5, the stored 5", () => assertBody(KEY, { counter: 5 })],
  ["counter 0 on a key never asserted (stored 0 from its attestation)", () => assertBody(FRESH, { counter: 0 })],
  ["unknown keyId: a key never attested, signing for itself", () => assertBody(OUTSIDER)],
  ["wrong key: the attested keyId over another key's signature", () => assertBody(KEY, { signer: OUTSIDER })],
  ["wrong key: another attested key's keyId over this key's signature", async () => ({ ...(await assertBody(KEY)), keyId: FRESH.keyId })],
  ["stale challenge: expired at now", async () => { await seedChallenge(NEVER_ISSUED, NOW); return assertBody(KEY, { challenge: NEVER_ISSUED }, { challenge: NEVER_ISSUED }); }],
  ["stale challenge: never issued", () => assertBody(KEY, { challenge: NEVER_ISSUED }, { challenge: NEVER_ISSUED })],
  ["the nonce is over another live challenge than the body's", () => assertBody(KEY, { challenge: OTHER_CHALLENGE })],
  ["rpId mismatch: another App ID", () => assertBody(KEY, { appId: "PLANNED.com.phineasfritsch.other" })],
  ["rpId mismatch: the App ID's hash with one bit flipped, signed as such", () => assertBody(KEY, { before: (a) => flip(a, 31) })],
  ["authenticatorData cut to 36 bytes, signed as such", () => assertBody(KEY, { before: (a) => a.subarray(0, 36) })],
  ["authenticatorData of 38 bytes, signed as such", () => assertBody(KEY, { before: (a) => Uint8Array.from([...a, 0]) })],
  ["the counter changed after signing (7 signed, 6 sent)", () => assertBody(KEY, { counter: 7, after: (a) => flip(a, 36) })],
  ["the signature with one bit flipped", () => assertBody(KEY, { signature: (s) => flip(s, s.length - 1) })],
  ["the signature not DER: 64 raw bytes", () => assertBody(KEY, { signature: () => new Uint8Array(64).fill(1) })],
  ["CBOR: an extra key", () => assertBody(KEY, { object: (p) => new Map<string, W>([["signature", p.signature], ["authenticatorData", p.authenticatorData], ["x", 1]]) })],
  ["CBOR: the signature missing", () => assertBody(KEY, { object: (p) => new Map<string, W>([["authenticatorData", p.authenticatorData]]) })],
  ["CBOR: authenticatorData a text string", () => assertBody(KEY, { object: (p) => new Map<string, W>([["signature", p.signature], ["authenticatorData", "abc"]]) })],
  ["CBOR: the signature a text string", () => assertBody(KEY, { object: (p) => new Map<string, W>([["signature", "abc"], ["authenticatorData", p.authenticatorData]]) })],
  ["not CBOR: an array of the two", () => assertBody(KEY, { object: (p) => [p.signature, p.authenticatorData] })],
  ["body: an extra field (device)", () => assertBody(KEY, {}, { device: DEVICE })],
  ["body: the assertion missing", async () => { const { assertion: _, ...rest } = await assertBody(KEY); return rest; }],
  ["body: keyId of 31 bytes", () => assertBody(KEY, {}, { keyId: b64(new Uint8Array(31)) })],
  ["body: a challenge of 42 characters", () => assertBody(KEY, {}, { challenge: CHALLENGE.slice(1) })],
  ["body: appAccountToken not a UUID", () => assertBody(KEY, {}, { appAccountToken: "not-a-uuid" })],
  ["body: the assertion not base64", () => assertBody(KEY, {}, { assertion: "!!!!" })],
  ["body: not JSON", async () => "{"],
];

describe("every assertion defect is 400 invalid_assertion with all four tables unchanged (R3)", () => {
  for (const [name, body] of ROWS) {
    it(name, async () => {
      const b = await body();
      const before = await allTables();
      expect({ answer: await assert(b), tables: await allTables() }).toEqual({ answer: REFUSED, tables: before });
    });
  }

  it("the control: the untouched assertion of the table renews (counter 6 over 5)", async () => {
    expect(await assert(await assertBody(KEY))).toEqual(await granted({ iss: "scenic-api", sub: DEVICE, iat: S, exp: S + 3600 }));
  });
});

const live = (c: string) => ({ challenge: c, expires_at: NOW + 60_000 });
const bothKeys = () => [keyRow(KEY, DEVICE), keyRow(FRESH, OTHER_DEVICE)].sort((a, b) => a.key_id.localeCompare(b.key_id));

describe("a verified assertion stores its counter, consumes the challenge and answers the stored device's session (R2, R4)", () => {
  it("counter stored + 1: sign_count 6, the challenge consumed, sub the stored device, no act", async () => {
    expect({ answer: await assert(await assertBody(KEY)), tables: await allTables() }).toEqual({
      answer: await granted({ iss: "scenic-api", sub: DEVICE, iat: S, exp: S + 3600 }),
      tables: { challenges: [live(OTHER_CHALLENGE)], keys: bothKeys(), counts: [{ key_id: KEY.keyId, sign_count: 6 }], rates: [] },
    });
  });

  for (const [counter, stored] of [[1, undefined], [2 ** 31, 5], [2 ** 32 - 1, 2 ** 32 - 2], [2 ** 31 + 1, 2 ** 31]] as const) {
    it(`counter ${counter} over stored ${stored ?? "0 (no row)"} is stored whole; sub is that key's device`, async () => {
      if (stored !== undefined) await setCount(FRESH.keyId, stored);
      const answer = await assert(await assertBody(FRESH, { counter }));
      expect({ answer, counts: (await allTables()).counts }).toEqual({
        answer: await granted({ iss: "scenic-api", sub: OTHER_DEVICE, iat: S, exp: S + 3600 }),
        counts: [{ key_id: FRESH.keyId, sign_count: counter }, { key_id: KEY.keyId, sign_count: 5 }].sort((a, b) => a.key_id.localeCompare(b.key_id)),
      });
    });
  }

  it("counter 2^31 below a stored 2^31 + 1 is refused (the comparison is unsigned and whole)", async () => {
    await setCount(KEY.keyId, 2 ** 31 + 1);
    const before = await allTables();
    expect({ answer: await assert(await assertBody(KEY, { counter: 2 ** 31 })), tables: await allTables() }).toEqual({ answer: REFUSED, tables: before });
  });

  it("an upper-case appAccountToken is lowercased into act", async () => {
    expect(await assert(await assertBody(KEY, {}, { appAccountToken: ACCOUNT.toUpperCase() })))
      .toEqual(await granted({ iss: "scenic-api", sub: DEVICE, act: ACCOUNT, iat: S, exp: S + 3600 }));
  });

  it("a replay of an accepted assertion is refused and changes nothing (the challenge is consumed)", async () => {
    const body = await assertBody(KEY);
    expect((await assert(body)).status).toBe(200);
    const after = await allTables();
    expect({ answer: await assert(body), tables: await allTables() }).toEqual({ answer: REFUSED, tables: after });
  });

  it("a challenge expiring 1 ms after now is live (bound)", async () => {
    await seedChallenge(NEVER_ISSUED, NOW + 1);
    expect((await assert(await assertBody(KEY, { challenge: NEVER_ISSUED }, { challenge: NEVER_ISSUED }))).status).toBe(200);
  });

  it("without SESSION_JWT_SECRET: 503 attest_unavailable, nothing written; GET is 405", async () => {
    const before = await allTables();
    expect([await route("/attest/assert", { SESSION_JWT_SECRET: undefined }, post(await assertBody(KEY))), await route("/attest/assert", {}, { method: "GET" }), await allTables()])
      .toEqual([{ status: 503, json: { error: "attest_unavailable" } }, { status: 405, json: { error: "POST only" } }, before]);
  });
});

describe("the commit batch is the authority: rows changed after the key read commit nothing (R4)", () => {
  const between = async (fn: () => Promise<unknown>, body: unknown) => assert(body, { DB: interleaved(KEY_FOR_ASSERTION, fn) });

  it("a rival commits counter 6 after the read: this counter 6 is refused, the rival's row stands, the challenge stays live", async () => {
    const body = await assertBody(KEY);
    expect({ answer: await between(() => setCount(KEY.keyId, 6), body), tables: await allTables() }).toEqual({
      answer: REFUSED, tables: { challenges: [live(CHALLENGE), live(OTHER_CHALLENGE)], keys: bothKeys(), counts: [{ key_id: KEY.keyId, sign_count: 6 }], rates: [] },
    });
  });

  it("the challenge is consumed after the read: refused, the counter unchanged", async () => {
    const body = await assertBody(KEY);
    const gone = () => env.DB.prepare("DELETE FROM attest_challenges WHERE challenge = ?1").bind(CHALLENGE).run();
    expect({ answer: await between(gone, body), tables: await allTables() }).toEqual({
      answer: REFUSED, tables: { challenges: [live(OTHER_CHALLENGE)], keys: bothKeys(), counts: [{ key_id: KEY.keyId, sign_count: 5 }], rates: [] },
    });
  });

  for (const [at, ok] of [[NOW, false], [NOW + 1, true]] as const) {
    it(`the batch sees the challenge expiring at now${at === NOW ? "" : " + 1 ms"}: ${ok ? "stored and consumed" : "refused, nothing written"} (bound)`, async () => {
      const body = await assertBody(KEY);
      const expire = () => env.DB.prepare("UPDATE attest_challenges SET expires_at = ?1 WHERE challenge = ?2").bind(at, CHALLENGE).run();
      expect({ answer: (await between(expire, body)).status, tables: await allTables() }).toEqual({
        answer: ok ? 200 : 400,
        tables: { challenges: ok ? [live(OTHER_CHALLENGE)] : [{ challenge: CHALLENGE, expires_at: NOW }, live(OTHER_CHALLENGE)], keys: bothKeys(), counts: [{ key_id: KEY.keyId, sign_count: ok ? 6 : 5 }], rates: [] },
      });
    });
  }

  it("the key is gone after the read: refused, no counter row", async () => {
    const body = await assertBody(FRESH, { counter: 1 });
    const gone = () => env.DB.prepare("DELETE FROM attested_keys WHERE key_id = ?1").bind(FRESH.keyId).run();
    expect({ answer: await between(gone, body), tables: await allTables() }).toEqual({
      answer: REFUSED, tables: { challenges: [live(CHALLENGE), live(OTHER_CHALLENGE)], keys: [keyRow(KEY, DEVICE)], counts: [{ key_id: KEY.keyId, sign_count: 5 }], rates: [] },
    });
  });
});
