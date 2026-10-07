/**
 * The Sign in with Apple identity token (T-0287 R3, R5), Apple's 'Verify the identity token' steps: an RS256 JWS whose
 * header is {alg, kid} plus at most typ "JWT", signed by the Apple key published under kid; iss APPLE_ISSUER; aud the
 * app's bundle id; now < exp; iat within APPLE_CLOCK_SKEW_S ahead and APPLE_TOKEN_MAX_AGE_S behind; sub an Apple user
 * id; nonce the lowercase-hex SHA256 of the caller's session JWT. Every defect throws IdentityRejected. Only sub is
 * read: email and every other claim are never read or stored.
 */
import { APP_BUNDLE_ID } from "./asnNotification";

export const APPLE_ISSUER = "https://appleid.apple.com";
export const APPLE_CLOCK_SKEW_S = 60;
export const APPLE_TOKEN_MAX_AGE_S = 600;
export const IDENTITY_TOKEN_MAX_LENGTH = 8192;
/** Apple's user ids are 44 characters of digits, hex and dots. */
export const APPLE_SUB = /^[A-Za-z0-9.]{1,64}$/;

const JWS = /^([A-Za-z0-9_-]+)\.([A-Za-z0-9_-]+)\.([A-Za-z0-9_-]+)$/;
const HEADER_KEYS = ["alg", "kid", "typ"];

export class IdentityRejected extends Error {}

const reject = (why: string): never => {
  throw new IdentityRejected(why);
};

const utf8 = (text: string) => new TextEncoder().encode(text);

function fromB64url(text: string): Uint8Array {
  const plain = text.replace(/-/g, "+").replace(/_/g, "/");
  return Uint8Array.from(atob(plain.padEnd(Math.ceil(plain.length / 4) * 4, "=")), (c) => c.charCodeAt(0));
}

function jsonObject(segment: string): Record<string, unknown> {
  let value: unknown;
  try {
    value = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(fromB64url(segment)));
  } catch {
    return reject("segment is not JSON");
  }
  if (typeof value !== "object" || value === null || Array.isArray(value)) reject("segment is not a JSON object");
  return value as Record<string, unknown>;
}

/** The nonce the app hashes into its request: lowercase hex SHA256 of the session JWT it holds (R3). */
export async function sessionNonce(sessionToken: string): Promise<string> {
  const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", utf8(sessionToken)));
  return Array.from(digest, (b) => b.toString(16).padStart(2, "0")).join("");
}

/** The Apple sub of a valid token; `keyFor` answers the Apple key published under a kid, or null. */
export async function verifyIdentityToken(token: string, expectedNonce: string,
  keyFor: (kid: string) => Promise<CryptoKey | null>, nowMs: number): Promise<string> {
  if (token.length > IDENTITY_TOKEN_MAX_LENGTH) reject("token is too long");
  const parts = JWS.exec(token) ?? reject("token is not a compact JWS");
  const header = jsonObject(parts[1]!);
  if (!Object.keys(header).every((k) => HEADER_KEYS.includes(k))) reject("header carries a key it may not");
  if (header.alg !== "RS256") reject("alg is not RS256");
  if ("typ" in header && header.typ !== "JWT") reject("typ is not JWT");
  const kid = header.kid;
  if (typeof kid !== "string" || kid.length === 0) reject("kid is not a string");
  const key = (await keyFor(kid as string)) ?? reject("no Apple key has this kid");
  let signature: Uint8Array;
  try {
    signature = fromB64url(parts[3]!);
  } catch {
    return reject("signature is not base64url");
  }
  const valid = await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key, signature, utf8(`${parts[1]}.${parts[2]}`));
  if (!valid) reject("signature is not Apple's");

  const claims = jsonObject(parts[2]!);
  const { iss, aud, exp, iat, sub, nonce } = claims;
  if (iss !== APPLE_ISSUER) reject("iss is not Apple");
  if (aud !== APP_BUNDLE_ID) reject("aud is not this app");
  if (!Number.isSafeInteger(exp) || !Number.isSafeInteger(iat)) reject("exp or iat is not an integer");
  const now = Math.floor(nowMs / 1000);
  if (!(now < (exp as number))) reject("expired");
  if (!((iat as number) <= now + APPLE_CLOCK_SKEW_S)) reject("issued in the future");
  if (!(now - (iat as number) <= APPLE_TOKEN_MAX_AGE_S)) reject("issued too long ago");
  if (typeof sub !== "string" || !APPLE_SUB.test(sub)) reject("sub is not an Apple user id");
  if (nonce !== expectedNonce) reject("nonce is not this session's");
  return sub as string;
}
