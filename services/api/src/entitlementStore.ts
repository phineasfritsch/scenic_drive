/**
 * The D1 entitlements table (migrations/0002_entitlements.sql; T-0267 R5, R6, R8). One row per
 * originalTransactionId. A write lands only when its signedDate is strictly newer than the stored one, in ONE
 * statement, so a replayed or out-of-order notification never regresses state and two deliveries cannot race.
 */
import type { EntitlementChange } from "./asnNotification";

export const UPSERT_ENTITLEMENT = `INSERT INTO entitlements (original_transaction_id, app_account_token, environment, product_id,
  status, active_until, notification_type, subtype, signed_date) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9)
  ON CONFLICT(original_transaction_id) DO UPDATE SET app_account_token = excluded.app_account_token,
  environment = excluded.environment, product_id = excluded.product_id, status = excluded.status,
  active_until = excluded.active_until, notification_type = excluded.notification_type, subtype = excluded.subtype,
  signed_date = excluded.signed_date WHERE excluded.signed_date > entitlements.signed_date`;

export const ENTITLEMENTS_FOR_TOKEN = "SELECT status, active_until FROM entitlements WHERE app_account_token = ?1";

export async function applyEntitlement(db: D1Database, c: EntitlementChange): Promise<void> {
  await db.prepare(UPSERT_ENTITLEMENT).bind(c.originalTransactionId, c.appAccountToken, c.environment, c.productId,
    c.status, c.activeUntil, c.notificationType, c.subtype, c.signedDate).run();
}

export interface EntitlementAnswer {
  status: "active" | "inactive" | "none";
  active_until: number | null;
}

/** active iff some row for the token is active and unexpired at `nowMs`; none iff no row names the token. */
export async function readEntitlement(db: D1Database, token: string, nowMs: number): Promise<EntitlementAnswer> {
  const { results } = await db.prepare(ENTITLEMENTS_FOR_TOKEN).bind(token)
    .all<{ status: string; active_until: number | null }>();
  if (results.length === 0) return { status: "none", active_until: null };
  const live = results.filter((r) => r.status === "active" && (r.active_until === null || nowMs < r.active_until));
  if (live.length === 0) return { status: "inactive", active_until: null };
  const open = live.some((r) => r.active_until === null);
  return { status: "active", active_until: open ? null : Math.max(...live.map((r) => r.active_until as number)) };
}
