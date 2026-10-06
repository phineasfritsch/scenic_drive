/**
 * Shared plumbing for T-0280 (assertions and the /attest/challenge rate limit): all four tables read back whole, a
 * test P-256 key seeded as an attested key, an App Attest assertion of the test's own (CBOR {signature,
 * authenticatorData}, a DER ECDSA signature over SHA256(authData || SHA256(challenge))), a D1 whose named read runs a
 * hook after it answers, and a caller of the shipped ROUTES. Not a test file.
 */
import { env } from "cloudflare:test";
import { ROUTES, type Env } from "../src/index";
import { b64 } from "./appleChain";
import { APP_ID, cat, cbor, CHALLENGE, freshAttestTables, NOW, SECRET, sha, type W } from "./attestHarness";

export const HOUR = 3_600_000;
export const DAY = 86_400_000;
export const HOUR_SLOT = Math.floor(NOW / HOUR) * HOUR;
export const DAY_SLOT = Math.floor(NOW / DAY) * DAY;

const utf8 = (t: string) => new TextEncoder().encode(t);
const hex = (b: Uint8Array) => Array.from(b, (x) => (x < 16 ? "0" : "") + x.toString(16)).join("");

/** Migrations 0003 and 0004 applied, all four tables empty (attestHarness's freshAttestTables). */
export const freshAssertTables = freshAttestTables;

export async function allTables() {
  const all = async (sql: string) => (await env.DB.prepare(sql).all()).results;
  return {
    challenges: await all("SELECT * FROM attest_challenges ORDER BY challenge"),
    keys: await all("SELECT * FROM attested_keys ORDER BY key_id"),
    counts: await all("SELECT * FROM attest_sign_counts ORDER BY key_id"),
    rates: await all("SELECT * FROM attest_challenge_counts ORDER BY bucket, slot"),
  };
}

export interface TestKey { keyId: string; pair: CryptoKeyPair; spkiHex: string }

/** A fresh P-256 key; keyId is SHA256 of its uncompressed point, as App Attest names it. */
export async function testKey(): Promise<TestKey> {
  const pair = (await crypto.subtle.generateKey({ name: "ECDSA", namedCurve: "P-256" }, true, ["sign", "verify"])) as CryptoKeyPair;
  const spki = new Uint8Array((await crypto.subtle.exportKey("spki", pair.publicKey)) as ArrayBuffer);
  return { keyId: b64(await sha(spki.slice(spki.length - 65))), pair, spkiHex: hex(spki) };
}

export const keyRow = (k: TestKey, device: string) =>
  ({ key_id: k.keyId, device_id: device, public_key: k.spkiHex, environment: "production", attested_at: NOW - 1000 });

export async function seedKey(k: TestKey, device: string, signCount?: number): Promise<void> {
  const r = keyRow(k, device);
  await env.DB.prepare("INSERT INTO attested_keys (key_id, device_id, public_key, environment, attested_at) VALUES (?1, ?2, ?3, ?4, ?5)")
    .bind(r.key_id, r.device_id, r.public_key, r.environment, r.attested_at).run();
  if (signCount !== undefined) await setCount(k.keyId, signCount);
}

export async function setCount(keyId: string, signCount: number): Promise<void> {
  await env.DB.prepare("INSERT INTO attest_sign_counts (key_id, sign_count) VALUES (?1, ?2) ON CONFLICT (key_id) DO UPDATE SET sign_count = ?2")
    .bind(keyId, signCount).run();
}

export async function seedRate(bucket: string, slot: number, issued: number): Promise<void> {
  await env.DB.prepare("INSERT INTO attest_challenge_counts (bucket, slot, issued) VALUES (?1, ?2, ?3)").bind(bucket, slot, issued).run();
}

/** A DER INTEGER of the unsigned big-endian `v`. */
function derInt(v: Uint8Array): Uint8Array {
  let at = 0;
  while (at < v.length - 1 && v[at] === 0) at++;
  const body = v[at]! & 0x80 ? cat([0], v.subarray(at)) : v.subarray(at);
  return cat([0x02, body.length], body);
}

export interface AssertSpec {
  counter?: number;
  appId?: string;
  /** The challenge hashed into the nonce (default CHALLENGE). */
  challenge?: string;
  /** The key that signs (default the asserted key). */
  signer?: TestKey;
  /** Rewrites authData AFTER the signature is made over it. */
  after?: (a: Uint8Array) => Uint8Array;
  /** Rewrites authData BEFORE it is signed. */
  before?: (a: Uint8Array) => Uint8Array;
  signature?: (der: Uint8Array) => Uint8Array;
  object?: (p: { authenticatorData: Uint8Array; signature: Uint8Array }) => W;
}

export async function assertion(k: TestKey, spec: AssertSpec = {}): Promise<string> {
  const c = spec.counter ?? 6;
  let authData = cat(await sha(utf8(spec.appId ?? APP_ID)), [0x00], [(c >>> 24) & 0xff, (c >>> 16) & 0xff, (c >>> 8) & 0xff, c & 0xff]);
  if (spec.before) authData = spec.before(authData);
  const nonce = await sha(cat(authData, await sha(utf8(spec.challenge ?? CHALLENGE))));
  const raw = new Uint8Array(await crypto.subtle.sign({ name: "ECDSA", hash: "SHA-256" }, (spec.signer ?? k).pair.privateKey, nonce));
  const rs = cat(derInt(raw.subarray(0, 32)), derInt(raw.subarray(32)));
  let signature = cat([0x30, rs.length], rs);
  if (spec.signature) signature = spec.signature(signature);
  const authenticatorData = spec.after ? spec.after(authData) : authData;
  const object = spec.object ? spec.object({ authenticatorData, signature })
    : new Map<string, W>([["signature", signature], ["authenticatorData", authenticatorData]]);
  return b64(cbor(object));
}

/** env.DB, except that the read `sql` runs `between` after it answers - so a test changes the rows between the read and the batch. */
export function interleaved(sql: string, between: () => Promise<unknown>): D1Database {
  const db = env.DB;
  return {
    prepare: (s: string) => (s !== sql ? db.prepare(s) : {
      bind: (...args: unknown[]) => ({ first: async () => { const row = await db.prepare(s).bind(...args).first(); await between(); return row; } }),
    }),
    batch: (statements: D1PreparedStatement[]) => db.batch(statements),
  } as unknown as D1Database;
}

export async function route(path: string, e: Partial<Env> = {}, init: RequestInit = { method: "POST" }) {
  const req = new Request(`https://scenic-api.test${path}`, init);
  const response = await ROUTES[path]!(req, { ...(env as unknown as Env), SESSION_JWT_SECRET: SECRET, ...e }, new URL(req.url));
  return { status: response.status, json: (await response.json()) as Record<string, unknown> };
}

export const post = (body: unknown, headers: Record<string, string> = {}): RequestInit =>
  ({ method: "POST", headers, body: typeof body === "string" ? body : JSON.stringify(body) });
