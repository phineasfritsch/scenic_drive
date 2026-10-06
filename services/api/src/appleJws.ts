/**
 * Verifies an Apple-signed JWS (an App Store Server Notification's signedPayload, and the signedTransactionInfo /
 * signedRenewalInfo inside it) - T-0267 R3. The header's alg is exactly ES256; x5c is exactly [leaf, intermediate,
 * root]; the root's SHA-256 equals the pinned fingerprint; each certificate is signed by the next and names it
 * as issuer; every certificate is valid at `now`; the intermediate and leaf carry Apple's marker OIDs; the JWS
 * signature is 64 raw bytes (r||s) verified with the leaf's key - a P-256 key is the only one
 * whose ECDSA signature is 64 bytes, so the length check is what refuses a P-384 leaf. Any failure throws JwsRejected.
 */
import { importKey, parseCertificate, sha256Hex, signedBy, type Certificate } from "./x509";

/** SHA-256 of https://www.apple.com/certificateauthority/AppleRootCA-G3.cer, measured 2026-10-05 (Log R1). */
export const APPLE_ROOT_CA_G3_SHA256 = "63343abfb89a6a03ebb57e9b3f5fa7be7c4f5c756f3017b3a8c488c3653e9179";
/** Apple Worldwide Developer Relations intermediate marker. */
export const OID_APPLE_WWDR_INTERMEDIATE = "1.2.840.113635.100.6.2.1";
/** The App Store signing leaf's marker. */
export const OID_APPLE_STORE_LEAF = "1.2.840.113635.100.6.11.1";

export class JwsRejected extends Error {}

export interface JwsTrust {
  /** Lowercase hex SHA-256 of the one root certificate the chain must end in. */
  rootSha256: string;
  now(): Date;
}

function reject(why: string): never {
  throw new JwsRejected(why);
}

function base64Bytes(text: string, url: boolean): Uint8Array {
  const pattern = url ? /^[A-Za-z0-9_-]*$/ : /^[A-Za-z0-9+/]*={0,2}$/;
  if (!pattern.test(text)) reject("not base64");
  const plain = url ? text.replace(/-/g, "+").replace(/_/g, "/") : text;
  try {
    return Uint8Array.from(atob(plain.padEnd(Math.ceil(plain.length / 4) * 4, "=")), (c) => c.charCodeAt(0));
  } catch {
    return reject("not base64");
  }
}

function jsonPart(part: string): Record<string, unknown> {
  let value: unknown;
  try {
    value = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(base64Bytes(part, true)));
  } catch (e) {
    if (e instanceof JwsRejected) throw e;
    return reject("not JSON");
  }
  if (typeof value !== "object" || value === null || Array.isArray(value)) reject("not a JSON object");
  return value as Record<string, unknown>;
}

async function chain(x5c: unknown, trust: JwsTrust): Promise<Certificate> {
  if (!Array.isArray(x5c) || x5c.length !== 3 || !x5c.every((c) => typeof c === "string")) reject("x5c is not 3 certificates");
  let certs: Certificate[];
  try {
    certs = (x5c as string[]).map((c) => parseCertificate(base64Bytes(c, false)));
  } catch (e) {
    if (e instanceof JwsRejected) throw e;
    return reject("unparseable certificate");
  }
  const [leaf, intermediate, root] = certs as [Certificate, Certificate, Certificate];
  if ((await sha256Hex(root.der)) !== trust.rootSha256) reject("root is not the pinned root");
  const now = trust.now().getTime();
  for (const cert of certs) if (!(cert.notBefore <= now && now <= cert.notAfter)) reject("certificate outside its validity");
  if (!intermediate.extensions.includes(OID_APPLE_WWDR_INTERMEDIATE)) reject("intermediate lacks the WWDR OID");
  if (!leaf.extensions.includes(OID_APPLE_STORE_LEAF)) reject("leaf lacks the App Store OID");
  try {
    if (!(await signedBy(intermediate, root))) reject("intermediate not signed by root");
    if (!(await signedBy(leaf, intermediate))) reject("leaf not signed by intermediate");
  } catch (e) {
    if (e instanceof JwsRejected) throw e;
    return reject("chain signature unverifiable");
  }
  return leaf;
}

/** The verified payload of `jws`; throws JwsRejected on any defect. */
export async function verifyAppleJws(jws: unknown, trust: JwsTrust): Promise<Record<string, unknown>> {
  if (typeof jws !== "string") reject("not a string");
  const parts = jws.split(".");
  if (parts.length !== 3) reject("not three parts");
  const [head, body, sig] = parts as [string, string, string];
  const header = jsonPart(head);
  if (header.alg !== "ES256") reject("alg is not ES256");
  const leaf = await chain(header.x5c, trust);
  const signature = base64Bytes(sig, true);
  if (signature.length !== 64) reject("signature is not 64 bytes");
  let ok: boolean;
  try {
    ok = await crypto.subtle.verify({ name: "ECDSA", hash: "SHA-256" }, await importKey(leaf), signature,
      new TextEncoder().encode(`${head}.${body}`));
  } catch {
    return reject("signature unverifiable");
  }
  if (!ok) reject("bad signature");
  return jsonPart(body);
}
