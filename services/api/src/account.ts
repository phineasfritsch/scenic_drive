/** STUB for T-0287's red-first run: the route handlers exist and answer 501. */
import { appleClient, clientSecret, type AppleClient } from "./appleClient";
import { emptyJwksCache, type JwksCache } from "./appleJwks";
import { sessionSecret } from "./sessionJwt";

export interface AccountEnv {
  DB: D1Database;
  SESSION_JWT_SECRET?: string;
  APPLE_CLIENT_SECRET?: string;
}

export interface AccountDeps {
  db: D1Database;
  secret: string | null;
  clientSecret: string | null;
  apple: AppleClient;
  jwks: JwksCache;
  now: () => Date;
}

export const PRODUCTION_JWKS: JwksCache = emptyJwksCache();

export function accountDepsFromEnv(env: AccountEnv): AccountDeps {
  return { db: env.DB, secret: sessionSecret(env.SESSION_JWT_SECRET), clientSecret: clientSecret(env.APPLE_CLIENT_SECRET),
    apple: appleClient((url, init) => fetch(url, init)), jwks: PRODUCTION_JWKS, now: () => new Date() };
}

export async function handleAuthApple(_req: Request, _deps: AccountDeps): Promise<Response> {
  return new Response("{}", { status: 501 });
}

export async function handleDeleteAccount(_req: Request, _deps: AccountDeps): Promise<Response> {
  return new Response("{}", { status: 501 });
}
