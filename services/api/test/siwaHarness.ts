/**
 * Shared Sign in with Apple test plumbing (T-0287): test-generated RSA keys served as Apple's JWKS by a fake fetch
 * handed to the shipped appleClient (the fetch and the JWKS cache are the ONLY replacements in the deps), an RS256
 * signer of the test's own, the session JWT oracle (attestHarness's HS256 mintJwt), every shipped migration applied,
 * and every table read back whole. Constants are typed out, never imported from src. Not a test file.
 */
import { env } from "cloudflare:test";
import { accountDepsFromEnv, handleAuthApple, handleDeleteAccount, type AccountDeps } from "../src/account";
import { appleClient } from "../src/appleClient";
import { emptyJwksCache, type JwksCache } from "../src/appleJwks";
import type { Env } from "../src/index";
import { b64url } from "./appleChain";
import { DEVICE, mintJwt, NOW, SECRET } from "./attestHarness";

export { ACCOUNT, DEVICE, mintJwt, NOW, SECRET } from "./attestHarness";
export const S = NOW / 1000;
export const BUNDLE = "com.phineasfritsch.scenicdrive";
export const ISSUER = "https://appleid.apple.com";
export const KEYS_URL = "https://appleid.apple.com/auth/keys";
export const TOKEN_URL = "https://appleid.apple.com/auth/token";
export const REVOKE_URL = "https://appleid.apple.com/auth/revoke";
export const APPLE_USER = "001234.0123456789abcdef0123456789abcdef.1234";
export const OTHER_APPLE_USER = "005678.fedcba9876543210fedcba9876543210.5678";
export const SECOND_DEVICE = "2c3d4e5f-6a7b-4c8d-9e0f-1a2b3c4d5e6f";
export const OTHER_DEVICE = "9a8b7c6d-5e4f-4a3b-8c2d-1e0f9a8b7c6d";
export const OTHER_ACCOUNT = "7e6d5c4b-3a29-4180-9f7e-6d5c4b3a2918";
/** A placeholder of the client secret's shape (three base64url segments); not a credential. */
export const CLIENT_SECRET = "test-client-secret-header.test-client-secret-claims.test-client-secret-signature";
export const AUTH_CODE = "c0de.test-authorization-code";

const MIGRATIONS = import.meta.glob("../migrations/*.sql", { query: "?raw", import: "default", eager: true }) as Record<string, string>;
const utf8 = (t: string) => new TextEncoder().encode(t);
const hex = (b: Uint8Array) => Array.from(b, (x) => (x < 16 ? "0" : "") + x.toString(16)).join("");

export const sha256Hex = async (text: string) => hex(new Uint8Array(await crypto.subtle.digest("SHA-256", utf8(text))));

/** Every table name a shipped migration creates, read from the SQL itself, in migration order. */
export function migrationTables(): string[] {
  return Object.keys(MIGRATIONS).sort().flatMap((file) =>
    [...MIGRATIONS[file]!.matchAll(/CREATE TABLE(?: IF NOT EXISTS)?\s+([A-Za-z_][A-Za-z0-9_]*)/gi)].map((m) => m[1]!));
}

export async function freshAllTables(): Promise<void> {
  for (const file of Object.keys(MIGRATIONS).sort()) {
    for (const statement of MIGRATIONS[file]!.split(";").map((s) => s.trim()).filter(Boolean)) await env.DB.prepare(statement).run();
  }
  for (const table of migrationTables()) await env.DB.prepare(`DELETE FROM ${table}`).run();
}

/** Every migration table's rows, each table sorted by its rows' JSON. */
export async function allTables(): Promise<Record<string, unknown[]>> {
  const out: Record<string, unknown[]> = {};
  for (const table of migrationTables()) {
    const { results } = await env.DB.prepare(`SELECT * FROM ${table}`).all();
    out[table] = results.map((r) => JSON.stringify(r)).sort().map((r) => JSON.parse(r) as unknown);
  }
  return out;
}

export interface TestKey { kid: string; privateKey: CryptoKey; jwk: Record<string, unknown> }

export async function rsaKey(kid: string, bits = 2048, jwk: Record<string, unknown> = {}): Promise<TestKey> {
  const pair = (await crypto.subtle.generateKey({ name: "RSASSA-PKCS1-v1_5", modulusLength: bits,
    publicExponent: new Uint8Array([1, 0, 1]), hash: "SHA-256" }, true, ["sign", "verify"])) as CryptoKeyPair;
  const pub = (await crypto.subtle.exportKey("jwk", pair.publicKey)) as JsonWebKey;
  return { kid, privateKey: pair.privateKey, jwk: { kty: "RSA", kid, use: "sig", alg: "RS256", n: pub.n, e: pub.e, ...jwk } };
}

/** A compact RS256 JWS of the test's own: header and claims serialised as given (a string is used verbatim). */
export async function signJws(header: Record<string, unknown> | string, claims: Record<string, unknown> | string, key: CryptoKey): Promise<string> {
  const h = b64url(typeof header === "string" ? header : JSON.stringify(header));
  const p = b64url(typeof claims === "string" ? claims : JSON.stringify(claims));
  const signature = new Uint8Array(await crypto.subtle.sign("RSASSA-PKCS1-v1_5", key, utf8(`${h}.${p}`)));
  return `${h}.${p}.${b64url(signature)}`;
}

/** The caller's session JWT: T-0278's claims for DEVICE, plus `extra`. */
export const sessionToken = (extra: Record<string, unknown> = {}, nowS = S) =>
  mintJwt({ iss: "scenic-api", sub: DEVICE, iat: nowS, exp: nowS + 3600, ...extra });

/** Apple's claims for `bearer`'s nonce; a key set to undefined is dropped. */
export const identityClaims = async (bearer: string, over: Record<string, unknown> = {}, nowS = S): Promise<Record<string, unknown>> => ({
  iss: ISSUER, aud: BUNDLE, exp: nowS + 600, iat: nowS, sub: APPLE_USER, c_hash: "dGVzdA", email: "relay@privaterelay.appleid.com",
  email_verified: true, is_private_email: true, auth_time: nowS, nonce: await sha256Hex(bearer), nonce_supported: true, ...over,
});

export interface AppleCall { url: string; method: string; contentType: string | null; form: Record<string, string> | null }

export interface FakeApple {
  keys?: () => Response | Promise<Response>;
  exchange?: () => Response | Promise<Response>;
  revoke?: (token: string) => Response | Promise<Response>;
}

export const jsonResponse = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status });

/** A fetch that answers Apple's three URLs and records every call whole. */
export function fakeAppleFetch(set: TestKey[], spec: FakeApple = {}) {
  const calls: AppleCall[] = [];
  const fetchImpl = async (url: string, init?: RequestInit): Promise<Response> => {
    const body = typeof init?.body === "string" ? init.body : null;
    const form = body === null ? null : Object.fromEntries(new URLSearchParams(body));
    calls.push({ url, method: init?.method ?? "GET", contentType: new Headers(init?.headers).get("content-type"), form });
    if (url === KEYS_URL) return spec.keys ? spec.keys() : jsonResponse({ keys: set.map((k) => k.jwk) });
    if (url === TOKEN_URL) return spec.exchange ? spec.exchange() : jsonResponse({ access_token: "a.1", token_type: "Bearer", expires_in: 3600, refresh_token: "r.fresh", id_token: "i.1" });
    if (url === REVOKE_URL) return spec.revoke ? spec.revoke(form?.token ?? "") : new Response("", { status: 200 });
    throw new Error(`unexpected fetch ${url}`);
  };
  return { calls, fetchImpl };
}

export const keysCall: AppleCall = { url: KEYS_URL, method: "GET", contentType: null, form: null };
export const formCall = (url: string, form: Record<string, string>): AppleCall =>
  ({ url, method: "POST", contentType: "application/x-www-form-urlencoded", form });
export const exchangeCall = (code = AUTH_CODE) =>
  formCall(TOKEN_URL, { client_id: BUNDLE, client_secret: CLIENT_SECRET, code, grant_type: "authorization_code" });
export const revokeCall = (token: string) =>
  formCall(REVOKE_URL, { client_id: BUNDLE, client_secret: CLIENT_SECRET, token, token_type_hint: "refresh_token" });

/** Production deps for env plus the session secret; only the Apple fetch and the JWKS cache are the test's. */
export function siwaDeps(fetchImpl: (url: string, init?: RequestInit) => Promise<Response>, extra: Partial<Env> = {},
  jwks: JwksCache = emptyJwksCache()): AccountDeps {
  return { ...accountDepsFromEnv({ ...(env as unknown as Env), SESSION_JWT_SECRET: SECRET, ...extra }), apple: appleClient(fetchImpl), jwks };
}

async function answer(response: Response) {
  return { status: response.status, json: (await response.json()) as unknown };
}

export async function postApple(deps: AccountDeps, body: unknown, bearer: string | null, method = "POST") {
  const headers: Record<string, string> = bearer === null ? {} : { authorization: `Bearer ${bearer}` };
  const init: RequestInit = method === "GET" ? { method, headers } : { method, headers, body: typeof body === "string" ? body : JSON.stringify(body) };
  return answer(await handleAuthApple(new Request("https://scenic-api.test/auth/apple", init), deps));
}

export async function deleteAccount(deps: AccountDeps, bearer: string | null, method = "DELETE") {
  const headers: Record<string, string> = bearer === null ? {} : { authorization: `Bearer ${bearer}` };
  return answer(await handleDeleteAccount(new Request("https://scenic-api.test/account", { method, headers }), deps));
}

/** The session the bind answers: the test's own HS256 signing of the ruled claims, in signSession's order. */
export async function grantedSession(claims: Record<string, unknown>) {
  return { status: 200, json: { token: await mintJwt({ iss: "scenic-api", sub: DEVICE, iat: S, exp: S + 3600, ...claims }), expires_at: "2026-10-06T13:00:00.000Z" } };
}
