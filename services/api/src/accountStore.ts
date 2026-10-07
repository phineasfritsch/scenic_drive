/**
 * The apple_accounts table (migrations/0005_apple_accounts.sql; T-0287 R6) and account deletion (R7). A binding is
 * keyed by the install UUID; a rebinding replaces it, keeping the stored refresh token only when the same Apple user
 * rebinds without a new one. Deletion is ONE batch over every user-keyed row of every D1 table: the user's devices are
 * the session device plus every device bound to the user's Apple subs (?1 the device, ?2 the session's apple claim or
 * NULL), and the entitlements are the session's account token's.
 */

export const BIND_APPLE = `INSERT INTO apple_accounts (device_id, apple_sub, refresh_token, bound_at) VALUES (?1, ?2, ?3, ?4)
  ON CONFLICT (device_id) DO UPDATE SET refresh_token = COALESCE(excluded.refresh_token,
  CASE WHEN apple_accounts.apple_sub = excluded.apple_sub THEN apple_accounts.refresh_token END),
  apple_sub = excluded.apple_sub, bound_at = excluded.bound_at`;

const USER_SUBS = "SELECT apple_sub FROM apple_accounts WHERE device_id = ?1 UNION SELECT ?2 WHERE ?2 IS NOT NULL";
const USER_DEVICES = `SELECT ?1 AS device UNION SELECT device_id FROM apple_accounts WHERE apple_sub IN (${USER_SUBS})`;

/** Every binding of the user's subs - the device's own binding among them, its sub being one of USER_SUBS. */
export const USER_BINDINGS = `SELECT device_id, apple_sub, refresh_token FROM apple_accounts
  WHERE apple_sub IN (${USER_SUBS}) ORDER BY device_id`;
export const DELETE_SIGN_COUNTS = `DELETE FROM attest_sign_counts WHERE key_id IN
  (SELECT key_id FROM attested_keys WHERE device_id IN (SELECT device FROM (${USER_DEVICES})))`;
export const DELETE_KEYS = `DELETE FROM attested_keys WHERE device_id IN (SELECT device FROM (${USER_DEVICES}))`;
export const DELETE_CHALLENGE_COUNTS = `DELETE FROM attest_challenge_counts WHERE bucket IN
  (SELECT 'device:' || device FROM (${USER_DEVICES}))`;
export const DELETE_ENTITLEMENTS = "DELETE FROM entitlements WHERE app_account_token = ?1";
/** T-0302 R8: every Surprise ledger row of every one of the user's devices. */
export const DELETE_LEDGER = `DELETE FROM surprise_ledger WHERE user_id IN (SELECT device FROM (${USER_DEVICES}))`;
export const DELETE_BINDINGS = `DELETE FROM apple_accounts WHERE apple_sub IN (${USER_SUBS})`;

export interface AppleBinding {
  deviceId: string;
  appleSub: string;
  refreshToken: string | null;
}

export async function bindApple(db: D1Database, deviceId: string, appleSub: string, refreshToken: string | null, nowMs: number): Promise<void> {
  await db.prepare(BIND_APPLE).bind(deviceId, appleSub, refreshToken, nowMs).run();
}

export interface AccountUser {
  deviceId: string;
  /** The session's apple claim, when it carries one. */
  appleSub: string | null;
  /** The session's appAccountToken, when it carries one. */
  accountToken: string | null;
}

export async function userBindings(db: D1Database, user: AccountUser): Promise<AppleBinding[]> {
  const { results } = await db.prepare(USER_BINDINGS).bind(user.deviceId, user.appleSub)
    .all<{ device_id: string; apple_sub: string; refresh_token: string | null }>();
  return results.map((r) => ({ deviceId: r.device_id, appleSub: r.apple_sub, refreshToken: r.refresh_token }));
}

/** Deletes every row of the user in ONE batch; apple_accounts last, since every other statement reads it. */
export async function deleteUser(db: D1Database, user: AccountUser): Promise<void> {
  await db.batch([
    db.prepare(DELETE_SIGN_COUNTS).bind(user.deviceId, user.appleSub),
    db.prepare(DELETE_KEYS).bind(user.deviceId, user.appleSub),
    db.prepare(DELETE_CHALLENGE_COUNTS).bind(user.deviceId, user.appleSub),
    db.prepare(DELETE_ENTITLEMENTS).bind(user.accountToken),
    db.prepare(DELETE_LEDGER).bind(user.deviceId, user.appleSub),
    db.prepare(DELETE_BINDINGS).bind(user.deviceId, user.appleSub),
  ]);
}
