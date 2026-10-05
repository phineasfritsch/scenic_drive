/**
 * What one verified App Store Server Notification V2 does to the entitlement row (T-0267 R5, R7). Returns the
 * row to write, or null for "acknowledge with no change"; throws JwsRejected for a malformed or unverifiable
 * notification (400, nothing written).
 */
import { JwsRejected, verifyAppleJws, type JwsTrust } from "./appleJws";

/** The app's PRODUCT_BUNDLE_IDENTIFIER (apps/ios). A notification for any other bundle changes nothing (R7). */
export const APP_BUNDLE_ID = "com.phineasfritsch.scenicdrive";

export const ACTIVATES = ["SUBSCRIBED", "DID_RENEW", "OFFER_REDEEMED"];
export const DEACTIVATES = ["EXPIRED", "REFUND", "REVOKE", "GRACE_PERIOD_EXPIRED"];

export interface EntitlementChange {
  originalTransactionId: string;
  appAccountToken: string | null;
  environment: "Production" | "Sandbox";
  productId: string;
  status: "active" | "inactive";
  activeUntil: number | null;
  notificationType: string;
  subtype: string | null;
  signedDate: number;
}

export interface AsnPolicy extends JwsTrust {
  bundleId: string;
  allowSandbox: boolean;
}

function bad(why: string): never {
  throw new JwsRejected(why);
}

function epochMs(value: unknown, what: string): number {
  if (typeof value !== "number" || !Number.isSafeInteger(value) || value < 0) bad(`${what} is not an epoch ms`);
  return value;
}

export async function entitlementChange(payload: Record<string, unknown>, policy: AsnPolicy): Promise<EntitlementChange | null> {
  const type = payload.notificationType;
  if (typeof type !== "string") bad("no notificationType");
  const subtype = typeof payload.subtype === "string" ? payload.subtype : null;
  const signedDate = epochMs(payload.signedDate, "signedDate");
  const grace = type === "DID_FAIL_TO_RENEW" && subtype === "GRACE_PERIOD";
  const status = ACTIVATES.includes(type) || grace ? "active" : DEACTIVATES.includes(type) ? "inactive" : null;
  if (status === null) return null;

  const data = payload.data;
  if (typeof data !== "object" || data === null) bad("no data");
  const { environment, bundleId, signedTransactionInfo, signedRenewalInfo } = data as Record<string, unknown>;
  if (environment !== "Production" && environment !== "Sandbox") bad("unknown environment");
  if (environment === "Sandbox" && !policy.allowSandbox) return null;
  if (bundleId !== policy.bundleId) return null;

  const tx = await verifyAppleJws(signedTransactionInfo, policy);
  const { originalTransactionId, productId, appAccountToken, expiresDate } = tx;
  if (typeof originalTransactionId !== "string" || originalTransactionId.length === 0) bad("no originalTransactionId");
  if (typeof productId !== "string") bad("no productId");
  let activeUntil: number | null = null;
  if (grace) {
    const renewal = await verifyAppleJws(signedRenewalInfo, policy);
    activeUntil = epochMs(renewal.gracePeriodExpiresDate, "gracePeriodExpiresDate");
  } else if (status === "active" && expiresDate !== undefined) {
    activeUntil = epochMs(expiresDate, "expiresDate");
  }
  return {
    originalTransactionId,
    appAccountToken: typeof appAccountToken === "string" ? appAccountToken.toLowerCase() : null,
    environment,
    productId,
    status,
    activeUntil,
    notificationType: type,
    subtype,
    signedDate,
  };
}
