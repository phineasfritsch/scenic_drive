---
id: T-0318
title: The /trip trip_places read stops scanning the whole table before the quota reservation - a quota-refused trip reads no trip_places row, and a served trip reads only the rows near its corridor
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T08:10:54Z
lease_expires_at: 2026-10-17T08:10:54Z
worktree: .worktrees/T-0318
branch: task/T-0318
exclusive: []
touches: [services/api/src/, services/api/test/, services/api/migrations/0010_trip_places_lat.sql, ops/lib/named-tests.json, pins/PINS.yaml]
pins_affected: [P-COST-01, P-PRIV-05]
reviewer: null
depends_on: [T-0316]
verify: [ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST: trip_places row count in production D1 at filing of the claim (0 when T-0316 merged), where handleTrip reads it relative to guardedPlan's quota reservation, and D1's rows-read billing for a full scan versus a bounded read; rule read-after-reservation versus a bbox/corridor-bounded read (or both) before code"
  - "Through worker.fetch: a quota-refused /trip prepares no trip_places statement (recorded D1 statements by full equality), and a served /trip's answer is unchanged by full equality against the T-0316 cross product; any new bound is table-tested at every edge (exact, next double outside) and binds no request value beyond what R3 of T-0316 ruled"
  - "Population entries MISSED before and CAUGHT by name after; no route-enumerating table changes"
  - "A1 (ruled 2026-10-16T08:15:41Z) QUOTA FIRST: through worker.fetch, a /trip refused 429 quota_exhausted records exactly [the destination lookup] as its D1 statements (whole equality) - no trip_places statement - and KILL=1 records none"
  - "A2 THE STATEMENT: a served /trip records exactly [destination lookup, {sql: TRIP_PLACES_QUERY (R2 text), binds: [south, north, west, east]}], whole equality, the binds recomputed in the test by a typed-out oracle of R3 over the shipped road's vertices; every bind has at most one decimal place (R4)"
  - "A3 UNCHANGED: every T-0316 row of test/tripPlaces.test.ts (the 3x3 cross product, the 15 km and 5 km exact/past rows, the tie rows, empty corpus, failed read) passes unchanged through worker.fetch; and over every case of Tests/Fixtures/t0268/trips.json (shared and synthetic) planRoadTrip over the box-filtered places EQUALS planRoadTrip over all places"
  - "A4 EVERY BOUND: through worker.fetch, a row exactly on each of the four box edges is returned by the read and the next double outside each edge is not (rows recorded from the read's result); placesBox table rows at the lat clamps (exact grid -90/90 kept, one step past clamped), the antimeridian fallback (west exactly -180 kept, the next double west of the vertex falls back to [-180, 180]; same east), the polar fallback (a band reaching 90 is the whole longitude range), each whole-box equality"
  - "A5 BILLING (R5): through worker.fetch with migrations 0009 + 0010 applied, the trip's read reports the same meta.rows_read with and without 100 rows outside the box's latitude band"
  - "A6 POPULATION: tripMutants.mjs gains entries on src/tripPlacesBox.ts, the new query, the read's position and migrations/0010 (SUBJECTS gains both files), each MISSED on the base test list and CAUGHT by name after, MIN_MUTATIONS raised by the count; check-mutate-anchors 0 stale; ROUTES and every route-enumerating table unchanged"
---
## Brief

Filed from rv1-t0316 RECORDABLE R-a (PR #203). handleTrip reads the whole trip_places table on every /trip that gets
past the kill switch, the region check and the place lookup - including requests guardedPlan then refuses for quota,
because the read runs before guardedPlan. D1 bills per row read, so once the ETL loader (T-0316 stillOpen 1) fills
the table, every quota-refused trip scans the whole corpus. Measured 0 rows when filed, so this is a follow-up, not a
P-COST fail-open today. It belongs with (or before) the loader.

## Log
- 2026-10-08T09:05:40Z filed by agent/claude-opus-5 (T-0316 owner) from rv1-t0316 R-a.
- 2026-10-16T08:10:54Z claimed by agent/claude-opus-5; lease until 2026-10-17T08:10:54Z
- 2026-10-16T08:15:41Z MEASURED, then RULINGS before code (agent/claude-opus-5, owner). Read: services/api/src/{trip,tripPlaces,tripPlanner,roadTrip,routePath,index}.ts, migrations/0009_trip_places.sql, test/{tripPlaces,roadTripParity}.test.ts, test/mutate/tripMutants.mjs, queue/done/T-0316 R3/R4.
  M1 ORDER (trip.ts handleTrip): killSwitch (l.70) -> method -> body -> region (l.83) -> deps -> resolvePlace (l.88) -> identify (l.94) -> closures snapshot (l.96) -> `places = await deps.tripPlaces()` (l.100, unbound, whole table) -> guardedPlan (l.106), which reads and RESERVES the quota. So every quota-refused trip past the place lookup scans trip_places.
  M2 ROWS: production D1 not re-measured - this session may not touch Cloudflare resources; nothing in the repo writes trip_places outside test/tripPlaces.test.ts (grep "INTO trip_places" over *.py/*.ts/*.sql/*.mjs), so the loader has not landed and the count is still the T-0316 0. Schema (0009): id TEXT PK, name, kind, score INTEGER, lat REAL, lon REAL, CHECKs; NO index but the PK's.
  M3 USE: planTrip's splitOf feeds planRoadTrip(edges, places); a stop counts only within CORRIDOR_METERS 5_000 of its nearest vertex, a lodging only within OVERNIGHT_RADIUS_METERS 15_000 of a boundary vertex; vertices = [edges[0].start, ...edges.map(e => e.end)]. A row farther than 15 km from every vertex cannot change the answer. splitOf runs on the chosen path and at most once more on a closure re-request.
  M4 BILLING, measured in miniflare (meta.rows_read, a throwaway probe test, deleted): 200 rows; "WHERE lat >= ?1 AND lat <= ?2 AND lon >= ?3 AND lon <= ?4" with no index -> rows_read 200 (EXPLAIN QUERY PLAN "SCAN trip_places"), the unbound read 200; after "CREATE INDEX trip_places_lat ON trip_places (lat)" the same bounded read -> rows_read 2 for 1 row (EXPLAIN "SEARCH trip_places USING INDEX trip_places_lat (lat>? AND lat<?)"). A box over the existing columns is expressible, but bills the full scan without an index.
  R1 BOTH: the read moves AFTER the reservation and is bounded. It moves into planTrip (inside guardedPlan's callback): splitOf reads the box of the path it splits. KILL, 400, 405, region, missing deps, unknown place, session rejected, quota refused and a router failure before the split never reach it.
  R2 THE SQL: TRIP_PLACES_QUERY = "SELECT name, kind, score, lat, lon FROM trip_places WHERE lat >= ?1 AND lat <= ?2 AND lon >= ?3 AND lon <= ?4", bound (south, north, west, east). NO LIMIT: a LIMIT can drop a row that is a stop or the nearest lodging and change the answer; the box is the bound.
  R3 THE BOX (new src/tripPlacesBox.ts, placesBox(vertices)): pad PLACES_PAD_METERS 16_000 = the larger radius (15 km) + 1 km for float rounding. Lat pad = pad / R in degrees (great-circle distance >= R x |dlat|); south/north = min/max vertex lat -/+ it, rounded OUTWARD to a 0.1 degree grid (floor/ceil of x10, /10), clamped to [-90, 90]. Lon pad = 2 asin(sin(pad / 2R) / cos(phi_max)), phi_max = max(-south, north) (haversine: cos phi1 cos phi2 sin^2(dlon/2) <= sin^2(d/2R), and both cosines >= cos phi_max), west/east = min/max vertex lon -/+ it, outward on the grid. When that ratio is not < 1 (only a band reaching 90) or west < -180 or east > 180, the lon range is the whole [-180, 180]. R is roadTrip's EARTH_RADIUS_METERS. Router points are JSON numbers (never NaN/inf, routePath.ts position()); an out-of-range lat clamps, an out-of-range lon falls back to full width.
  R4 DISAGREEMENT, T-0316 R3 ("no bound parameter, no request value reaches D1") vs this Brief (a corridor-bounded read). RULED: the binds are the ROUTE's box, padded >= 16 km and rounded outward to 0.1 degree - at most one decimal place, coarser than the 2-dp coordinate the server already holds (CLAUDE.md invariant) - and stay in our own D1; the request whitelist and router bodies are unchanged. A2 asserts the one-decimal property on every bind.
  R5 DISAGREEMENT, the Brief's "existing columns" vs M4. RULED: services/api/migrations/0010_trip_places_lat.sql "CREATE INDEX IF NOT EXISTS trip_places_lat ON trip_places (lat);" (touches amended above). Applying it to production D1 is owner ops (stillOpen); unapplied, the read is still exact, only unindexed. The index does not change the answer: the splitter breaks every tie by name (T-0316 B2), not by read order.
  R6 FAILURE: a read that throws gives null for that split (not_searched, places_searched false), as T-0316 R4; places_searched reports the split that ships.
  R7 TESTS red first by name: new test/tripPlacesBox.test.ts (A1, A2, A4, A5 through worker.fetch; A3's fixture equality; A4's placesBox table); test/tripPlaces.test.ts's P-PRIV-05 statement test renamed to the bounded read and its migrations gain 0010; named-tests.json follows the rename and gains A1 (P-COST-01) and A2 (P-PRIV-05). R8 NO NEW ROUTE: ROUTES, index.ts and every enumerating table untouched.
