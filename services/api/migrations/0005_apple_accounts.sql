CREATE TABLE IF NOT EXISTS apple_accounts (
  device_id TEXT PRIMARY KEY NOT NULL,
  apple_sub TEXT NOT NULL,
  refresh_token TEXT,
  bound_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS apple_accounts_by_sub ON apple_accounts (apple_sub);
