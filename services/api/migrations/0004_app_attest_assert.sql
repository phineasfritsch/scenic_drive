CREATE TABLE IF NOT EXISTS attest_sign_counts (
  key_id TEXT PRIMARY KEY NOT NULL,
  sign_count INTEGER NOT NULL CHECK (sign_count > 0)
);
CREATE TABLE IF NOT EXISTS attest_challenge_counts (
  bucket TEXT NOT NULL,
  slot INTEGER NOT NULL,
  issued INTEGER NOT NULL CHECK (issued > 0),
  PRIMARY KEY (bucket, slot)
);
