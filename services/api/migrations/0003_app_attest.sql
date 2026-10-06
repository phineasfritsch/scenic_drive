CREATE TABLE IF NOT EXISTS attest_challenges (
  challenge TEXT PRIMARY KEY NOT NULL,
  expires_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS attested_keys (
  key_id TEXT PRIMARY KEY NOT NULL,
  device_id TEXT NOT NULL,
  public_key TEXT NOT NULL,
  environment TEXT NOT NULL CHECK (environment IN ('production', 'development')),
  attested_at INTEGER NOT NULL
);
