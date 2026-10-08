---
id: T-0316
title: Road trips name an overnight town per day boundary and 2-4 corridor stops per day - the Worker's planTrip passes the corpus places it already holds into the ScenicKit-parity day splitter
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-08T06:33:22Z
lease_expires_at: 2026-10-08T20:33:22Z
worktree: .worktrees/T-0316
branch: task/T-0316
exclusive: []
touches: [services/api/src/, services/api/test/, services/api/migrations/0009_trip_places.sql, ops/lib/named-tests.json, pins/PINS.yaml]
pins_affected: [P-COST-01, P-PRIV-05]
reviewer: null
depends_on: [T-0268, T-0313]
verify: [ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST: which places the Worker already holds (D1 places table, T-0256 resolver), the plan's rule (overnight = lodging within 15 km of the day boundary; 2-4 corridor POIs/day), and that no new coordinate leaves the device (the server picks from its own corpus)"
  - "planTrip passes the candidate places to the splitter; a full-equality table over {no lodging near a boundary, one, several} and {0, 1, 5 corridor places} through worker.fetch; an itinerary with no lodging says so honestly"
  - "Every route-enumerating table unchanged (no new route); population entries MISSED before and CAUGHT by name after; new PINS.yaml text double-quoted"
---
## Brief

T-0313 owner stillOpen (PR #201): the Worker's planTrip passes no places, so stops are always empty and overnight towns
read "not searched yet" in the app (T-0268). Plan, Road trip: "2-4 corridor POIs/day; overnight town = lodging within
15 km".

## Log
- 2026-10-08T06:32:40Z filed by agent/claude-opus-5 (orchestrator) from T-0313's stillOpen.
- 2026-10-08T06:33:22Z claimed by agent/claude-opus-5; lease until 2026-10-08T20:33:22Z
- 2026-10-08T06:36:50Z MEASURED, then RULINGS before code (agent/claude-opus-5, owner). Read: services/api/src/{trip,tripPlanner,roadTrip,placeResolver,plan,index}.ts, migrations/0001..0008, test/{tripHarness,tripRoute,tripFull,migrationColumns,siwaHarness}.ts, test/mutate/tripMutants.mjs, Sources/ScenicAPIClient/TripResponseDay.swift, queue/done/T-0268 R4, T-0313.
  M1 WHAT THE WORKER HOLDS. D1 has exactly one place table, `places (id TEXT PK, lat REAL, lon REAL)` (migrations/0001_places.sql), read one row at a time by PLACE_QUERY "SELECT lat, lon FROM places WHERE id = ?1" (placeResolver.ts, T-0256 R6) to resolve the destination id. It has NO name, NO kind, NO score, NO lodging flag. No other D1 table, KV namespace or bundled list in services/api/src carries a POI or a lodging (grep places|lodging|tourism|viewpoint over src: only placeResolver, ledger place ids, planRequest/tripRequest id syntax). Nothing in the repo writes the Worker's D1 places either; the ETL writes its OWN SQLite corpus places (place_id, osm_type, osm_id, cls, name, lon_e7, lat_e7) (services/etl/etl/corpuswriter.py), which never reaches the Worker. MEASURED population of usable candidates on the Worker today: 0.
  R1 DISAGREEMENT, Brief vs reality: the title's "the corpus places it already holds" do not exist in a form the splitter can use (RoadTripPlace needs name, kind stop|lodging, integer score, coordinate). RULED: a new server-side table `trip_places (id, name, kind, score, lat, lon)` in services/api/migrations/0009_trip_places.sql, its CHECK constraints the row validation (DB constraints are a permitted anchor, CLAUDE.md): name text of length >= 1, kind IN ('stop','lodging'), score an integer, lat a real in [-90, 90], lon a real in [-180, 180]. touches: gains exactly that one file (edited above, ruled here). Loading it from the ETL corpus is services/etl work outside touches - filed as stillOpen; until it is loaded production searches an EMPTY corpus and every non-last day honestly says no_lodging.
  R2 THE PLAN'S RULE is already the splitter's (roadTrip.ts, parity-held to RoadTrip.swift by Tests/Fixtures/t0268/trips.json): overnight = the NEAREST lodging within OVERNIGHT_RADIUS_METERS 15_000 (inclusive) of the day's end vertex, ties by name, meters rounded; corridor stops = kind stop within CORRIDOR_METERS 5_000 of the route, the top MAX_STOPS_PER_DAY 4 by score in route order. "2-4 a day" has no lower bound the server can honour without inventing stops: a day lists 0-4 real corpus stops, never padded. The splitter is not edited.
  R3 NO NEW COORDINATE LEAVES THE DEVICE. The read is TRIP_PLACES_QUERY "SELECT name, kind, score, lat, lon FROM trip_places" with NO bound parameter: no request value (not the origin, not the destination id) reaches D1 for it, the request whitelist (tripRequest.ts) is unchanged, and router bodies are unchanged (places never reach the router). The answer gains corpus lodging names and metres - server data, no device coordinate. The whole table is read (no bbox): a bbox adds four bounds and their mutants while the splitter filters exactly; CPU over a large corpus is stillOpen (measured rows today: 0).
  R4 THE WIRE. places_searched: true when the read answered, false when it threw (table not migrated, D1 down). overnight on every non-last day: {kind: "lodging", name, meters} | {kind: "no_lodging"} (searched; nothing within 15 km - the honest "no lodging") | {kind: "not_searched"} (the read failed); the last day null as before. The app's decoder (TripResponseDay.swift) reads only overnight.kind as a string, so all three decode; showing the lodging name in the app is Sources/ work outside touches (stillOpen). A failed read DEGRADES (not_searched), never fails the trip. It runs after the closures snapshot and before guardedPlan: KILL, 400, 405, region, missing deps and unknown place never reach it, and it is not an upstream call. TripDeps gains `tripPlaces`; tripDepsFromEnv builds it from env.DB; index.ts and ROUTES are not edited.
  R5 TESTS, red first by name. New test/tripPlaces.test.ts through worker.fetch (src/index.ts default export, the miniflare D1 with every migration applied): the cross product {no lodging near a boundary, one, several} x {0, 1, 5 corridor places} = 9 rows, each the WHOLE answer by full equality to expectedTrip over that variant (overnight and stops written as functions of the variant, hand-placed: lodging on/north of the boundary vertices, so metres are R x dlat), a meta-test that the 9 answers are pairwise distinct (no row ignores a variant), the 15 km bound inside the "several" variant (14_990 m found, 15_010 m not), and the table-missing row (places_searched false, not_searched). The trip_places columns read back exactly (P-PRIV-05, beside the waitlist/ledger rows) and its CHECKs table-tested at every bound (exact accepted, next double outside refused, wrong kind/type refused).
  R6 NO NEW ROUTE: ROUTES, killSwitchRoutes, requestReadSites, configSweep and the index.ts content pin are untouched.
  R7 POPULATION: tripMutants.mjs gains entries on the new code (places not passed, searched always false, lodging read as no_lodging, failure claimed as searched, query widened to a bound parameter is out - none exists); each run --only against the T-0268 test list (MISSED) and again with tripPlaces.test.ts (CAUGHT by name), quoted here; MIN_MUTATIONS raised by the count.
