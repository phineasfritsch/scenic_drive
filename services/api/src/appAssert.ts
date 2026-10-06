/**
 * Verifies an Apple App Attest assertion (T-0280 R3), Apple's 'Verify the assertion' steps: the CBOR object is exactly
 * {authenticatorData, signature}, both byte strings; clientData is the UTF-8 challenge as issued; the signature is a DER
 * ECDSA (P-256, SHA-256) over nonce = SHA256(authenticatorData || SHA256(clientData)) by the key stored at attestation;
 * authenticatorData is exactly 37 bytes with rpIdHash = SHA256(APP_ATTEST_APP_ID) and an unsigned 32-bit counter
 * strictly greater than the stored one. Answers the new counter; any failure throws AttestRejected.
 */
import { APP_ATTEST_APP_ID, AttestRejected } from "./appAttest";
import { decodeCbor, type Cbor } from "./cbor";
import { ecdsaRaw } from "./der";
import { sameBytes } from "./x509";

export interface AssertInput {
  assertion: Uint8Array;
  challenge: string;
  /** The SubjectPublicKeyInfo DER stored at attestation, as hex. */
  publicKeyHex: string;
  storedCounter: number;
}

/** Apple's assertion authenticatorData: rpIdHash 32, flags 1, counter 4. */
export const ASSERTION_AUTH_DATA_LENGTH = 37;

function reject(why: string): never {
  throw new AttestRejected(why);
}

async function sha256(bytes: Uint8Array): Promise<Uint8Array> {
  return new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
}

function fromHex(hex: string): Uint8Array {
  if (!/^(?:[0-9a-f]{2})+$/.test(hex)) return reject("stored key is not hex");
  return Uint8Array.from(hex.match(/../g)!, (b) => parseInt(b, 16));
}

/** The counter of a verified assertion; throws AttestRejected on any defect. */
export async function verifyAssertion(input: AssertInput): Promise<number> {
  let object: Cbor;
  try {
    object = decodeCbor(input.assertion);
  } catch {
    return reject("not CBOR");
  }
  if (!(object instanceof Map) || [...object.keys()].sort().join() !== "authenticatorData,signature") reject("keys are not exactly authenticatorData,signature");
  const authData = (object as Map<string, Cbor>).get("authenticatorData");
  const signature = (object as Map<string, Cbor>).get("signature");
  if (!(authData instanceof Uint8Array) || !(signature instanceof Uint8Array)) return reject("authenticatorData or signature is not bytes");
  if (authData.length !== ASSERTION_AUTH_DATA_LENGTH) reject("authenticatorData is not 37 bytes");

  const clientDataHash = await sha256(new TextEncoder().encode(input.challenge));
  const signed = new Uint8Array(authData.length + clientDataHash.length);
  signed.set(authData);
  signed.set(clientDataHash, authData.length);
  const nonce = await sha256(signed);
  let valid: boolean;
  try {
    const key = await crypto.subtle.importKey("spki", fromHex(input.publicKeyHex), { name: "ECDSA", namedCurve: "P-256" }, false, ["verify"]);
    valid = await crypto.subtle.verify({ name: "ECDSA", hash: "SHA-256" }, key, ecdsaRaw(signature, 32), nonce);
  } catch {
    return reject("signature or key unverifiable");
  }
  if (!valid) reject("signature is not the stored key's over the nonce");

  if (!sameBytes(authData.subarray(0, 32), await sha256(new TextEncoder().encode(APP_ATTEST_APP_ID)))) reject("rpIdHash is not the App ID's");
  const counter = ((authData[33]! << 24) | (authData[34]! << 16) | (authData[35]! << 8) | authData[36]!) >>> 0;
  if (!(counter > input.storedCounter)) reject("counter is not above the stored counter");
  return counter;
}
