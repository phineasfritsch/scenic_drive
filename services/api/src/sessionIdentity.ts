/**
 * Who is calling, once App Attest exists (T-0278 R6). Without SESSION_JWT_SECRET: today's identify, unchanged
 * (`legacy`). With it: a Bearer session JWT that verifies is the identity - sub the bucket, act's live entitlement
 * the tier - and the bare headers are ignored; a Bearer that does not verify is the shared unidentified bucket, anon
 * (fail closed, no fallthrough); no Bearer reaches `legacy` only while the migration flag IDENTITY_HEADERS is "1".
 */
import { readEntitlement } from "./entitlementStore";
import type { Tier } from "./quota";
import { sessionSecret, verifySession } from "./sessionJwt";

export const AUTHORIZATION_HEADER = "authorization";
/** The bucket every caller without a valid identity shares; equal to routerDeps' UNIDENTIFIED_DEVICE. */
export const UNIDENTIFIED_SESSION = "unidentified";

export const BEARER = /^Bearer ([A-Za-z0-9_.-]+)$/;

export interface SessionEnv {
  DB?: D1Database;
  /** secret: `wrangler secret put SESSION_JWT_SECRET`; absent, identity is today's header identity. */
  SESSION_JWT_SECRET?: string;
  /** The migration flag: "1" keeps the bare x-scenic-device / x-scenic-account-token path for a caller with no JWT. */
  IDENTITY_HEADERS?: string;
}

export interface CallerIdentity {
  userId: string;
  tier: Tier;
}

async function entitledTier(db: D1Database | undefined, token: string, nowMs: number): Promise<Tier> {
  if (db === undefined) return "anon";
  try {
    return (await readEntitlement(db, token, nowMs)).status === "active" ? "paid" : "anon";
  } catch {
    return "anon";
  }
}

export async function identifyCaller(bearer: string | null, env: SessionEnv, nowMs: number,
  legacy: () => Promise<CallerIdentity>): Promise<CallerIdentity> {
  const secret = sessionSecret(env.SESSION_JWT_SECRET);
  if (secret === null) return legacy();
  if (bearer === null) return env.IDENTITY_HEADERS === "1" ? legacy() : { userId: UNIDENTIFIED_SESSION, tier: "anon" };
  const match = BEARER.exec(bearer);
  const claims = match ? await verifySession(secret, match[1]!, nowMs) : null;
  if (claims === null) return { userId: UNIDENTIFIED_SESSION, tier: "anon" };
  return { userId: claims.sub, tier: claims.act === undefined ? "anon" : await entitledTier(env.DB, claims.act, nowMs) };
}
