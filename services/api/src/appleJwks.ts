/**
 * Apple's Sign in with Apple public keys (T-0287 R4): the JWKS at APPLE_JWKS_URL, cached APPLE_JWKS_TTL_MS. A key is
 * selected by kid EQUALITY; a kid absent from a live cache buys ONE refetch, and only when the cached set is at least
 * APPLE_JWKS_REFETCH_MIN_AGE_MS old; still absent is null - never a fallback key. A fetch that throws, is not 200 or is
 * not {keys: [...]} throws AppleUnavailable and leaves the cache as it was. Only RS256 RSA signing keys of at least
 * MIN_RSA_MODULUS_BITS are usable; a kid listed twice is dropped (fail closed).
 */

export const APPLE_JWKS_URL = "https://appleid.apple.com/auth/keys";
export const APPLE_JWKS_TTL_MS = 3_600_000;
export const APPLE_JWKS_REFETCH_MIN_AGE_MS = 60_000;
export const MIN_RSA_MODULUS_BITS = 2048;

export class AppleUnavailable extends Error {}

export interface JwksCache {
  /** null until the first successful fetch. */
  keys: Map<string, CryptoKey> | null;
  fetchedAtMs: number;
}

export const emptyJwksCache = (): JwksCache => ({ keys: null, fetchedAtMs: 0 });

const B64URL = /^[A-Za-z0-9_-]+$/;

function fromB64url(text: string): Uint8Array {
  const plain = text.replace(/-/g, "+").replace(/_/g, "/");
  return Uint8Array.from(atob(plain.padEnd(Math.ceil(plain.length / 4) * 4, "=")), (c) => c.charCodeAt(0));
}

/** The bit length of a big-endian unsigned integer. */
export function modulusBits(n: Uint8Array): number {
  let at = 0;
  while (at < n.length && n[at] === 0) at += 1;
  if (at === n.length) return 0;
  return (n.length - at - 1) * 8 + (32 - Math.clz32(n[at]!));
}

async function usableKey(entry: unknown): Promise<[string, CryptoKey] | null> {
  if (typeof entry !== "object" || entry === null || Array.isArray(entry)) return null;
  const { kty, alg, use, kid, n, e } = entry as Record<string, unknown>;
  if (kty !== "RSA" || alg !== "RS256" || (use !== undefined && use !== "sig")) return null;
  if (typeof kid !== "string" || kid.length === 0) return null;
  if (typeof n !== "string" || !B64URL.test(n) || typeof e !== "string" || !B64URL.test(e)) return null;
  try {
    if (modulusBits(fromB64url(n)) < MIN_RSA_MODULUS_BITS) return null;
    const key = await crypto.subtle.importKey("jwk", { kty: "RSA", n, e, alg: "RS256", ext: true },
      { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"]);
    return [kid, key];
  } catch {
    return null;
  }
}

async function refresh(cache: JwksCache, fetchKeys: () => Promise<Response>, nowMs: number): Promise<void> {
  let body: unknown;
  try {
    const response = await fetchKeys();
    if (response.status !== 200) throw new AppleUnavailable(`JWKS answered ${response.status}`);
    body = await response.json();
  } catch (e) {
    throw e instanceof AppleUnavailable ? e : new AppleUnavailable("JWKS fetch failed");
  }
  if (typeof body !== "object" || body === null || !Array.isArray((body as { keys?: unknown }).keys)) {
    throw new AppleUnavailable("JWKS is not {keys: [...]}");
  }
  const found = new Map<string, CryptoKey>();
  const twice = new Set<string>();
  for (const entry of (body as { keys: unknown[] }).keys) {
    const usable = await usableKey(entry);
    if (usable === null) continue;
    if (found.has(usable[0])) twice.add(usable[0]);
    found.set(usable[0], usable[1]);
  }
  for (const kid of twice) found.delete(kid);
  cache.keys = found;
  cache.fetchedAtMs = nowMs;
}

/** The key Apple publishes under `kid`, or null. Throws AppleUnavailable when a needed fetch fails. */
export async function appleKey(kid: string, cache: JwksCache, fetchKeys: () => Promise<Response>, nowMs: number): Promise<CryptoKey | null> {
  if (cache.keys === null || nowMs - cache.fetchedAtMs >= APPLE_JWKS_TTL_MS) await refresh(cache, fetchKeys, nowMs);
  let key = cache.keys!.get(kid);
  if (key === undefined && nowMs - cache.fetchedAtMs >= APPLE_JWKS_REFETCH_MIN_AGE_MS) {
    await refresh(cache, fetchKeys, nowMs);
    key = cache.keys!.get(kid);
  }
  return key ?? null;
}
