CREATE TABLE IF NOT EXISTS waitlist_seen (
  tag TEXT PRIMARY KEY NOT NULL CHECK (length(tag) = 64),
  day TEXT NOT NULL CHECK (length(day) = 10)
);
