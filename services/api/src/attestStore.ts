/**
 * The D1 tables of App Attest (migrations/0003_app_attest.sql; T-0278 R1). A challenge lives CHALLENGE_TTL_MS and
 * is used once: a verified attestation commits its key and consumes its challenge in ONE batch, the key landing
 * only while the challenge is live and the challenge deleted only when the key landed - so a replay, a race and an
 * already-attested key all change nothing.
 */

export const CHALLENGE_TTL_MS = 300_000;

export const PRUNE_CHALLENGES = "DELETE FROM attest_challenges WHERE expires_at <= ?1";
export const INSERT_CHALLENGE = "INSERT INTO attest_challenges (challenge, expires_at) VALUES (?1, ?2)";
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

/** Stores `challenge` live until nowMs + CHALLENGE_TTL_MS, pruning the expired ones in the same batch. */
export async function issueChallenge(db: D1Database, challenge: string, nowMs: number): Promise<void> {
  await db.batch([
    db.prepare(PRUNE_CHALLENGES).bind(nowMs),
    db.prepare(INSERT_CHALLENGE).bind(challenge, nowMs + CHALLENGE_TTL_MS),
  ]);
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
