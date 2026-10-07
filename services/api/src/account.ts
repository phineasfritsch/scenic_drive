/**
 * POST /auth/apple and DELETE /account (T-0287). Both take the caller's session JWT as `Authorization: Bearer` and
 * nothing else as identity (R1: 401 unauthorized otherwise; 503 auth_unavailable without SESSION_JWT_SECRET).
 * /auth/apple takes exactly {identityToken, authorizationCode}, verifies the token (appleIdentity.ts, the key from
 * appleJwks.ts, the nonce the hash of the Bearer itself), exchanges the code for a refresh token only with the owner's
 * APPLE_CLIENT_SECRET, binds the Apple sub to the session's device and answers the session JWT re-signed with apple
 * (R2-R6). Every defect is 400 invalid_identity_token with nothing written. /account revokes every stored refresh token
 * of the user, then deletes every user row of every D1 table in one batch and answers {deleted, revoke_pending} (R7).
 */
import { bindApple, deleteUser, userBindings, type AccountUser } from "./accountStore";
import { appleClient, clientSecret, type AppleClient } from "./appleClient";
import { IdentityRejected, sessionNonce, verifyIdentityToken } from "./appleIdentity";
import { AppleUnavailable, appleKey, emptyJwksCache, type JwksCache } from "./appleJwks";
import { AUTHORIZATION_HEADER, BEARER } from "./sessionIdentity";
import { sessionSecret, signSession, verifySession, type SessionClaims } from "./sessionJwt";

export interface AccountEnv {
  DB: D1Database;
  SESSION_JWT_SECRET?: string;
  /** Owner secret: the pre-signed Sign in with Apple client-secret JWT; absent, no exchange and revoke_pending. */
  APPLE_CLIENT_SECRET?: string;
}

export interface AccountDeps {
  db: D1Database;
  /** null when SESSION_JWT_SECRET is absent or too short. */
  secret: string | null;
  /** null when APPLE_CLIENT_SECRET is absent or not a JWT. */
  clientSecret: string | null;
  apple: AppleClient;
  jwks: JwksCache;
  now: () => Date;
}

/** One per isolate: the production JWKS cache. */
export const PRODUCTION_JWKS: JwksCache = emptyJwksCache();

export function accountDepsFromEnv(env: AccountEnv): AccountDeps {
  return { db: env.DB, secret: sessionSecret(env.SESSION_JWT_SECRET), clientSecret: clientSecret(env.APPLE_CLIENT_SECRET),
    apple: appleClient((url, init) => fetch(url, init)), jwks: PRODUCTION_JWKS, now: () => new Date() };
}

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });

const UNAUTHORIZED = () => json({ error: "unauthorized" }, 401);
const UNAVAILABLE = () => json({ error: "auth_unavailable" }, 503);
const INVALID = () => json({ error: "invalid_identity_token" }, 400);
const APPLE_DOWN = () => json({ error: "apple_unavailable" }, 503);
const STORE_DOWN = () => json({ error: "account_unavailable" }, 503);

const BODY_KEYS = ["authorizationCode", "identityToken"];
const AUTHORIZATION_CODE = /^[A-Za-z0-9._-]{1,512}$/;

/** The verified session and its compact token, or null: the ONE read of the request's Authorization header. */
async function caller(req: Request, secret: string, nowMs: number): Promise<{ token: string; claims: SessionClaims } | null> {
  const match = BEARER.exec(req.headers.get(AUTHORIZATION_HEADER) ?? "");
  if (match === null) return null;
  const claims = await verifySession(secret, match[1]!, nowMs);
  return claims === null ? null : { token: match[1]!, claims };
}

/** The refresh token of a 200 exchange that carries one; null for anything else, a throw included. */
async function exchangedRefreshToken(deps: AccountDeps, code: string): Promise<string | null> {
  if (deps.clientSecret === null) return null;
  try {
    const response = await deps.apple.exchange(code, deps.clientSecret);
    if (response.status !== 200) return null;
    const body: unknown = await response.json();
    const token = typeof body === "object" && body !== null ? (body as { refresh_token?: unknown }).refresh_token : undefined;
    return typeof token === "string" && token.length > 0 ? token : null;
  } catch {
    return null;
  }
}

export async function handleAuthApple(req: Request, deps: AccountDeps): Promise<Response> {
  if (req.method !== "POST") return json({ error: "POST only" }, 405);
  if (deps.secret === null) return UNAVAILABLE();
  const nowMs = deps.now().getTime();
  const session = await caller(req, deps.secret, nowMs);
  if (session === null) return UNAUTHORIZED();
  let body: Record<string, unknown>;
  try {
    const raw: unknown = await req.json();
    if (typeof raw !== "object" || raw === null || Array.isArray(raw)) return INVALID();
    body = raw as Record<string, unknown>;
  } catch {
    return INVALID();
  }
  const { identityToken, authorizationCode } = body;
  if (Object.keys(body).sort().join() !== BODY_KEYS.join()) return INVALID();
  if (typeof identityToken !== "string"
    || typeof authorizationCode !== "string" || !AUTHORIZATION_CODE.test(authorizationCode)) return INVALID();

  let appleSub: string;
  try {
    appleSub = await verifyIdentityToken(identityToken, await sessionNonce(session.token),
      (kid) => appleKey(kid, deps.jwks, () => deps.apple.keys(), nowMs), nowMs);
  } catch (e) {
    if (e instanceof IdentityRejected) return INVALID();
    if (e instanceof AppleUnavailable) return APPLE_DOWN();
    throw e;
  }
  const refreshToken = await exchangedRefreshToken(deps, authorizationCode);
  try {
    await bindApple(deps.db, session.claims.sub, appleSub, refreshToken, nowMs);
  } catch {
    return STORE_DOWN();
  }
  const { sub, act } = session.claims;
  const signed = await signSession(deps.secret, act === undefined ? { sub, apple: appleSub } : { sub, act, apple: appleSub }, nowMs);
  return json({ token: signed.token, expires_at: new Date(signed.expiresAtMs).toISOString() });
}

/** True iff Apple answered 200 to revoking `token`; a throw is false. */
async function revoked(deps: AccountDeps, secret: string, token: string): Promise<boolean> {
  try {
    return (await deps.apple.revoke(token, secret)).status === 200;
  } catch {
    return false;
  }
}

export async function handleDeleteAccount(req: Request, deps: AccountDeps): Promise<Response> {
  if (req.method !== "DELETE") return json({ error: "DELETE only" }, 405);
  if (deps.secret === null) return UNAVAILABLE();
  const session = await caller(req, deps.secret, deps.now().getTime());
  if (session === null) return UNAUTHORIZED();
  const user: AccountUser = { deviceId: session.claims.sub, appleSub: session.claims.apple ?? null, accountToken: session.claims.act ?? null };
  let bindings;
  try {
    bindings = await userBindings(deps.db, user);
  } catch {
    return STORE_DOWN();
  }
  let pending = false;
  for (const binding of bindings) {
    const secret = deps.clientSecret;
    if (secret === null || binding.refreshToken === null || !(await revoked(deps, secret, binding.refreshToken))) pending = true;
  }
  try {
    await deleteUser(deps.db, user);
  } catch {
    return STORE_DOWN();
  }
  return json({ deleted: true, revoke_pending: pending });
}
