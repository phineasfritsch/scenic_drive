CREATE TABLE IF NOT EXISTS waitlist (
  cell TEXT PRIMARY KEY NOT NULL CHECK (length(cell) = 15),
  count INTEGER NOT NULL CHECK (count >= 1),
  updated_at TEXT NOT NULL CHECK (length(updated_at) = 10)
);
