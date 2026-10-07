CREATE TABLE IF NOT EXISTS surprise_ledger (
  user_id TEXT NOT NULL,
  place_id TEXT NOT NULL CHECK (length(place_id) BETWEEN 1 AND 19),
  cell TEXT NOT NULL CHECK (length(cell) = 15),
  day TEXT NOT NULL CHECK (length(day) = 10),
  PRIMARY KEY (user_id, place_id, day)
);
CREATE INDEX IF NOT EXISTS surprise_ledger_by_day ON surprise_ledger (day);
