/**
 * Shared App Attest test plumbing (T-0278): a CBOR writer, a test-generated App Attest chain and attestation object
 * (the root is self-made, so production's pinned Apple root never trusts it; tests hand its DER and fingerprint to
 * the verifier in place of the pin - the ONLY replacement in the deps), the shipped migrations (0003, and T-0280's 0004), both tables read
 * back whole, and an HS256 signer of the test's own for the session JWT oracle. Not a test file.
 */
import { env } from "cloudflare:test";
import attestSql from "../migrations/0003_app_attest.sql?raw";
import assertSql from "../migrations/0004_app_attest_assert.sql?raw";
import { attestDepsFromEnv, handleAttest, type AttestDeps } from "../src/attest";
import type { Env } from "../src/index";
import { b64, b64url, certificate, party, seq, tlv, type CertSpec } from "./appleChain";

export const NOW = Date.UTC(2026, 9, 6, 12, 0, 0);
export const SECRET = "test-session-secret-0123456789abcdef";
export const DEVICE = "0f8b6d5e-1a2b-4c3d-8e9f-0123456789ab";
export const ACCOUNT = "6f1c2d3e-4a5b-4c6d-8e7f-0123456789ab";
export const CHALLENGE = "Q2hhbGxlbmdlLWlzc3VlZC1ieS10aGUtdGVzdC0wMDE";
export const OTHER_CHALLENGE = "Q2hhbGxlbmdlLWlzc3VlZC1ieS10aGUtdGVzdC0wMDI";
export const NONCE_OID = "1.2.840.113635.100.8.2";
/** Written out, never imported: SHA256 of this is what the verifier must find as rpIdHash. */
export const APP_ID = "PLANNED.com.phineasfritsch.scenicdrive";
/** base64url of {"alg":"HS256","typ":"JWT"}, typed out. */
export const HS256_HEADER = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9";
export const AAGUID_PRODUCTION = new Uint8Array([...new TextEncoder().encode("appattest"), 0, 0, 0, 0, 0, 0, 0]);
export const AAGUID_DEVELOP = new TextEncoder().encode("appattestdevelop");
const YEAR = 365 * 24 * 3600 * 1000;

export type W = number | string | Uint8Array | W[] | Map<string, W> | { raw: Uint8Array } | { entries: [string, W][] };

function head(major: number, n: number): number[] {
  if (n < 24) return [(major << 5) | n];
  if (n < 256) return [(major << 5) | 24, n];
  if (n < 65536) return [(major << 5) | 25, n >> 8, n & 0xff];
  return [(major << 5) | 26, (n >>> 24) & 0xff, (n >> 16) & 0xff, (n >> 8) & 0xff, n & 0xff];
}

export const cat = (...parts: (Uint8Array | number[])[]) => {
  const out = new Uint8Array(parts.reduce((n, p) => n + p.length, 0));
  let at = 0;
  for (const p of parts) { out.set(p, at); at += p.length; }
  return out;
};

/** A CBOR writer of the test's own - definite lengths, keys in the order given. */
export function cbor(v: W): Uint8Array {
  if (typeof v === "number") return new Uint8Array(head(0, v));
  if (typeof v === "string") { const t = new TextEncoder().encode(v); return cat(head(3, t.length), t); }
  if (v instanceof Uint8Array) return cat(head(2, v.length), v);
  if (Array.isArray(v)) return cat(head(4, v.length), ...v.map(cbor));
  if (v instanceof Map) return cbor({ entries: [...v.entries()] });
  if ("raw" in v) return v.raw;
  return cat(head(5, v.entries.length), ...v.entries.flatMap(([k, x]) => [cbor(k), cbor(x)]));
}

const utf8 = (t: string) => new TextEncoder().encode(t);
export const sha = async (b: Uint8Array) => new Uint8Array(await crypto.subtle.digest("SHA-256", b));
const hex = (b: Uint8Array) => Array.from(b, (x) => (x < 16 ? "0" : "") + x.toString(16)).join("");

/** SEQUENCE { [1] EXPLICIT OCTET STRING nonce } - the credCert nonce extension's value. */
export const nonceExtension = (nonce: Uint8Array) => seq(tlv(0xa1, tlv(0x04, nonce)));

export interface AttestSpec {
  now?: number;
  /** The challenge hashed into the nonce (default CHALLENGE). */
  challenge?: string;
  appId?: string;
  counter?: number[];
  aaguid?: Uint8Array;
  credIdLength?: number;
  credId?: (keyId: Uint8Array) => Uint8Array;
  /** Rewrites authData BEFORE the nonce is computed over it. */
  authData?: (a: Uint8Array) => Uint8Array;
  /** The whole nonce extension value; null omits the extension. */
  nonceExt?: (nonce: Uint8Array) => Uint8Array | null;
  repeatNonce?: boolean;
  leaf?: Partial<CertSpec>;
  intermediate?: Partial<CertSpec>;
  root?: Partial<CertSpec>;
  leafCurve?: "P-256" | "P-384";
  outsiderSignsLeaf?: boolean;
  outsiderSignsIntermediate?: boolean;
  object?: (p: { authData: Uint8Array; x5c: Uint8Array[]; rootDer: Uint8Array }) => W;
  keyId?: (keyId: Uint8Array) => Uint8Array;
}

export interface Attested { keyId: string; attestation: string; rootDer: Uint8Array; rootSha256: string; publicKeyHex: string }

export async function attestation(spec: AttestSpec = {}): Promise<Attested> {
  const now = spec.now ?? NOW;
  const root = await party("Test App Attestation Root CA", "P-384");
  const inter = await party("Test App Attestation CA 1", "P-384");
  const leaf = await party("test-app-attest-key", spec.leafCurve ?? "P-256");
  const keyId = await sha(leaf.spki.slice(leaf.spki.length - 65));
  const credId = spec.credId ? spec.credId(keyId) : keyId;
  const len = spec.credIdLength ?? credId.length;
  let authData = cat(await sha(utf8(spec.appId ?? APP_ID)), [0x40], spec.counter ?? [0, 0, 0, 0], spec.aaguid ?? AAGUID_PRODUCTION,
    [len >> 8, len & 0xff], credId, cbor(new Map<string, W>([["1", 2], ["3", 7]])));
  if (spec.authData) authData = spec.authData(authData);
  const nonce = await sha(cat(authData, await sha(utf8(spec.challenge ?? CHALLENGE))));
  const ext = spec.nonceExt ? spec.nonceExt(nonce) : nonceExtension(nonce);
  const span = { notBefore: now - YEAR, notAfter: now + YEAR };
  const rootDer = await certificate(root, root, { ...span, extensions: [], ...spec.root });
  const interSigner = spec.outsiderSignsIntermediate ? { ...(await party("outsider", "P-384")), name: root.name } : root;
  const interDer = await certificate(inter, interSigner, { ...span, extensions: [], ...spec.intermediate });
  const leafSigner = spec.outsiderSignsLeaf ? { ...(await party("outsider", "P-384")), name: inter.name } : inter;
  const exts = ext === null ? { extensions: [] } : { extensions: spec.repeatNonce ? [NONCE_OID, NONCE_OID] : [NONCE_OID], values: { [NONCE_OID]: ext } };
  const leafDer = await certificate(leaf, leafSigner, { ...span, ...exts, ...spec.leaf });
  const x5c = [leafDer, interDer];
  const object = spec.object ? spec.object({ authData, x5c, rootDer })
    : new Map<string, W>([["fmt", "apple-appattest"], ["attStmt", new Map<string, W>([["x5c", x5c], ["receipt", utf8("receipt")]])], ["authData", authData]]);
  return { keyId: b64(spec.keyId ? spec.keyId(keyId) : keyId), attestation: b64(cbor(object)), rootDer, rootSha256: hex(await sha(rootDer)),
    publicKeyHex: hex(leaf.spki) };
}

export async function freshAttestTables(): Promise<void> {
  for (const sql of [attestSql, assertSql]) {
    for (const statement of sql.split(";").map((s) => s.trim()).filter(Boolean)) await env.DB.prepare(statement).run();
  }
  for (const table of ["attest_challenges", "attested_keys", "attest_sign_counts", "attest_challenge_counts"]) await env.DB.prepare(`DELETE FROM ${table}`).run();
}

export async function seedChallenge(challenge: string, expiresAt: number): Promise<void> {
  await env.DB.prepare("INSERT INTO attest_challenges (challenge, expires_at) VALUES (?1, ?2)").bind(challenge, expiresAt).run();
}

export async function tables() {
  return {
    challenges: (await env.DB.prepare("SELECT * FROM attest_challenges ORDER BY challenge").all()).results,
    keys: (await env.DB.prepare("SELECT * FROM attested_keys ORDER BY key_id").all()).results,
  };
}

/** Production deps for env plus the session secret, with the test chain's root in place of the pinned Apple root. */
export function testDeps(a: Pick<Attested, "rootDer" | "rootSha256">, extra: Partial<Env> = {}): AttestDeps {
  return { ...attestDepsFromEnv({ ...(env as unknown as Env), SESSION_JWT_SECRET: SECRET, ...extra }), rootDer: a.rootDer, rootSha256: a.rootSha256 };
}

export const bodyOf = (a: Attested, over: Record<string, unknown> = {}) =>
  ({ keyId: a.keyId, attestation: a.attestation, challenge: CHALLENGE, device: DEVICE, ...over });

export async function postAttest(body: unknown, deps: AttestDeps) {
  const req = new Request("https://scenic-api.test/attest", { method: "POST", body: typeof body === "string" ? body : JSON.stringify(body) });
  const response = await handleAttest(req, deps);
  return { status: response.status, json: (await response.json()) as unknown };
}

/** An HS256 JWT of the test's own: `header` and `claims` serialised as given, signed with `secret`. */
export async function mintJwt(claims: Record<string, unknown> | string, secret = SECRET, header = HS256_HEADER): Promise<string> {
  const body = b64url(typeof claims === "string" ? claims : JSON.stringify(claims));
  const key = await crypto.subtle.importKey("raw", utf8(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return `${header}.${body}.${b64url(new Uint8Array(await crypto.subtle.sign("HMAC", key, utf8(`${header}.${body}`))))}`;
}
