/**
 * POST /attest/challenge and POST /attest (T-0278). The first issues a single-use challenge (R1); the second takes
 * {keyId, attestation, challenge, device, appAccountToken?}, verifies the attestation against the live challenge
 * (R2-R4), commits the key and consumes the challenge in one batch, then answers a session JWT whose sub is the
 * install UUID and whose act is the account token (R5). Every defect is 400 invalid_attestation with nothing
 * written; without SESSION_JWT_SECRET both routes are 503 attest_unavailable (R7).
 */
import { UUID } from "./asn";
import { APPLE_APP_ATTEST_ROOT_CA, APPLE_APP_ATTEST_ROOT_CA_SHA256, AttestRejected, verifyAttestation, type AttestTrust } from "./appAttest";
import { CHALLENGE_TTL_MS, challengeIsLive, commitAttestation, issueChallenge } from "./attestStore";
import { sessionSecret, signSession } from "./sessionJwt";

export interface AttestEnv {
  DB: D1Database;
  SESSION_JWT_SECRET?: string;
  APP_ATTEST_ALLOW_DEVELOP?: string;
}

export interface AttestDeps extends AttestTrust {
  db: D1Database;
  /** null when SESSION_JWT_SECRET is absent or too short. */
  secret: string | null;
}

const ROOT_DER = Uint8Array.from(atob(APPLE_APP_ATTEST_ROOT_CA), (c) => c.charCodeAt(0));

export function attestDepsFromEnv(env: AttestEnv): AttestDeps {
  return {
    rootDer: ROOT_DER,
    rootSha256: APPLE_APP_ATTEST_ROOT_CA_SHA256,
    allowDevelop: env.APP_ATTEST_ALLOW_DEVELOP === "1",
    now: () => new Date(),
    db: env.DB,
    secret: sessionSecret(env.SESSION_JWT_SECRET),
  };
}

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });

const INVALID = () => json({ error: "invalid_attestation" }, 400);
const UNAVAILABLE = () => json({ error: "attest_unavailable" }, 503);

const KEY_ID = /^[A-Za-z0-9+/]{43}=$/;
const ATTESTATION = /^(?:[A-Za-z0-9+/]{4})+(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/;
const CHALLENGE = /^[A-Za-z0-9_-]{43}$/;
const BODY_KEYS = ["attestation", "challenge", "device", "keyId"];

const bytesOf = (b64: string) => Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));

function b64url(bytes: Uint8Array): string {
  return btoa(String.fromCharCode(...bytes)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export async function handleAttestChallenge(req: Request, deps: AttestDeps): Promise<Response> {
  if (req.method !== "POST") return json({ error: "POST only" }, 405);
  if (deps.secret === null) return UNAVAILABLE();
  const challenge = b64url(crypto.getRandomValues(new Uint8Array(32)));
  const nowMs = deps.now().getTime();
  try {
    await issueChallenge(deps.db, challenge, nowMs);
  } catch {
    return UNAVAILABLE();
  }
  return json({ challenge, expires_at: new Date(nowMs + CHALLENGE_TTL_MS).toISOString() });
}

export async function handleAttest(req: Request, deps: AttestDeps): Promise<Response> {
  if (req.method !== "POST") return json({ error: "POST only" }, 405);
  if (deps.secret === null) return UNAVAILABLE();
  let body: Record<string, unknown>;
  try {
    const raw: unknown = await req.json();
    if (typeof raw !== "object" || raw === null || Array.isArray(raw)) return INVALID();
    body = raw as Record<string, unknown>;
  } catch {
    return INVALID();
  }
  const { keyId, attestation, challenge, device, appAccountToken } = body;
  if (Object.keys(body).filter((k) => k !== "appAccountToken").sort().join() !== BODY_KEYS.join()) return INVALID();
  if (typeof keyId !== "string" || !KEY_ID.test(keyId) || typeof attestation !== "string" || !ATTESTATION.test(attestation)
    || typeof challenge !== "string" || !CHALLENGE.test(challenge) || typeof device !== "string") return INVALID();
  const sub = device.toLowerCase();
  const act = typeof appAccountToken === "string" ? appAccountToken.toLowerCase() : undefined;
  if (!UUID.test(sub) || ("appAccountToken" in body && (act === undefined || !UUID.test(act)))) return INVALID();

  const nowMs = deps.now().getTime();
  try {
    if (!(await challengeIsLive(deps.db, challenge, nowMs))) return INVALID();
  } catch {
    return UNAVAILABLE();
  }
  let key;
  try {
    key = await verifyAttestation({ keyId: bytesOf(keyId), attestation: bytesOf(attestation), challenge }, deps);
  } catch (e) {
    if (e instanceof AttestRejected) return INVALID();
    throw e;
  }
  const publicKeyHex = Array.from(key.publicKey, (b) => b.toString(16).padStart(2, "0")).join("");
  try {
    if (!(await commitAttestation(deps.db, { keyId, deviceId: sub, publicKeyHex, environment: key.environment, challenge }, nowMs))) {
      return INVALID();
    }
  } catch {
    return UNAVAILABLE();
  }
  const session = await signSession(deps.secret, act === undefined ? { sub } : { sub, act }, nowMs);
  return json({ token: session.token, expires_at: new Date(session.expiresAtMs).toISOString() });
}
