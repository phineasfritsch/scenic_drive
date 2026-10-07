/**
 * The session JWT /attest issues (T-0278 R5): HS256 through WebCrypto HMAC, keyed by the SESSION_JWT_SECRET secret.
 * The header is one fixed string; the claims are exactly {iss, sub, iat, exp} and an optional act and apple (T-0287 R6:
 * the Sign in with Apple user id, APPLE_SUB); a token is valid
 * iff its signature verifies, iat <= now < exp in whole seconds and exp - iat == SESSION_TTL_S. Anything else is
 * null - the caller fails closed.
 */
import { APPLE_SUB } from "./appleIdentity";
import { UUID } from "./asn";

export const SESSION_TTL_S = 3600;
export const SESSION_ISSUER = "scenic-api";
/** A secret shorter than this counts as absent. */
export const MIN_SECRET_LENGTH = 32;

const utf8 = (text: string) => new TextEncoder().encode(text);

function b64url(bytes: Uint8Array): string {
  return btoa(String.fromCharCode(...bytes)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function fromB64url(text: string): Uint8Array | null {
  if (!/^[A-Za-z0-9_-]*$/.test(text) || text.length % 4 === 1) return null;
  const plain = text.replace(/-/g, "+").replace(/_/g, "/");
  return Uint8Array.from(atob(plain.padEnd(Math.ceil(plain.length / 4) * 4, "=")), (c) => c.charCodeAt(0));
}

const HEADER = b64url(utf8(JSON.stringify({ alg: "HS256", typ: "JWT" })));

export interface SessionClaims {
  /** The install UUID: the quota bucket. */
  sub: string;
  /** The appAccountToken whose entitlement is the session's tier. */
  act?: string;
  /** The Sign in with Apple user id bound to the device (T-0287 R6). */
  apple?: string;
}

/** The secret, or null when absent or shorter than MIN_SECRET_LENGTH. */
export function sessionSecret(value: unknown): string | null {
  return typeof value === "string" && value.length >= MIN_SECRET_LENGTH ? value : null;
}

function hmacKey(secret: string): Promise<CryptoKey> {
  return crypto.subtle.importKey("raw", utf8(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign", "verify"]);
}

export async function signSession(secret: string, claims: SessionClaims, nowMs: number): Promise<{ token: string; expiresAtMs: number }> {
  const iat = Math.floor(nowMs / 1000);
  const body = { iss: SESSION_ISSUER, sub: claims.sub, iat, exp: iat + SESSION_TTL_S, ...(claims.act ? { act: claims.act } : {}),
    ...(claims.apple ? { apple: claims.apple } : {}) };
  const signing = `${HEADER}.${b64url(utf8(JSON.stringify(body)))}`;
  const signature = new Uint8Array(await crypto.subtle.sign("HMAC", await hmacKey(secret), utf8(signing)));
  return { token: `${signing}.${b64url(signature)}`, expiresAtMs: (iat + SESSION_TTL_S) * 1000 };
}

const CLAIMS = ["exp", "iat", "iss", "sub"];

export async function verifySession(secret: string, token: string, nowMs: number): Promise<SessionClaims | null> {
  const parts = token.split(".");
  if (parts.length !== 3 || parts[0] !== HEADER) return null;
  const signature = fromB64url(parts[2]!);
  if (signature === null || signature.length !== 32) return null;
  if (!(await crypto.subtle.verify("HMAC", await hmacKey(secret), signature, utf8(`${parts[0]}.${parts[1]}`)))) return null;
  let claims: Record<string, unknown>;
  try {
    const value: unknown = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(fromB64url(parts[1]!) ?? new Uint8Array([0xff])));
    if (typeof value !== "object" || value === null || Array.isArray(value)) return null;
    claims = value as Record<string, unknown>;
  } catch {
    return null;
  }
  const keys = Object.keys(claims).filter((k) => k !== "act" && k !== "apple").sort();
  if (keys.join() !== CLAIMS.join() || claims.iss !== SESSION_ISSUER) return null;
  const { sub, iat, exp, act, apple } = claims;
  if (typeof sub !== "string" || !UUID.test(sub)) return null;
  if (!Number.isSafeInteger(iat) || !Number.isSafeInteger(exp) || (exp as number) - (iat as number) !== SESSION_TTL_S) return null;
  const now = Math.floor(nowMs / 1000);
  if (!((iat as number) <= now && now < (exp as number))) return null;
  if ("act" in claims && (typeof act !== "string" || !UUID.test(act))) return null;
  if ("apple" in claims && (typeof apple !== "string" || !APPLE_SUB.test(apple))) return null;
  return { sub, ...(typeof act === "string" ? { act } : {}), ...(typeof apple === "string" ? { apple } : {}) };
}
