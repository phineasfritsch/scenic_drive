/**
 * T-0278 R1-R4 through the SHIPPED handleAttest, production deps whose ONLY replacement is the root (a test-made
 * root DER and its fingerprint): every defect of the body, the CBOR object, the chain, the nonce, the keyId and
 * authData is 400 invalid_attestation with BOTH tables unchanged - the challenge not consumed, no key written. The
 * answer and the tables are compared WHOLE.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { AttestDeps } from "../src/attest";
import type { Env } from "../src/index";
import { b64, seq, tlv } from "./appleChain";
import {
  AAGUID_DEVELOP, AAGUID_PRODUCTION, ACCOUNT, attestation, bodyOf, cat, cbor, CHALLENGE, DEVICE, freshAttestTables, nonceExtension,
  NOW, OTHER_CHALLENGE, postAttest, seedChallenge, tables, testDeps, type AttestSpec, type Attested, type W,
} from "./attestHarness";

const REFUSED = { status: 400, json: { error: "invalid_attestation" } };
const SEEDED = { challenges: [{ challenge: CHALLENGE, expires_at: NOW + 60_000 }], keys: [] };

const flip = (b: Uint8Array, i = 0) => { const c = b.slice(); c[i]! ^= 1; return c; };
const bytes = (text: string) => Uint8Array.from(atob(text), (c) => c.charCodeAt(0));
const without = (a: Attested, key: string) => Object.fromEntries(Object.entries(bodyOf(a)).filter(([k]) => k !== key));

type Parts = { authData: Uint8Array; x5c: Uint8Array[]; rootDer: Uint8Array };
/** The well-formed object's entries with `edit` applied: a key set to undefined is dropped. */
function object(edit: (p: Parts) => Record<string, W | undefined>, stmt: (p: Parts) => Record<string, W | undefined> = () => ({})) {
  return (p: Parts): W => {
    const entries = (base: Record<string, W>, over: Record<string, W | undefined>) =>
      Object.entries({ ...base, ...over }).filter((e): e is [string, W] => e[1] !== undefined);
    const attStmt: W = { entries: entries({ x5c: p.x5c, receipt: new TextEncoder().encode("receipt") }, stmt(p)) };
    return { entries: entries({ fmt: "apple-appattest", attStmt, authData: p.authData }, edit(p)) };
  };
}

interface Row { name: string; spec?: AttestSpec; body?: (a: Attested) => unknown; deps?: (a: Attested) => Partial<AttestDeps>; env?: Partial<Env> }
const body = (over: Record<string, unknown>) => (a: Attested) => bodyOf(a, over);
const ext = (f: (n: Uint8Array) => Uint8Array | null): AttestSpec => ({ nonceExt: f });

const ROWS: Row[] = [
  { name: "a body that is not JSON", body: () => "{not json" },
  { name: "a body that is a JSON array", body: (a) => [bodyOf(a)] },
  { name: "keyId absent", body: (a) => without(a, "keyId") },
  { name: "attestation absent", body: (a) => without(a, "attestation") },
  { name: "challenge absent", body: (a) => without(a, "challenge") },
  { name: "device absent", body: (a) => without(a, "device") },
  { name: "an unknown body key", body: body({ extra: 1 }) },
  { name: "keyId not base64", body: (a) => bodyOf(a, { keyId: `-${a.keyId.slice(1)}` }) },
  { name: "keyId of 31 bytes", body: body({ keyId: b64(new Uint8Array(31)) }) },
  { name: "keyId of 33 bytes", body: body({ keyId: b64(new Uint8Array(33)) }) },
  { name: "keyId a number", body: body({ keyId: 1 }) },
  { name: "attestation empty", body: body({ attestation: "" }) },
  { name: "attestation not base64", body: (a) => bodyOf(a, { attestation: `${a.attestation}!` }) },
  { name: "challenge unknown to the store", spec: { challenge: OTHER_CHALLENGE }, body: body({ challenge: OTHER_CHALLENGE }) },
  { name: "challenge of 42 characters", body: body({ challenge: CHALLENGE.slice(1) }) },
  { name: "challenge of 44 characters", body: body({ challenge: `${CHALLENGE}A` }) },
  { name: "device malformed", body: body({ device: DEVICE.slice(1) }) },
  { name: "device a number", body: body({ device: 7 }) },
  { name: "appAccountToken malformed", body: body({ appAccountToken: ACCOUNT.slice(1) }) },
  { name: "appAccountToken null", body: body({ appAccountToken: null }) },
  { name: "attestation not CBOR", body: body({ attestation: b64(new Uint8Array([0xff])) }) },
  { name: "a byte after the CBOR object", body: (a) => bodyOf(a, { attestation: b64(cat(bytes(a.attestation), [0])) }) },
  { name: "the object is an array", spec: { object: (p) => [p.authData] } },
  { name: "fmt packed", spec: { object: object(() => ({ fmt: "packed" })) } },
  { name: "fmt absent", spec: { object: object(() => ({ fmt: undefined })) } },
  { name: "a fourth top-level key", spec: { object: object(() => ({ extra: 1 })) } },
  { name: "attStmt is bytes", spec: { object: object(() => ({ attStmt: new Uint8Array([1]) })) } },
  { name: "x5c of one certificate", spec: { object: object(() => ({}), (p) => ({ x5c: [p.x5c[0]!] })) } },
  { name: "x5c of three certificates", spec: { object: object(() => ({}), (p) => ({ x5c: [...p.x5c, p.rootDer] })) } },
  { name: "x5c reversed", spec: { object: object(() => ({}), (p) => ({ x5c: [p.x5c[1]!, p.x5c[0]!] })) } },
  { name: "x5c with a text element", spec: { object: object(() => ({}), (p) => ({ x5c: ["cert", p.x5c[1]!] })) } },
  { name: "x5c with a certificate that is not DER", spec: { object: object(() => ({}), (p) => ({ x5c: [new Uint8Array([1, 2, 3]), p.x5c[1]!] })) } },
  { name: "receipt absent", spec: { object: object(() => ({}), () => ({ receipt: undefined })) } },
  { name: "receipt is text", spec: { object: object(() => ({}), () => ({ receipt: "receipt" })) } },
  { name: "a third attStmt key", spec: { object: object(() => ({}), () => ({ alg: 7 })) } },
  { name: "authData is text", spec: { object: object(() => ({ authData: "authData" })) } },
  { name: "an indefinite-length top map", spec: { object: (p) => ({ raw: cat([0xbf], cbor3(p).slice(1), [0xff]) }) } },
  { name: "a duplicate top-level key (a garbage authData before the real one)", spec: { object: (p) => ({ entries: [["fmt", "apple-appattest"],
    ["attStmt", { entries: [["x5c", p.x5c], ["receipt", new TextEncoder().encode("receipt")]] }], ["authData", new Uint8Array(1)], ["authData", p.authData]] }) } },
  { name: "a negative integer as the receipt", spec: { object: object(() => ({}), () => ({ receipt: { raw: new Uint8Array([0x20]) } })) } },
  { name: "a tagged authData", spec: { object: object((p) => ({ authData: { raw: cat([0xc2, 0x58, p.authData.length], p.authData) } })) } },
  { name: "credCert signed by an outsider", spec: { outsiderSignsLeaf: true } },
  { name: "intermediate signed by an outsider", spec: { outsiderSignsIntermediate: true } },
  { name: "the root does not hash to the pin", deps: (a) => ({ rootSha256: `${a.rootSha256.slice(0, -1)}${a.rootSha256.endsWith("0") ? "1" : "0"}` }) },
  { name: "credCert expired 1 s ago", spec: { leaf: { notAfter: NOW - 1000 } } },
  { name: "credCert valid from 1 s ahead", spec: { leaf: { notBefore: NOW + 1000 } } },
  { name: "intermediate expired 1 s ago", spec: { intermediate: { notAfter: NOW - 1000 } } },
  { name: "intermediate valid from 1 s ahead", spec: { intermediate: { notBefore: NOW + 1000 } } },
  { name: "root expired 1 s ago", spec: { root: { notAfter: NOW - 1000 } } },
  { name: "root valid from 1 s ahead", spec: { root: { notBefore: NOW + 1000 } } },
  { name: "credCert names another issuer", spec: { leaf: { issuerName: "Someone Else CA" } } },
  { name: "credCert key on P-384", spec: { leafCurve: "P-384" } },
  { name: "nonce extension absent", spec: ext(() => null) },
  { name: "nonce extension twice", spec: { repeatNonce: true } },
  { name: "nonce over another challenge", spec: { challenge: OTHER_CHALLENGE } },
  { name: "nonce one bit off", spec: ext((n) => nonceExtension(flip(n))) },
  { name: "nonce of 31 bytes", spec: ext((n) => nonceExtension(n.slice(1))) },
  { name: "nonce not in a SEQUENCE", spec: ext((n) => tlv(0xa1, tlv(0x04, n))) },
  { name: "nonce under tag [0]", spec: ext((n) => seq(tlv(0xa0, tlv(0x04, n)))) },
  { name: "nonce not an OCTET STRING", spec: ext((n) => seq(tlv(0xa1, tlv(0x03, n)))) },
  { name: "nonce sequence of two elements", spec: ext((n) => seq(tlv(0xa1, tlv(0x04, n)), tlv(0xa2, tlv(0x04, n)))) },
  { name: "nonce with a trailing byte inside [1]", spec: ext((n) => seq(tlv(0xa1, cat(tlv(0x04, n), [0])))) },
  { name: "keyId of another key", spec: { keyId: (k) => flip(k) } },
  { name: "keyId and credentialId both another key's", spec: { keyId: (k) => flip(k), credId: (k) => flip(k) } },
  { name: "rpIdHash of another bundle", spec: { appId: "PLANNED.com.example.other" } },
  { name: "rpIdHash of a real team id", spec: { appId: "ABCDE12345.com.phineasfritsch.scenicdrive" } },
  { name: "rpIdHash of the bundle id alone", spec: { appId: "com.phineasfritsch.scenicdrive" } },
  { name: "counter 1", spec: { counter: [0, 0, 0, 1] } },
  { name: "counter 256", spec: { counter: [0, 0, 1, 0] } },
  { name: "counter 65536", spec: { counter: [0, 1, 0, 0] } },
  { name: "counter 2^24", spec: { counter: [1, 0, 0, 0] } },
  { name: "counter 2^31", spec: { counter: [0x80, 0, 0, 0] } },
  { name: "aaguid appattestdevelop without the flag", spec: { aaguid: AAGUID_DEVELOP } },
  { name: "aaguid appattestdevelop with the flag 0", spec: { aaguid: AAGUID_DEVELOP }, env: { APP_ATTEST_ALLOW_DEVELOP: "0" } },
  { name: "aaguid appattest with a non-zero last byte", spec: { aaguid: flip(AAGUID_PRODUCTION, 15) } },
  { name: "aaguid of zeros", spec: { aaguid: new Uint8Array(16) } },
  { name: "credentialIdLength 31", spec: { credIdLength: 31 } },
  { name: "credentialIdLength 33", spec: { credIdLength: 33 } },
  { name: "credentialId one bit off", spec: { credId: (k) => flip(k) } },
  { name: "authData cut to 86 bytes", spec: { authData: (a) => a.slice(0, 86) } },
  { name: "authData cut to 54 bytes", spec: { authData: (a) => a.slice(0, 54) } },
];

/** The well-formed object's three entries, encoded - for the indefinite-length row. */
function cbor3(p: Parts): Uint8Array {
  return cbor({ entries: [["fmt", "apple-appattest"], ["attStmt", { entries: [["x5c", p.x5c], ["receipt", new TextEncoder().encode("receipt")]] }], ["authData", p.authData]] });
}

beforeEach(async () => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(NOW);
  await freshAttestTables();
  await seedChallenge(CHALLENGE, NOW + 60_000);
});

afterEach(() => {
  vi.useRealTimers();
});

describe("every attestation defect is 400 with zero state change (shipped handleAttest)", () => {
  for (const row of ROWS) {
    it(row.name, async () => {
      const a = await attestation(row.spec);
      const deps = { ...testDeps(a, row.env), ...row.deps?.(a) };
      const answer = await postAttest(row.body ? row.body(a) : bodyOf(a), deps);
      expect({ answer, tables: await tables() }).toEqual({ answer: REFUSED, tables: SEEDED });
    });
  }

  it("the untouched attestation of the table is accepted (the rows' control)", async () => {
    const a = await attestation();
    expect((await postAttest(bodyOf(a), testDeps(a))).status).toBe(200);
  });
});
