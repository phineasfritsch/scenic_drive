/**
 * The three Apple endpoints Sign in with Apple needs (T-0287 R4, R6, R7), behind one injected fetch: the JWKS, the
 * authorization-code exchange and token revocation. The two form posts carry client_id = APP_BUNDLE_ID and the owner's
 * client secret (APPLE_CLIENT_SECRET: a pre-signed ES256 JWT; the .p8 never reaches the Worker).
 */
import { APP_BUNDLE_ID } from "./asnNotification";
import { APPLE_JWKS_URL } from "./appleJwks";

export const APPLE_TOKEN_URL = "https://appleid.apple.com/auth/token";
export const APPLE_REVOKE_URL = "https://appleid.apple.com/auth/revoke";
/** A client secret that is not three base64url segments counts as absent. */
export const CLIENT_SECRET = /^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/;

export type FetchImpl = (url: string, init?: RequestInit) => Promise<Response>;

export interface AppleClient {
  keys(): Promise<Response>;
  /** POST /auth/token: the authorization code for a refresh token. */
  exchange(code: string, clientSecret: string): Promise<Response>;
  /** POST /auth/revoke: a refresh token. */
  revoke(refreshToken: string, clientSecret: string): Promise<Response>;
}

export function clientSecret(value: unknown): string | null {
  return typeof value === "string" && CLIENT_SECRET.test(value) ? value : null;
}

const form = (fields: Record<string, string>): RequestInit => ({
  method: "POST",
  headers: { "content-type": "application/x-www-form-urlencoded" },
  body: new URLSearchParams(fields).toString(),
});

export function appleClient(fetchImpl: FetchImpl): AppleClient {
  return {
    keys: () => fetchImpl(APPLE_JWKS_URL),
    exchange: (code, secret) => fetchImpl(APPLE_TOKEN_URL,
      form({ client_id: APP_BUNDLE_ID, client_secret: secret, code, grant_type: "authorization_code" })),
    revoke: (token, secret) => fetchImpl(APPLE_REVOKE_URL,
      form({ client_id: APP_BUNDLE_ID, client_secret: secret, token, token_type_hint: "refresh_token" })),
  };
}
