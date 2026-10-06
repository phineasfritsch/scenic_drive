/**
 * The D1 tables of App Attest (migrations/0003_app_attest.sql; T-0278 R1). A challenge lives CHALLENGE_TTL_MS and
 * is used once: a verified attestation commits its key and consumes its challenge in ONE batch, the key landing
 * only while the challenge is live and the challenge deleted only when the key landed - so a replay, a race and an
 * already-attested key all change nothing.
 */

export const CHALLENGE_TTL_MS = 300_000;

export const LIVE_CHALLENGE = "SELECT challenge FROM attest_challenges WHERE challenge = ?1 AND expires_at > ?2";
export const COMMIT_KEY = `INSERT OR IGNORE INTO attested_keys (key_id, device_id, public_key, environment, attested_at)
  SELECT ?1, ?2, ?3, ?4, ?5 WHERE EXISTS (SELECT 1 FROM attest_challenges WHERE challenge = ?6 AND expires_at > ?5)`;
export const CONSUME_CHALLENGE = "DELETE FROM attest_challenges WHERE challenge = ?1 AND changes() = 1";

export interface AttestedRow {
  keyId: string;
  deviceId: string;
  publicKeyHex: string;
  environment: "production" | "development";
  challenge: string;
}

/** Challenges one device may be issued per UTC clock hour (T-0280 R5): a session lives an hour, so ~1 an hour plus retries. */
export const ATTEST_CHALLENGES_PER_DEVICE_HOUR = 10;
/** Challenges issued in all per UTC day (T-0280 R5): ~6 D1 row writes a flow keeps a day under D1's 100000. A code change to raise. */
export const ATTEST_CHALLENGES_PER_DAY = 10_000;
export const HOUR_MS = 3_600_000;
export const DAY_MS = 86_400_000;
export const GLOBAL_BUCKET = "global";

export const RESERVE_DEVICE = `INSERT INTO attest_challenge_counts (bucket, slot, issued) SELECT ?1, ?2, 1
  WHERE COALESCE((SELECT issued FROM attest_challenge_counts WHERE bucket = ?1 AND slot = ?2), 0) < ?3
  AND COALESCE((SELECT issued FROM attest_challenge_counts WHERE bucket = '${GLOBAL_BUCKET}' AND slot = ?4), 0) < ?5
  ON CONFLICT (bucket, slot) DO UPDATE SET issued = issued + 1`;
export const RESERVE_GLOBAL = `INSERT INTO attest_challenge_counts (bucket, slot, issued) SELECT '${GLOBAL_BUCKET}', ?1, 1 WHERE changes() = 1
  ON CONFLICT (bucket, slot) DO UPDATE SET issued = issued + 1`;
export const INSERT_CHALLENGE = "INSERT INTO attest_challenges (challenge, expires_at) SELECT ?1, ?2 WHERE changes() = 1";
export const PRUNE_CHALLENGES = `DELETE FROM attest_challenges WHERE expires_at <= ?1
  AND EXISTS (SELECT 1 FROM attest_challenges WHERE challenge = ?2)`;
export const PRUNE_COUNTS = `DELETE FROM attest_challenge_counts
  WHERE ((bucket = '${GLOBAL_BUCKET}' AND slot < ?1) OR (bucket <> '${GLOBAL_BUCKET}' AND slot < ?2))
  AND EXISTS (SELECT 1 FROM attest_challenges WHERE challenge = ?3)`;

/**
 * Reserves the device's and the global count and stores `challenge` live until nowMs + CHALLENGE_TTL_MS, pruning
 * expired challenges and older count slots - ONE batch, every statement guarded by the reservation, so a caller over
 * either limit writes nothing (T-0280 R5). True exactly when the challenge was stored.
 */
export async function issueChallenge(db: D1Database, challenge: string, device: string, nowMs: number): Promise<boolean> {
  const hour = Math.floor(nowMs / HOUR_MS) * HOUR_MS;
  const day = Math.floor(nowMs / DAY_MS) * DAY_MS;
  const results = await db.batch([
    db.prepare(RESERVE_DEVICE).bind(`device:${device}`, hour, ATTEST_CHALLENGES_PER_DEVICE_HOUR, day, ATTEST_CHALLENGES_PER_DAY),
    db.prepare(RESERVE_GLOBAL).bind(day),
    db.prepare(INSERT_CHALLENGE).bind(challenge, nowMs + CHALLENGE_TTL_MS),
    db.prepare(PRUNE_CHALLENGES).bind(nowMs, challenge),
    db.prepare(PRUNE_COUNTS).bind(day, hour, challenge),
  ]);
  return results[2]?.meta.changes === 1;
}

export async function challengeIsLive(db: D1Database, challenge: string, nowMs: number): Promise<boolean> {
  return (await db.prepare(LIVE_CHALLENGE).bind(challenge, nowMs).first()) !== null;
}

/** True exactly when the key landed and its challenge was consumed. */
export async function commitAttestation(db: D1Database, row: AttestedRow, nowMs: number): Promise<boolean> {
  const [inserted] = await db.batch([
    db.prepare(COMMIT_KEY).bind(row.keyId, row.deviceId, row.publicKeyHex, row.environment, nowMs, row.challenge),
    db.prepare(CONSUME_CHALLENGE).bind(row.challenge),
  ]);
  return inserted?.meta.changes === 1;
}

/** The attested key and its stored counter (0 without a sign_counts row: the attestation's), or null (T-0280 R1). */
export const KEY_FOR_ASSERTION = `SELECT k.device_id AS device_id, k.public_key AS public_key, COALESCE(c.sign_count, 0) AS sign_count
  FROM attested_keys k LEFT JOIN attest_sign_counts c ON c.key_id = k.key_id WHERE k.key_id = ?1`;
export const COMMIT_COUNTER = `INSERT INTO attest_sign_counts (key_id, sign_count) SELECT ?1, ?2
  WHERE ?2 > COALESCE((SELECT sign_count FROM attest_sign_counts WHERE key_id = ?1), 0)
  AND EXISTS (SELECT 1 FROM attested_keys WHERE key_id = ?1)
  AND EXISTS (SELECT 1 FROM attest_challenges WHERE challenge = ?3 AND expires_at > ?4)
  ON CONFLICT (key_id) DO UPDATE SET sign_count = excluded.sign_count`;

export interface AssertingKey {
  deviceId: string;
  publicKeyHex: string;
  signCount: number;
}

export async function keyForAssertion(db: D1Database, keyId: string): Promise<AssertingKey | null> {
  const row = await db.prepare(KEY_FOR_ASSERTION).bind(keyId).first<{ device_id: string; public_key: string; sign_count: number }>();
  return row === null ? null : { deviceId: row.device_id, publicKeyHex: row.public_key, signCount: row.sign_count };
}

/** True exactly when `counter` replaced a lower stored counter of the key and the live challenge was consumed (R4). */
export async function commitAssertion(db: D1Database, keyId: string, counter: number, challenge: string, nowMs: number): Promise<boolean> {
  const [stored] = await db.batch([
    db.prepare(COMMIT_COUNTER).bind(keyId, counter, challenge, nowMs),
    db.prepare(CONSUME_CHALLENGE).bind(challenge),
  ]);
  return stored?.meta.changes === 1;
}
