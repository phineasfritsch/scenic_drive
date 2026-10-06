/**
 * Verifies an Apple App Attest attestation object (T-0278 R2-R4), Apple's 'Validating apps that connect to your
 * server' steps 1-9: the CBOR object is exactly {fmt, attStmt, authData} with fmt apple-appattest; attStmt.x5c is
 * exactly [credCert, intermediate], chained to the pinned App Attestation root, every certificate valid at now;
 * the credCert's 1.2.840.113635.100.8.2 extension holds SHA256(authData || SHA256(challenge)); keyId is the SHA-256
 * of the credCert's P-256 point; authData carries rpIdHash = SHA256(APP_ATTEST_APP_ID), counter 0, a ruled aaguid
 * and credentialId = keyId. Any failure throws AttestRejected.
 */
import { APP_BUNDLE_ID } from "./asnNotification";
import { decodeCbor, type Cbor } from "./cbor";
import { children, expectTag, readOnly } from "./der";
import { OID_P256, parseCertificate, sameBytes, sha256Hex, signedBy, type Certificate } from "./x509";

/** SHA-256 of the DER in https://www.apple.com/certificateauthority/Apple_App_Attestation_Root_CA.pem (Log R2). */
export const APPLE_APP_ATTEST_ROOT_CA_SHA256 = "1cb9823ba28ba6ad2d33a006941de2ae4f513ef1d4e831b9f7e0fa7b6242c932";
/** That PEM's body: the Apple App Attestation Root CA, a public certificate. It must hash to the pin above. */
export const APPLE_APP_ATTEST_ROOT_CA = "MIICITCCAaegAwIBAgIQC/O+DvHN0uD7jG5yH2IXmDAKBggqhkjOPQQDAzBSMSYwJAYDVQQDDB1BcHBsZSBBcHAgQXR0ZXN0YXRpb24gUm9vdCBDQTETMBEGA1UECgwKQXBwbGUgSW5jLjETMBEGA1UECAwKQ2FsaWZvcm5pYTAeFw0yMDAzMTgxODMyNTNaFw00NTAzMTUwMDAwMDBaMFIxJjAkBgNVBAMMHUFwcGxlIEFwcCBBdHRlc3RhdGlvbiBSb290IENBMRMwEQYDVQQKDApBcHBsZSBJbmMuMRMwEQYDVQQIDApDYWxpZm9ybmlhMHYwEAYHKoZIzj0CAQYFK4EEACIDYgAERTHhmLW07ATaFQIEVwTtT4dyctdhNbJhFs/Ii2FdCgAHGbpphY3+d8qjuDngIN3WVhQUBHAoMeQ/cLiP1sOUtgjqK9auYen1mMEvRq9Sk3Jm5X8U62H+xTD3FE9TgS41o0IwQDAPBgNVHRMBAf8EBTADAQH/MB0GA1UdDgQWBBSskRBTM72+aEH/pwyp5frq5eWKoTAOBgNVHQ8BAf8EBAMCAQYwCgYIKoZIzj0EAwMDaAAwZQIwQgFGnByvsiVbpTKwSga0kP0e8EeDS4+sQmTvb7vn53O5+FRXgeLhpJ06ysC5PrOyAjEAp5U4xDgEgllF7En3VcE3iexZZtKeYnpqtijVoyFraWVIyd/dganmrduC1bmTBGwD";
/** The credCert extension that carries the nonce. */
export const OID_APP_ATTEST_NONCE = "1.2.840.113635.100.8.2";

/** The Apple Developer Team ID; PLANNED until the owner supplies it, so no real device's rpIdHash matches (R3). */
export type TeamId = "PLANNED";
export const APPLE_TEAM_ID: TeamId = "PLANNED";
/** The App ID App Attest hashes into authData's rpIdHash. */
export const APP_ATTEST_APP_ID = `${APPLE_TEAM_ID}.${APP_BUNDLE_ID}`;

const AAGUID_PRODUCTION = "appattest\0\0\0\0\0\0\0";
const AAGUID_DEVELOP = "appattestdevelop";

export class AttestRejected extends Error {}

export interface AttestTrust {
  /** The root certificate's DER; it must hash to rootSha256 or every attestation is refused. */
  rootDer: Uint8Array;
  rootSha256: string;
  /** Accept the appattestdevelop aaguid (R4); production is always accepted. */
  allowDevelop: boolean;
  now(): Date;
}

export interface AttestInput {
  keyId: Uint8Array;
  attestation: Uint8Array;
  challenge: string;
}

export interface AttestedKey {
  /** The credCert's SubjectPublicKeyInfo DER - what a later assertion is verified with. */
  publicKey: Uint8Array;
  environment: "production" | "development";
}

function reject(why: string): never {
  throw new AttestRejected(why);
}

async function sha256(bytes: Uint8Array): Promise<Uint8Array> {
  return new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
}

/** The map `value`, whose keys must be exactly `keys`. */
function mapOf(value: Cbor | undefined, keys: string[]): Map<string, Cbor> {
  if (!(value instanceof Map)) return reject("not a CBOR map");
  if ([...value.keys()].sort().join() !== keys.join()) reject(`keys are not exactly ${keys.join()}`);
  return value;
}

async function credCert(x5c: Uint8Array[], trust: AttestTrust): Promise<Certificate> {
  if ((await sha256Hex(trust.rootDer)) !== trust.rootSha256) reject("root is not the pinned root");
  let certs: Certificate[];
  try {
    certs = [...x5c, trust.rootDer].map(parseCertificate);
  } catch {
    return reject("unparseable certificate");
  }
  const [leaf, intermediate, root] = certs as [Certificate, Certificate, Certificate];
  const now = trust.now().getTime();
  for (const cert of certs) if (!(cert.notBefore <= now && now <= cert.notAfter)) reject("certificate outside its validity");
  if (leaf.curve !== OID_P256) reject("credCert key is not P-256");
  try {
    if (!(await signedBy(intermediate, root))) reject("intermediate not signed by root");
    if (!(await signedBy(leaf, intermediate))) reject("credCert not signed by intermediate");
  } catch (e) {
    if (e instanceof AttestRejected) throw e;
    return reject("chain signature unverifiable");
  }
  return leaf;
}

/** The single OCTET STRING of SEQUENCE { [1] EXPLICIT OCTET STRING } in the credCert's nonce extension. */
function nonceOf(leaf: Certificate): Uint8Array {
  const at = leaf.extensions.indexOf(OID_APP_ATTEST_NONCE);
  if (at < 0 || leaf.extensions.lastIndexOf(OID_APP_ATTEST_NONCE) !== at) reject("nonce extension absent or repeated");
  try {
    const parts = children(expectTag(readOnly(leaf.extensionValues[at]!), 0x30));
    if (parts.length !== 1) reject("nonce sequence is not one element");
    return expectTag(readOnly(expectTag(parts[0], 0xa1).value), 0x04).value;
  } catch (e) {
    if (e instanceof AttestRejected) throw e;
    return reject("nonce extension malformed");
  }
}

/** The uncompressed P-256 point in the credCert's SubjectPublicKeyInfo. */
function publicPoint(leaf: Certificate): Uint8Array {
  let bits: Uint8Array;
  try {
    bits = expectTag(children(readOnly(leaf.spki))[1], 0x03).value;
  } catch {
    return reject("credCert key unreadable");
  }
  if (bits.length !== 66 || bits[0] !== 0 || bits[1] !== 0x04) reject("credCert key is not an uncompressed point");
  return bits.subarray(1);
}

/** The verified key of `input`; throws AttestRejected on any defect. */
export async function verifyAttestation(input: AttestInput, trust: AttestTrust): Promise<AttestedKey> {
  let object: Cbor;
  try {
    object = decodeCbor(input.attestation);
  } catch {
    return reject("not CBOR");
  }
  const top = mapOf(object, ["attStmt", "authData", "fmt"]);
  if (top.get("fmt") !== "apple-appattest") reject("fmt is not apple-appattest");
  const statement = mapOf(top.get("attStmt"), ["receipt", "x5c"]);
  const x5c = statement.get("x5c");
  if (!Array.isArray(x5c) || x5c.length !== 2 || !x5c.every((c) => c instanceof Uint8Array)) reject("x5c is not 2 certificates");
  if (!(statement.get("receipt") instanceof Uint8Array)) reject("receipt is not bytes");
  const authData = top.get("authData");
  if (!(authData instanceof Uint8Array)) return reject("authData is not bytes");

  const leaf = await credCert(x5c as Uint8Array[], trust);
  const clientDataHash = await sha256(new TextEncoder().encode(input.challenge));
  const signed = new Uint8Array(authData.length + clientDataHash.length);
  signed.set(authData);
  signed.set(clientDataHash, authData.length);
  if (!sameBytes(nonceOf(leaf), await sha256(signed))) reject("nonce mismatch");
  if (!sameBytes(await sha256(publicPoint(leaf)), input.keyId)) reject("keyId is not the credCert key's hash");

  if (authData.length < 87) reject("authData truncated");
  if (!sameBytes(authData.subarray(0, 32), await sha256(new TextEncoder().encode(APP_ATTEST_APP_ID)))) reject("rpIdHash is not the App ID's");
  const counter = ((authData[33]! << 24) | (authData[34]! << 16) | (authData[35]! << 8) | authData[36]!) >>> 0;
  if (counter !== 0) reject("counter is not 0");
  const aaguid = String.fromCharCode(...authData.subarray(37, 53));
  const environment = aaguid === AAGUID_PRODUCTION ? "production"
    : aaguid === AAGUID_DEVELOP && trust.allowDevelop ? "development" : reject("aaguid is not accepted");
  if (authData[53]! * 256 + authData[54]! !== 32) reject("credentialId is not 32 bytes");
  if (!sameBytes(authData.subarray(55, 87), input.keyId)) reject("credentialId is not the keyId");
  return { publicKey: leaf.spki, environment };
}
