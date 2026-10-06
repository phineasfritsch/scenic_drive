/**
 * X.509 for the App Store chain (T-0267 R3): parse what verification needs from a DER certificate - the signed
 * TBS bytes, the signature algorithm and value, issuer/subject names, validity, the EC public key's curve and
 * the extension OIDs - and verify one certificate's signature with its parent's key through WebCrypto.
 */
import { DerError, children, ecdsaRaw, expectTag, oidText, readOnly, timeMs } from "./der";

export const OID_EC_PUBLIC_KEY = "1.2.840.10045.2.1";
export const OID_ECDSA_SHA256 = "1.2.840.10045.4.3.2";
export const OID_ECDSA_SHA384 = "1.2.840.10045.4.3.3";
export const OID_P256 = "1.2.840.10045.3.1.7";
export const OID_P384 = "1.3.132.0.34";

const CURVES: Record<string, { name: "P-256" | "P-384"; size: number }> = {
  [OID_P256]: { name: "P-256", size: 32 },
  [OID_P384]: { name: "P-384", size: 48 },
};
const HASHES: Record<string, "SHA-256" | "SHA-384"> = { [OID_ECDSA_SHA256]: "SHA-256", [OID_ECDSA_SHA384]: "SHA-384" };

export interface Certificate {
  der: Uint8Array;
  tbs: Uint8Array;
  signatureAlgorithm: string;
  signature: Uint8Array;
  issuer: Uint8Array;
  subject: Uint8Array;
  notBefore: number;
  notAfter: number;
  spki: Uint8Array;
  curve: string;
  extensions: string[];
  /** The extnValue content octets of each extension, index for index with `extensions` (T-0278 R2). */
  extensionValues: Uint8Array[];
}

function bitString(value: Uint8Array): Uint8Array {
  if (value.length === 0 || value[0] !== 0) throw new DerError("BIT STRING with unused bits");
  return value.subarray(1);
}

export function parseCertificate(der: Uint8Array): Certificate {
  const [tbsTlv, algTlv, sigTlv] = children(expectTag(readOnly(der), 0x30));
  const tbs = expectTag(tbsTlv, 0x30);
  const fields = children(tbs);
  let i = fields[0]?.tag === 0xa0 ? 1 : 0;
  expectTag(fields[i++], 0x02);
  expectTag(fields[i++], 0x30);
  const issuer = expectTag(fields[i++], 0x30);
  const [notBefore, notAfter] = children(expectTag(fields[i++], 0x30));
  const subject = expectTag(fields[i++], 0x30);
  const spki = expectTag(fields[i++], 0x30);
  const [keyAlg] = children(spki);
  const [keyType, curve] = children(expectTag(keyAlg, 0x30));
  if (oidText(expectTag(keyType, 0x06).value) !== OID_EC_PUBLIC_KEY) throw new DerError("not an EC public key");
  const extensions: string[] = [];
  const extensionValues: Uint8Array[] = [];
  for (const field of fields.slice(i)) {
    if (field.tag !== 0xa3) continue;
    for (const ext of children(expectTag(children(field)[0], 0x30))) {
      extensions.push(oidText(expectTag(children(expectTag(ext, 0x30))[0], 0x06).value));
      extensionValues.push(expectTag(children(expectTag(ext, 0x30)).at(-1), 0x04).value);
    }
  }
  return {
    der,
    tbs: tbs.raw,
    signatureAlgorithm: oidText(expectTag(children(expectTag(algTlv, 0x30))[0], 0x06).value),
    signature: bitString(expectTag(sigTlv, 0x03).value),
    issuer: issuer.raw,
    subject: subject.raw,
    notBefore: timeMs(notBefore!),
    notAfter: timeMs(notAfter!),
    spki: spki.raw,
    curve: oidText(expectTag(curve, 0x06).value),
    extensions,
    extensionValues,
  };
}

/** The certificate's EC public key as a WebCrypto verify key; an unsupported curve throws. */
export function importKey(cert: Certificate): Promise<CryptoKey> {
  const curve = CURVES[cert.curve];
  if (!curve) throw new DerError("unsupported curve");
  return crypto.subtle.importKey("spki", cert.spki, { name: "ECDSA", namedCurve: curve.name }, false, ["verify"]);
}

export function sameBytes(a: Uint8Array, b: Uint8Array): boolean {
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
  return true;
}

/** True exactly when `child` names `parent` as its issuer and `parent`'s key verifies `child`'s signature. */
export async function signedBy(child: Certificate, parent: Certificate): Promise<boolean> {
  const hash = HASHES[child.signatureAlgorithm];
  const curve = CURVES[parent.curve];
  if (!hash || !curve || !sameBytes(child.issuer, parent.subject)) return false;
  const raw = ecdsaRaw(child.signature, curve.size);
  return crypto.subtle.verify({ name: "ECDSA", hash }, await importKey(parent), raw, child.tbs);
}

export async function sha256Hex(bytes: Uint8Array): Promise<string> {
  const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
  return Array.from(digest, (b) => b.toString(16).padStart(2, "0")).join("");
}
