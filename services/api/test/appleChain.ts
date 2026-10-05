/**
 * A test-generated Apple-shaped chain (T-0267 R2): a DER writer, certificates signed through WebCrypto, and ES256
 * JWSs carrying [leaf, intermediate, root] in x5c - the root is self-made, so production's pinned Apple root never
 * trusts it; tests hand its fingerprint to the verifier in place of the pin. Not a test file.
 */
import { OID_APPLE_STORE_LEAF, OID_APPLE_WWDR_INTERMEDIATE } from "../src/appleJws";

type Curve = "P-256" | "P-384";
const bytes = (...parts: (Uint8Array | number[])[]) => {
  const out = new Uint8Array(parts.reduce((n, p) => n + p.length, 0));
  let at = 0;
  for (const p of parts) { out.set(p, at); at += p.length; }
  return out;
};

export function tlv(tag: number, ...content: Uint8Array[]): Uint8Array {
  const body = bytes(...content);
  const n = body.length;
  const len = n < 128 ? [n] : n < 256 ? [0x81, n] : [0x82, n >> 8, n & 0xff];
  return bytes([tag], len, body);
}
const seq = (...c: Uint8Array[]) => tlv(0x30, ...c);
function int(value: Uint8Array): Uint8Array {
  let v = value;
  while (v.length > 1 && v[0] === 0 && !(v[1]! & 0x80)) v = v.subarray(1);
  return tlv(0x02, v[0]! & 0x80 ? bytes([0], v) : v);
}
export function oid(text: string): Uint8Array {
  const [a, b, ...rest] = text.split(".").map(Number);
  const out = [a! * 40 + b!];
  for (const n of rest) {
    const groups = [n & 0x7f];
    for (let x = Math.floor(n / 128); x > 0; x = Math.floor(x / 128)) groups.unshift((x & 0x7f) | 0x80);
    out.push(...groups);
  }
  return tlv(0x06, new Uint8Array(out));
}
function time(ms: number): Uint8Array {
  const iso = new Date(ms).toISOString().replace(/[-:T]/g, "").slice(0, 14) + "Z";
  return new Date(ms).getUTCFullYear() < 2050 ? tlv(0x17, new TextEncoder().encode(iso.slice(2))) : tlv(0x18, new TextEncoder().encode(iso));
}
const name = (cn: string) => seq(tlv(0x31, seq(oid("2.5.4.3"), tlv(0x0c, new TextEncoder().encode(cn)))));

export function b64(data: Uint8Array): string {
  return btoa(String.fromCharCode(...data));
}
export function b64url(data: Uint8Array | string): string {
  const raw = typeof data === "string" ? new TextEncoder().encode(data) : data;
  return b64(raw).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export interface Party { name: string; curve: Curve; keys: CryptoKeyPair; spki: Uint8Array }

export async function party(cn: string, curve: Curve): Promise<Party> {
  const keys = (await crypto.subtle.generateKey({ name: "ECDSA", namedCurve: curve }, true, ["sign", "verify"])) as CryptoKeyPair;
  return { name: cn, curve, keys, spki: new Uint8Array((await crypto.subtle.exportKey("spki", keys.publicKey)) as ArrayBuffer) };
}

export interface CertSpec { notBefore: number; notAfter: number; extensions: string[]; issuerName?: string }

export async function certificate(subject: Party, issuer: Party, spec: CertSpec): Promise<Uint8Array> {
  const hash = issuer.curve === "P-384" ? "SHA-384" : "SHA-256";
  const alg = seq(oid(hash === "SHA-384" ? "1.2.840.10045.4.3.3" : "1.2.840.10045.4.3.2"));
  const exts = spec.extensions.map((x) => seq(oid(x), tlv(0x04, new Uint8Array([0x05, 0x00]))));
  const tbs = seq(tlv(0xa0, int(new Uint8Array([2]))), int(crypto.getRandomValues(new Uint8Array(8))), alg,
    name(spec.issuerName ?? issuer.name), seq(time(spec.notBefore), time(spec.notAfter)), name(subject.name), subject.spki,
    tlv(0xa3, seq(...exts)));
  const raw = new Uint8Array(await crypto.subtle.sign({ name: "ECDSA", hash }, issuer.keys.privateKey, tbs));
  const half = raw.length / 2;
  const sig = seq(int(raw.subarray(0, half)), int(raw.subarray(half)));
  return seq(tbs, alg, tlv(0x03, new Uint8Array([0]), sig));
}

/** The test's own hex of a SHA-256 - never the verifier's sha256Hex, so a defect there cannot cancel itself out. */
async function fingerprint(der: Uint8Array): Promise<string> {
  const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", der));
  return Array.from(digest, (b) => (b < 16 ? "0" : "") + b.toString(16)).join("");
}

export interface Chain { x5c: string[]; leaf: Party; rootSha256: string }
export interface ChainSpec {
  now: number;
  leaf?: Partial<CertSpec>;
  intermediate?: Partial<CertSpec>;
  root?: Partial<CertSpec>;
  leafCurve?: Curve;
  /** Sign the leaf with this party instead of the intermediate (same issuer name). */
  leafSigner?: Party;
  /** Sign the intermediate with this party instead of the root (same issuer name). */
  intermediateSigner?: Party;
}

const YEAR = 365 * 24 * 3600 * 1000;

export async function appleChain(spec: ChainSpec): Promise<Chain> {
  const root = await party("Test Root CA - G3", "P-384");
  const intermediate = await party("Test WWDR - G6", "P-384");
  const leaf = await party("Test Mac App Store and iTunes Store Receipt Signing", spec.leafCurve ?? "P-256");
  const span = { notBefore: spec.now - YEAR, notAfter: spec.now + YEAR };
  const rootDer = await certificate(root, root, { ...span, extensions: [], ...spec.root });
  const interSigner = spec.intermediateSigner ? { ...spec.intermediateSigner, name: root.name } : root;
  const interDer = await certificate(intermediate, interSigner, { ...span, extensions: [OID_APPLE_WWDR_INTERMEDIATE], ...spec.intermediate });
  const signer = spec.leafSigner ? { ...spec.leafSigner, name: intermediate.name } : intermediate;
  const leafDer = await certificate(leaf, signer, { ...span, extensions: [OID_APPLE_STORE_LEAF], ...spec.leaf });
  return { x5c: [leafDer, interDer, rootDer].map(b64), leaf, rootSha256: await fingerprint(rootDer) };
}

/** An ES256 JWS over `payload` with `chain`'s x5c; `header` overrides or (as undefined) removes header fields. */
export async function signJws(payload: unknown, chain: Chain, header: Record<string, unknown> = {}, key?: CryptoKey): Promise<string> {
  const h = b64url(JSON.stringify({ alg: "ES256", x5c: chain.x5c, ...header }));
  const p = b64url(typeof payload === "string" ? payload : JSON.stringify(payload));
  const sig = await crypto.subtle.sign({ name: "ECDSA", hash: "SHA-256" }, key ?? chain.leaf.keys.privateKey,
    new TextEncoder().encode(`${h}.${p}`));
  return `${h}.${p}.${b64url(new Uint8Array(sig))}`;
}

export interface NotificationSpec {
  type: string;
  subtype?: string;
  signedDate: number;
  environment?: string;
  bundleId?: string;
  tx?: Record<string, unknown> | null;
  renewal?: Record<string, unknown> | null;
}

/** A whole signedPayload: the outer notification and its nested signed transaction / renewal info. */
export async function notification(chain: Chain, spec: NotificationSpec): Promise<string> {
  const data: Record<string, unknown> = { environment: spec.environment ?? "Production", bundleId: spec.bundleId ?? "com.phineasfritsch.scenicdrive" };
  if (spec.tx !== null) data.signedTransactionInfo = await signJws(spec.tx ?? {}, chain);
  if (spec.renewal) data.signedRenewalInfo = await signJws(spec.renewal, chain);
  return signJws({ notificationType: spec.type, ...(spec.subtype ? { subtype: spec.subtype } : {}), notificationUUID: "u",
    data, version: "2.0", signedDate: spec.signedDate }, chain);
}
