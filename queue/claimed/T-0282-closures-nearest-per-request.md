---
id: T-0282
title: closures nearest-first per request - KV keeps every active full closure (measured), and each driven request sends the <=50 polygons nearest its own corridor instead of a fixed global 50
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-06T15:36:12Z
lease_expires_at: 2026-10-07T03:36:12Z
worktree: .worktrees/T-0282
branch: task/T-0282
exclusive: []
touches: [services/api/, Tests/Fixtures/t0276/, pins/PINS.yaml, ops/lib/named-tests.json]
pins_affected: [P-SAFE-08, P-SAFE-01]
reviewer: null
depends_on: [T-0276, T-0281]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE FIRST on the recorded D7 fixture: active full closures (163 at record time), polygons after buffering, KV value bytes for all of them vs Cloudflare's KV value limit, and the GraphHopper custom-model areas limit actually configured in services/routing (quote both); RULE the stored cap and the per-request selection (distance from each closure to the request's origin/destination segment, or a ruled corridor box) in the Log before code"
  - "the cron stores every active full closure up to the measured ceiling; each driven request (/plan, /loop, /trip legs) selects its nearest <= 50 by the ruled metric, deterministic tie-break; a closure ON the straight corridor is never dropped while a farther one is kept - a table test through ROUTES by full equality of the areas sent; the closures-version still keys every cache; the 'closures dropped' count is reported in the hazard when > 0"
  - "P-SAFE-08's WHAT IT CANNOT SEE line about the global cap is superseded by an APPENDED dated sentence; new tests bound by name under P-SAFE-08; a TS mutation population entry set with a literal floor and the table-rows-as-functions-of-input discipline (rows over an empty set, one closure, and > 50)"
---
## Brief

T-0276 stillOpen 3 / T-0281 WHAT IT CANNOT SEE: the global 50-polygon cap dropped 121 of 163 active full closures on
the recorded LA feed, so a route can be sent through a dropped closure with no hazard. Selecting per request keeps
the ones that matter for that drive.

## Log
- 2026-10-06T15:25:23Z filed by agent/claude-opus-5 (orchestrator) after PR #171 (T-0281) review PASS.
- 2026-10-06T15:36:12Z claimed by agent/claude-opus-5; lease until 2026-10-07T03:36:12Z
- 2026-10-06T15:44:57Z MEASURE (before any predicate). `python Tests/Fixtures/t0276/nearest.py` (new, independent of
  services/api; imports only oracle.py; recomputes in R4's literal plane with + - * / only) over the recorded D7
  response and T-0276's expected.json:
    active closures=163 polygons=173 record_bytes=56691 two_ring=10
    worst case every Full row active: closures=1708 polygons=1785 record_bytes=582603
    santa-monica->pasadena: on_corridor=0 within_1/5/20km=[5, 8, 42] kept=46 polygons=50 dropped=117 farthest_kept_m=24178 nearest_dropped_m=24575
    malibu->downtown: on_corridor=0 within_1/5/20km=[0, 4, 60] kept=46 polygons=50 dropped=117 farthest_kept_m=14968 nearest_dropped_m=15168
    lancaster->long-beach: on_corridor=0 within_1/5/20km=[6, 28, 75] kept=46 polygons=50 dropped=117 farthest_kept_m=9136 nearest_dropped_m=9162
    loop@topanga: on_corridor=0 within_1/5/20km=[0, 0, 25] kept=47 polygons=50 dropped=116 farthest_kept_m=26905 nearest_dropped_m=27067
    loop@newhall: on_corridor=0 within_1/5/20km=[0, 4, 15] kept=46 polygons=50 dropped=117 farthest_kept_m=32976 nearest_dropped_m=33212
  KV value limit, quoted from https://developers.cloudflare.com/kv/platform/limits/ (fetched 2026-10-06):
  "Value size | 25 MiB | 25 MiB" (Free | Paid). GraphHopper areas limit actually configured in services/routing:
  NONE - config.yml sets graph.location, datareader.file, graph.encoded_values, import.osm.ignored_highways,
  custom_models.directory and the two profiles (car_fast, car_scenic; custom_model_files [car_scenic_base.json]); no
  key bounds a request's custom_model areas. The only per-request bound is customModel.ts MAX_CLOSURE_POLYGONS = 50
  (the plan's "<= 50 polygons"), which stays.
- 2026-10-06T15:49:21Z RULINGS (author rule; before code).
  N1 stored cap: CLOSURES_STORED_MAX_POLYGONS = 2000 (literal, closuresStore.ts). Measured: today 173 polygons,
  56691 bytes; the worst case on this feed (every one of 1708 Full rows active) 1785 polygons, 582603 bytes; 2000
  polygons is ~0.65 MB, under 3% of KV's 25 MiB. Above 2000 the cron still fills greedily in R5's order (R5
  unchanged except the cap literal) and counts the rest in stats.dropped. The plan's "<50 KB" is superseded by
  measurement: today's whole set is 56.7 KB and the plan's bound existed only because the whole set was sent.
  N2 reader: readClosures accepts a FeatureCollection of 0..2000 features; every feature still passes
  buildCustomModel's rebuild (each run of 50 is built, so every refusal by name still applies); more than 2000,
  or anything buildCustomModel refuses, is UNAVAILABLE (R7 unchanged).
  N3 metric: squared planar distance in R4's literal plane (110946 m/deg lat, 91961 m/deg lon) from the request's
  corridor - the straight segment origin -> destination (a point when they are equal) - to a polygon: 0 when the
  origin lies inside the ring or the segment properly crosses an edge, else the least of the point-to-segment
  distances among the four endpoints of each (corridor, edge) pair. + - * / only, no sqrt (squared ordering is
  the same), so nearest.py recomputes it bit-identically. A closure is a run of consecutive features sharing a
  string properties.lcs_index (the cron writes one on every feature); a feature without one is its own closure.
  Its distance is the least over its polygons.
  N4 selection: closures sorted by distance, ties by stored position (R5's order); kept is the LONGEST PREFIX of
  that order whose polygons total <= 50 - the first closure that does not fit stops the fill (no greedy skip), so
  every kept closure is no farther than every dropped one and a closure ON the corridor (distance 0) is dropped
  only when > 50 polygons are at distance 0 (then the stored order decides). The kept features are SENT IN STORED
  ORDER; a set of <= 50 polygons is sent unchanged (every earlier test's body is unchanged).
  N5 corridors: /plan's scenic search (origin, destination); /trip's scenic search (origin, destination) and each
  day leg (its start vertex, its end vertex); /loop's round trips (start, start), then the retrace squares merged
  after the selected feed (mergeClosures, feed first, <= 50 - unchanged R8). car_fast and /isochrone unchanged
  (R8). Planners take a picker (from, to) -> set instead of the set.
  N6 hazard: dropped = the MOST closures any one driven request of the answer did not carry. closures_hazard is
  present when the state is not fresh OR dropped > 0; it gains `dropped` only when > 0; a fresh answer with drops
  reads {state: "fresh", version, fetched_at, dropped}. Measured above: on today's feed every driven answer drops
  ~117, so the hazard is present on every driven answer until the feed shrinks - the acceptance's "reported when
  > 0", not noise to suppress.
  N7 cache: the only cache is /isochrone's reach cache; its key keeps the record's closures-version (over the
  whole stored set). The per-request selection is a pure function of (version, corridor) and caches nothing.
  N8 tests: a new test file closuresNearest.test.ts - through ROUTES for /plan, /loop, /trip (search; shipped
  identity is free, R3 of T-0256), legs through handleTrip with paid deps as closuresDriven does; table rows over
  the set variants empty / one / fifty / over 50 (on-corridor closures stored LAST) / a 51-way tie at distance 0 /
  over 50 stale, by full equality of the models' areas and the hazard, with a meta-test that every route's
  expectation differs across variants. Store bounds 2000 accepted / 2001 unavailable through ROUTES. The cap tests
  of closuresFeed.test.ts move to 2000/2001/1999 and the measured-counts test renames (163 kept, 173 polygons,
  0 dropped) - its P-SAFE-08 binding follows the name. oracle.py CAP 50 -> 2000; expected.json regenerated by it.
  N9 mutation population: entries appended to closuresMutants.mjs with subject src/closuresNearest.ts and the new
  test file; MIN_MUTATIONS raised to the new literal population.
- 2026-10-06T16:28:16Z RED FIRST by name, before any src/ change (`npx vitest run test/closuresNearest.test.ts` over the merged-in
  routes of 9a882dd): 11 failed | 14 passed (25), among them "/plan, over 50, the on-corridor ten stored last: every
  model's areas and the hazard equal the variant's selection" (and the same for /loop, /trip; the 51-way tie and
  the stale rows per route), "/plan, 2000 polygons stored: fresh, the 50 nearest sent, 1950 dropped" and "the search
  and legs 3-5 carry Big Sur and the 49 nearest of the origin's 50; legs 1-2 the origin's 50" - each read today as
  closures_hazard unavailable, since the reader refused > 50. Green before the change by design: empty / one / fifty
  rows (the unchanged bodies) and "2001 polygons stored: unavailable" (it was unavailable at 51 already).
  CODE: src/closuresNearest.ts (N3-N6; nearestClosures, closurePicker); closuresStore.ts (N1 cap 2000, N2 chunked
  read, fetchedAt on the snapshot, withClosuresHazard(answer, snapshot, dropped)); lcsFeed capClosures(closures,
  cap = 2000); plan/loop/trip build one picker per request and report picker.dropped(); scenicPlanner,
  tripPlanner (search and every leg) and loopPlanner take ClosuresFor. Tests moved by ruling N8: closuresFeed cap
  rows 50/51/49 -> 2000/2001/1999 and the measured-counts row renamed (163 kept in 173 polygons, 0 dropped);
  closuresCron RECORD stats kept 163 dropped 0; closuresRoutes' over-bound unavailable shape "51 polygons, the set's
  first" -> "2001 polygons, the set's first" (8 rows + its meta name; the P-SAFE-08 names follow, 9 renamed in
  named-tests.json, none dropped); oracle.py CAP 2000 -> `python Tests/Fixtures/t0276/oracle.py`: rows=2808
  full=1708 active=163 refused=0 kept=163 dropped=0 polygons=173 version=lcs-d7-f61d47351b56471d (expected.json
  regenerated by it). GREEN: `npx vitest run` Test Files 46 passed (46), Tests 1469 passed (1469) (d6c95ff).
- 2026-10-06T16:28:16Z MUTATION POPULATION (closuresMutants.mjs, N9): 34 entries appended (subject src/closuresNearest.ts added; tests
  closuresNearest.test.ts and closuresNearestPick.test.ts added) and 11 earlier entries RE-ANCHORED on the code
  they named (their anchors no longer occurred: feed-cap-49, store-geojson-unchecked, store-null-geojson-unchecked,
  store-shape-unchecked-on-empty, plan/loop/trip-no-closures, plan/loop/trip-no-hazard, trip-legs-no-closures);
  MIN_MUTATIONS 95 -> 129 (literal, the population). Run once over the 45 new/re-anchored (owner-approved faster
  verification): `node services/api/test/mutate/closuresMutants.mjs --only=<45 ids>` -> baseline green tests=708,
  `RESULT caught=43 missed=2 trap=0 of 45`. MISSED near-origin-end-only (pointSegment2(d, a, b) dropped: no row had a
  polygon whose nearest point to the corridor was the destination END against an edge interior) -> row "a long bar
  just past either END, its corners kilometres off"; MISSED near-lat-scale (lat scaled by the lon factor: no row
  turned on anisotropy) -> row "metres, not degrees: a square 0.0115 deg east is nearer than one 0.0100 deg north".
  Re-run of the two: `--only=near-origin-end-only,near-lat-scale` -> baseline green tests=710, RESULT caught=2
  missed=0 trap=0 of 2. --prove-floor: the four arms REFUSED ("population 0 is below the floor 129", "population
  128 ...", "subject src/isochrone.ts has no mutation", "subject src/newModule.ts has no mutation"), the real
  population quiet. NOT RUN: the whole 129 (the 84 untouched entries' anchors and tests are unchanged).
- 2026-10-06T16:28:16Z BOUND under P-SAFE-08 (ops/lib/named-tests.json, generated from the vitest JSON report of the two new files):
  closuresNearest.test.ts 26 + closuresNearestPick.test.ts 15 -> 640 names. `python ops/lib/run-named-tests.py
  P-SAFE-08` -> NAMED P-SAFE-08 passed=640/640. RED by one-line src/ mutants, each restored by git checkout, src
  clean after: closuresNearest `> MAX_CLOSURE_POLYGONS) break;` -> `continue;`: exit=1 passed=639/640 ("a two-gate
  closure is one closure: at 49, it does not fit, the fill STOPS, the farther single is not kept" RED);
  closuresStore `if (dropped === 0) return snapshot.hazard` -> `dropped >= 0`: exit=1 passed=629/640 (the over-50,
  tie and stale rows of closuresNearest.test.ts RED). PINS.yaml P-SAFE-08 why_no_test_catches_it: one dated
  passage APPENDED at its end ("T-0282 (2026-10-06) SUPERSEDES the WHAT IT CANNOT SEE sentence above about the
  50-polygon cap: ..."), nothing before it rewritten; read back through ops/lib/pins.py load().
- 2026-10-06T16:37:58Z FINAL (author rule): `git fetch origin` (main checkout) and merged origin/main (82f5d68, telemetry) as the
  last step -> ba39eeb; `git merge-base --is-ancestor origin/main HEAD` true. Gates on the merged head:
  `npx vitest run` Test Files 50 passed (50), Tests 1503 passed (1503); `python ops/lib/run-named-tests.py
  P-SAFE-08` NAMED P-SAFE-08 passed=640/640; `... P-SAFE-01` NAMED P-SAFE-01 passed=15/15;
  `python ops/lib/check-mutate-population.py` "P-PROC-06: every added module is covered or allowlisted; the floor
  of 67 holds"; `bash ops/queue-check` QUEUE OK (275 tasks); every one of the 129 + 1 mutation anchors occurs exactly
  once on the merged head. ops/test not run (orchestrator instruction). wc -l: closuresNearest.ts 115,
  closuresStore.ts 101, lcsFeed.ts 191, closuresCron.ts 73, plan.ts 105, loop.ts 87, trip.ts 98, scenicPlanner.ts
  122, loopPlanner.ts 170, tripPlanner.ts 186, closuresNearest.test.ts 190, closuresNearestPick.test.ts 129,
  closuresMutants.mjs 276, closuresFeed.test.ts 203, closuresRoutes.test.ts 291, nearest.py 127 - all under 300.
  ACCEPTANCE, re-quoted:
  1 MEASURE FIRST - MET: 163 active Full closures, 173 polygons after buffering (10 two-gate), record 56691 bytes
    (worst case on this feed 1785 polygons, 582603 bytes) vs KV's quoted "Value size | 25 MiB"; GraphHopper areas
    limit configured in services/routing: none (config.yml keys quoted), the per-request bound is customModel's 50.
    Stored cap (N1, 2000) and selection (N3-N4: distance to the origin->destination segment, prefix fill, stored
    order tie-break) ruled in the Log at 15:49:21Z before code.
  2 cron + per-request selection - MET: the cron stores every active closure up to 2000 polygons; /plan, /loop and
    /trip's search and day legs each select their nearest <= 50 with a deterministic tie-break; the table test
    through ROUTES (closuresNearest.test.ts: route x {empty, one, fifty, over 50 with the on-corridor ten stored
    last, 51-way tie, over 50 stale}) holds every model's areas and the hazard by full equality - the on-corridor
    ten are always sent while far ones are dropped; the closures-version (over the whole stored set) still keys
    /isochrone's cache, the only cache (N7, closuresRoutes' cache test green); closures_hazard carries dropped
    when > 0, fresh included. Legs through handleTrip with paid deps (no shipped identity reaches paid).
  3 P-SAFE-08 - MET: the WHAT IT CANNOT SEE cap sentence superseded by an APPENDED dated passage; 41 new tests bound
    by name (640 total), seen red by two one-line src mutants; mutation population appended with literal floor
    129, rows over empty / one closure / > 50 with the cross-product meta-test.
  OPEN for follow-up: the corridor is the straight segment, not the returned path (a detour can pass a dropped
    closure; the hazard says so but nothing re-checks the path); a loop's retrace squares are truncated whenever 50
    feed polygons are selected; the whole 129-entry population was not re-run (45 + 2 were).
