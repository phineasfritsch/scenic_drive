/**
 * POST /asn (App Store Server Notifications V2) and GET /entitlement (T-0267). /asn verifies the signedPayload
 * chain to the pinned Apple root, then writes at most one entitlement row; any defect is 400 with nothing
 * written. /entitlement answers the state for the purchase id the device names in x-scenic-account-token (R8).
 */
import { APPLE_ROOT_CA_G3_SHA256, JwsRejected, verifyAppleJws } from "./appleJws";
import { APP_BUNDLE_ID, entitlementChange, type AsnPolicy } from "./asnNotification";
import { applyEntitlement, readEntitlement } from "./entitlementStore";

/** The device's appAccountToken: the random purchase id the app keeps in iCloud Keychain (R8). */
export const ACCOUNT_TOKEN_HEADER = "x-scenic-account-token";
export const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;

export interface AsnEnv {
  DB: D1Database;
  /** "1" applies Sandbox notifications too (R7); unset in wrangler.jsonc, so production ignores sandbox. */
  ASN_ALLOW_SANDBOX?: string;
}

export interface AsnDeps extends AsnPolicy {
  db: D1Database;
}

export function asnDepsFromEnv(env: AsnEnv): AsnDeps {
  return {
    rootSha256: APPLE_ROOT_CA_G3_SHA256,
    now: () => new Date(),
    bundleId: APP_BUNDLE_ID,
    allowSandbox: env.ASN_ALLOW_SANDBOX === "1",
    db: env.DB,
  };
}

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" },
  });

const INVALID = () => json({ error: "invalid_notification" }, 400);

export async function handleAsn(req: Request, deps: AsnDeps): Promise<Response> {
  if (req.method !== "POST") return json({ error: "POST only" }, 405);
  let change;
  try {
    let body: unknown;
    try {
      body = await req.json();
    } catch {
      return INVALID();
    }
    const signed = typeof body === "object" && body !== null ? (body as Record<string, unknown>).signedPayload : undefined;
    change = await entitlementChange(await verifyAppleJws(signed, deps), deps);
  } catch (e) {
    if (e instanceof JwsRejected) return INVALID();
    throw e;
  }
  if (change === null) return json({ received: true });
  try {
    await applyEntitlement(deps.db, change);
  } catch {
    return json({ error: "entitlement_unavailable" }, 503);
  }
  return json({ received: true });
}

export async function handleEntitlement(req: Request, deps: AsnDeps): Promise<Response> {
  if (req.method !== "GET") return json({ error: "GET only" }, 405);
  const token = (req.headers.get(ACCOUNT_TOKEN_HEADER) ?? "").toLowerCase();
  if (!UUID.test(token)) return json({ error: "invalid_request" }, 400);
  try {
    return json(await readEntitlement(deps.db, token, deps.now().getTime()));
  } catch {
    return json({ error: "entitlement_unavailable" }, 503);
  }
}
