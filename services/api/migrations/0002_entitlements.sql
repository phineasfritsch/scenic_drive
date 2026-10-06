CREATE TABLE IF NOT EXISTS entitlements (
  original_transaction_id TEXT PRIMARY KEY NOT NULL,
  app_account_token TEXT,
  environment TEXT NOT NULL CHECK (environment IN ('Production', 'Sandbox')),
  product_id TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('active', 'inactive')),
  active_until INTEGER,
  notification_type TEXT NOT NULL,
  subtype TEXT,
  signed_date INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS entitlements_by_token ON entitlements (app_account_token);
