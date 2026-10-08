CREATE TABLE IF NOT EXISTS trip_places (
  id TEXT PRIMARY KEY NOT NULL,
  name TEXT NOT NULL CHECK (typeof(name) = 'text' AND length(name) >= 1),
  kind TEXT NOT NULL CHECK (kind IN ('stop', 'lodging')),
  score INTEGER NOT NULL CHECK (typeof(score) = 'integer'),
  lat REAL NOT NULL CHECK (lat >= -90 AND lat <= 90),
  lon REAL NOT NULL CHECK (lon >= -180 AND lon <= 180)
);
