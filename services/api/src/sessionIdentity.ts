/**
 * Who is calling, once App Attest exists (T-0278 R6). Without SESSION_JWT_SECRET: today's identify, unchanged
 * (`legacy`). With it: a Bearer session JWT that verifies is the identity - sub the bucket, act's live entitlement
 * the tier - and the bare headers are ignored. A Bearer that does not verify reads exactly as no Bearer (T-0322 B1):
 * `legacy` while the migration flag IDENTITY_HEADERS is "1", else the shared unidentified bucket, anon - so a forged
 * Bearer beside the headers yields only what the headers alone yield, and a stale session never lowers a subscriber.
 * T-0333 R1: identifySession tells the plan family more - with the flag closed, an authorization that is present and
 * does not verify is SESSION_REJECTED, so /plan, /trip and /loop answer 401 and the app renews; identifyCaller (every
 * other caller) reads that as the unidentified bucket, anon, exactly as before.
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

/** What identifySession answers for a present authorization that does not verify while the flag is closed. */
export const SESSION_REJECTED = "session_rejected";

export async function identifySession(bearer: string | null, env: SessionEnv, nowMs: number,
  legacy: () => Promise<CallerIdentity>): Promise<CallerIdentity | typeof SESSION_REJECTED> {
  const secret = sessionSecret(env.SESSION_JWT_SECRET);
  if (secret === null) return legacy();
  const match = bearer === null ? null : BEARER.exec(bearer);
  const claims = match ? await verifySession(secret, match[1]!, nowMs) : null;
  if (claims === null && bearer !== null && env.IDENTITY_HEADERS !== "1") return SESSION_REJECTED;
  if (claims === null) return env.IDENTITY_HEADERS === "1" ? legacy() : { userId: UNIDENTIFIED_SESSION, tier: "anon" };
  return { userId: claims.sub, tier: claims.act === undefined ? "anon" : await entitledTier(env.DB, claims.act, nowMs) };
}

export async function identifyCaller(bearer: string | null, env: SessionEnv, nowMs: number,
  legacy: () => Promise<CallerIdentity>): Promise<CallerIdentity> {
  const who = await identifySession(bearer, env, nowMs, legacy);
  return who === SESSION_REJECTED ? { userId: UNIDENTIFIED_SESSION, tier: "anon" } : who;
}
