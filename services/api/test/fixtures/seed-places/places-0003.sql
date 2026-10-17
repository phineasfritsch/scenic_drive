INSERT INTO places (id, lat, lon) VALUES
('9223372036854775807', -900000000 / 10000000.0, -1800000000 / 10000000.0)
ON CONFLICT (id) DO UPDATE SET lat = excluded.lat, lon = excluded.lon;
