---
id: T-0340
title: The /trip and /loop answers carry the route's hazard runs, and the trip and loop cards render them from HazardCopy - today only /plan and /reroute report surface and road_access runs
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-09T19:11:58Z
lease_expires_at: 2026-10-10T05:11:58Z
worktree: .worktrees/T-0340
branch: task/T-0340
exclusive: []
touches: [services/api/src/, services/api/test/, Sources/ScenicAPIClient/, Sources/ScenicKit/, Tests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/check-safety-disclaimer-pinned, ops/lib/check-hazard-copy-sites.txt, ops/mutate/, queue/]
pins_affected: [P-SAFE-02]
reviewer: agent/rv3-t0340
depends_on: [T-0339]
verify: [ops/test, ops/check-pins]
acceptance:
  - "A1 WORKER /trip WHOLE (full equality, through handleTrip): over view {preview, full} x road hazards {none, MIX} (MIX = a surface run crossing the day-1/day-2 boundary, a road_access run inside one day, a run on the route's first edge, a run on its last edge, an upper-cased value, and whitelisted asphalt / yes / missing runs), the 200 EQUALS the harness oracle expectedTrip with each day's hazards recomputed in the test by R1's rule written out independently of src/ (preview: the chosen route's runs clipped to the day's point span, indices into route.coordinates; full: the leg's own runs, indices into leg.coordinates), and every router request's details EQUAL [time, distance, scenic_score, surface, road_access]. Test: 'every trip day carries its own hazard runs, whole'. AND over every planner path whose shipped geometry differs from the first-requested one {preview: a stored closure crosses the chosen route and its re-request ships; preview: that re-request refused, the crossing route stays; full: a stored closure crosses the day-2 leg and its re-request ships; full: that re-request refused, the crossing leg stays}, each router answer carrying its own hand-written runs, the 200's {status, route.coordinates, every day's leg coordinates, every day's hazards} EQUAL {200, the SHIPPED path's coordinates, the shipped path's runs written out by hand}; a meta-check asserts every row ships one path whose runs differ from every other answer's in that row. Every re-request answer tiles its runs differently from the crossing answer (a different point count AND time/distance/scenic_score runs spanning several segments), and the meta-check also asserts each row's shipped answer's point count and vertex->point map differ from every other answer's in that row (rv2). Test: 'the trip's day hazards are the shipped path's runs'. STRUCTURE (rv2): planTrip binds the shipped route and each shipped leg once; the pre-swap paths (measuredChosen, legPath) are out of scope of the route coordinates, pointOf and hazard code."
  - "A2 WORKER /loop WHOLE (through handleLoop): over road hazards {none, MIX'} (MIX' = surface and road_access runs incl. an upper-cased value and whitelisted asphalt / yes / missing), the 200's hazards EQUAL the list recomputed in the test, and the request still sends ROUTE_DETAILS. Test: 'the loop carries its hazard runs, whole'. AND over every planner path to a shipped loop {re-seed after a retrace-dirty first attempt, third re-roll after two dull loops, retrace-square attempt after two dirty loops, closure re-request shipped, closure re-request dull so the first loop stays} with a different run set per attempt, the 200's {status, attempts, route.coordinates, hazards} EQUAL {200, attempts, the SHIPPED attempt's coordinates, the shipped attempt's runs written out by hand}; a meta-check asserts every row ships one attempt whose runs differ from every other attempt's. Test: 'the 200's hazards are the shipped attempt's runs'."
  - "A3 SWIFT THROUGH THE SHIPPING ENTRY POINTS: over {trip preview, trip full, loop} x {hazards empty, hazards full (a known row, a kind fallback, an unknown kind; on two trip days)}, a 200 sent through TripClient.trip -> ClientTripPlanner.itinerary and LoopClient.loop -> ClientLoopPlanner.outcome reads HazardCopy.lines(for:) EQUAL to a list written out in the test (R5's lines as literal strings, day order then run order, one line per run). Test: 'trip and loop answers read their hazard lines, whole'."
  - "A4 FAIL-CLOSED ON EVERY FIELD (rows as functions of input): over {trip preview day, trip full day, loop} x base {hazards empty, hazards full} x {hazards removed, null, number, string, object; an element that is not an object; kind removed / number / null; value removed / number / null; from_index removed / string / 1.5; to_index removed / string / null}, the client answers unexpectedResponse (R3) - never an itinerary or preview; a meta-check asserts every malformed body differs from its base and every base decodes. Test: 'a trip or loop whose hazards cannot be read is refused'."
  - "A5 RED FIRST BY NAME: A1-A4's named tests land against the shipped code (no Worker hazards, readers that ignore the key, lines(for:) closure-only) and the run is quoted with each named test failing; then the code lands and they are green."
  - "A6 CARDS RENDER ONLY HAZARDCOPY: TripItineraryCard and LoopPreviewCard are unchanged (they already render HazardCopy.lines(for:)); check-hazard-copy-sites.txt approves exactly the new fixture sites; bare check-hazard-copy-sites and check-safety-disclaimer pass with the touched digests re-approved."
  - "A7 SHOTS LOOKED AT: PlanRehearsalFixtures puts a gravel run on trip day 2 and a destination run on the loop; ios-compile and ios-screenshot success on the last commit touching apps/ios or Sources, plan-trip and plan-loop shots looked at and quoted."
  - "A8 POPULATION: tripMutants.mjs and loopMutants.mjs gain mutants over the new Worker code (details dropped, day clip off by one / unclipped / wrong path, loop hazards dropped) and hazardcopy_mutations.py over the new lines (day runs dropped, prefix lost, loop runs dropped), each CAUGHT by a named test; MIN floors raised to the shipped counts; stale anchors re-pointed."
  - "A9 GATES: touched vitest files and swift suites green; bare check-safety-disclaimer, check-hazard-copy-sites; check-mutate-population, check-line-cap, check-pins-yaml, queue-check; origin/main fetched and merged last."
---
## Brief

T-0339 M2 (measured at bdb77ca6): trip.ts, loop.ts, tripPlanner.ts and loopPlanner.ts never call `hazardsOf`, and
TripResponse / TripResponseDay / LoopResponse decode no hazards - so a trip or loop over a destination-only or gravel
stretch tells the driver nothing, while the same stretch on /plan does. MEASURE FIRST (which router paths the trip
days and the loop are built from, whether their details already carry surface / road_access), then the acceptance:
every day / the loop carries its runs, the readers decode them fail-closed, and TripItineraryCard / LoopPreviewCard
render them through HazardCopy (T-0339's closed table), never a raw key. Worker PRs conflict on the enumerating
tables - one at a time.

## Log
- 2026-10-09T08:33:30Z filed by agent/claude-opus-5 from T-0339 R4.
- 2026-10-09T19:11:58Z claimed by agent/claude-opus-5; lease until 2026-10-10T05:11:58Z
- 2026-10-09T19:17:08Z MEASURED (at 6c6dfc81, before any code).
  - M1 /trip DETAILS. tripPlanner.ts `TRIP_DETAILS = ["time", "distance", "scenic_score"]` is the details list of
    EVERY trip router request (fastest, the 6 lambda evaluations, any closure re-request, each full-view leg): the
    trip's paths carry no surface or road_access runs, so the Worker cannot compute hazards without asking for them.
    The days are cut from the chosen path's time runs (edgesOf): day d spans edge vertices [start_vertex,
    end_vertex], vertex v at route point 0 for v = 0 and time[v-1].to after (the runs tile [0, last], edgesOf
    refuses otherwise). A PREVIEW day carries no path of its own (leg null) - its geometry is a span of
    route.coordinates; a FULL day's leg is a separate car_scenic A->B request whose coordinates ship as
    leg.coordinates (after the closure guard `returned`).
  - M2 /loop DETAILS. loopPlanner.ts roundTrip sends `details: ROUTE_DETAILS` = [scenic_score, road_class,
    osm_way_id, surface, road_access, time] - the loop path already carries both hazard details; LoopResult just
    never calls hazardsOf (hazards.ts: lowercases, drops PAVED_SURFACES / OPEN_ACCESS, emits {kind, value,
    from_index, to_index}).
  - M3 SWIFT. TripResponseDay and LoopResponse decode no hazards; PlanResponse decodes `hazards` as a REQUIRED
    [PlanHazard] (a malformed or absent array fails the decode, TripReplyReader / PlanReplyReader then answer
    unexpectedResponse). TripItineraryDay and LoopPreview carry no runs; HazardCopy.lines(for: TripItinerary) and
    lines(for: LoopPreview) return the closure lines only (T-0341 R2).
  - M4 CARDS. TripItineraryCard:28 and LoopPreviewCard:32 already render `ForEach(HazardCopy.lines(for: ...))` - the
    only hazard text on either card; PlanRehearsalFixtures gives trip a stale and loop an unavailable closures set,
    no runs.
  - M5 PINS. P-SAFE-02 has no row in pins/PINS.yaml or ops/lib/named-tests.json (T-0339 R5 stands).
- 2026-10-09T19:17:08Z RULINGS.
  - R1 /trip: TRIP_DETAILS gains HAZARD_DETAILS (every trip request; the gate reads the model, not the details).
    Each TripDayResult carries `hazards: Hazard[]`. FULL: hazardsOf(the leg that ships), indices into
    leg.coordinates. PREVIEW: hazardsOf(the chosen route), each run kept iff from < dayEnd and to > dayStart (the
    day's point span from M1), clipped to [max(from, dayStart), min(to, dayEnd)], indices into route.coordinates -
    a run across a night is told on both days. No top-level trip field: the days carry every run.
  - R2 /loop: LoopResult carries `hazards: hazardsOf(chosen)` (M2: no request change).
  - R3 READERS FAIL CLOSED the way /plan does: TripResponseDay.hazards and LoopResponse.hazards are REQUIRED
    [PlanHazard]; absent, null, mistyped or any malformed element refuses the whole answer (unexpectedResponse). A
    trip whose hazards cannot be read is never shown as hazard-free. Consequence: the Worker must deploy before an
    app build carrying this reader (owner's deploy; recorded, not done here).
  - R4 MODEL: TripItineraryDay.hazards and LoopPreview.hazards ([PlanHazardRun]), one-to-one in ClientTripPlanner /
    ClientLoopPlanner, as ClientPlanner does.
  - R5 COPY: lines(for: LoopPreview) = closure lines + one line(for: run) per run in order (the plan strip's
    shape). lines(for: TripItinerary) = closure lines, then per day in order, per run in order, "Day N · " +
    line(for: run) - a trip's driver needs which day; the prefix spells no wire key. Nothing merged or dropped.
  - R6 P-SAFE-02 stays held by name in tests (one line per run, in order); no PINS.yaml edit (M5).
  - R7 Cards are not edited (M4); only fixtures gain runs for the shots.
- 2026-10-09T20:50:56Z ACCEPTANCE RUN (origin/main fetched and merged last: 65fa0e74, a merge of fcf657f9 and
  origin/main b048be30 - queue files and the T-0350 screenshot workflow only, no file this task touches).
  - A5 RED BY NAME. Worker (tests at 91b20fc5's test files over the shipped planners): `npx vitest run
    test/tripLoopHazards.test.ts` "Tests 2 failed (2)": "every trip day carries its own hazard runs, whole" and "the
    loop carries its hazard runs, whole", each AssertionError. Swift (13737639, the stub - models carry runs,
    readers ignore them, lines(for:) closure-only): `swift test --filter TripLoopHazardsTests` "Test run with 2
    tests in 1 suite failed ... with 114 issues": "trip and loop answers read their hazard lines, whole" 6 issues,
    "a trip or loop whose hazards cannot be read is refused" 108 issues (3 answers x 2 bases x 18 rows).
  - A1, A2 GREEN: both named Worker tests pass; touched vitest files on 65fa0e74 "Test Files 8 passed (8), Tests
    139 passed (139)" (tripLoopHazards, tripFull, tripRoute, loopShape, loopHonest, tripHonest,
    closuresCrossingTrip, accountTier). The whole Worker suite at 91b20fc5: 2570 passed; its only reds were the
    whole-answer tests this task updated (hazards: [] added, the trip details literal extended) and two
    timeouts on this loaded box (configAnswerPath, waitlistDedupe), each green alone.
  - A3, A4 GREEN: touched suites on 65fa0e74 "Test run with 99 tests in 19 suites passed"; the whole root suite at
    00db8f26 "Test run with 774 tests in 150 suites passed".
  - A6: cards unchanged (git diff origin/main -- TripItineraryCard.swift LoopPreviewCard.swift: empty).
    check-hazard-copy-sites seen RED with the fixtures before the whitelist: exit=1 "FAILED - 3 unapproved, 1
    missing of 12 approved"; then "ok - 14 sites, every one approved, in 5 files"; --prove-red "PROVE-RED OK: 13
    of 13 rows red by name, control 0". Bare check-safety-disclaimer exit=0 with the 8 linked Sources rows and the
    pinned PlanRehearsalFixtures row re-approved (each sha the reviewed file's).
  - A7 SHOTS: ios-compile 37983563080 success, ios-screenshot 37983569122 success, both on 00db8f26 (the last commit
    touching apps/ios or Sources). LOOKED AT: plan-trip-light - under the stale-closures line, a warning glyph and
    "Day 2 · Gravel on part of this route - check it suits your car"; plan-loop-dark - under "Road closures could
    not be checked ...", "Local traffic only on part of this route - you may not be allowed through". No raw key.
  - A8 POPULATION. tripMutants.mjs --only (8 new / re-pointed): "RESULT caught=8 missed=0 trap=0 of 8", floor
    "mutations=100 (floor 100)"; loopMutants.mjs --only loop-hazards-dropped "caught=1 ... of 1", "mutations=44
    (floor 44)"; both --prove-floor refuse their arms. hazardcopy.py --only 45-53: first run MISSED 9 of 9 - the
    runner's FILTER named only the T-0339/T-0341 suites (fcf657f9 adds TripLoopHazardsTests); re-run "MUTATE OK
    caught=9/9", each by its named killer; --prove-floor "FLOOR PROOF OK: 7 of 7 arms refused".
  - A9: check-mutate-population exit 0 ("the floor of 147 holds"); check-line-cap did not finish within 25 min on
    this box (another session's check-line-cap was running beside it) - left to PR CI's core job.
- 2026-10-09T21:54:02Z agent/claude-opus-5 - PRE-REVIEW MUTANT 2 (BLOCKING) CLOSED BY CLASS. Ruling: the finding is
  right - A2 ranged over one router answer, so tried[0] === shown === chosen and any "wrong attempt" read of the runs
  collapsed onto the right one; A2 is widened (acceptance block above) to every planner path that ships a loop.
  - MISSED first, on the shipped test file (test uncommitted, loopMutants.mjs carrying the new rows):
    "MISSED loop-hazards-first-attempt", "MISSED loop-hazards-pre-swap" ("caught=0 missed=2 trap=0 of 2"); the class's
    third member "MISSED loop-hazards-last-attempt" (hazardsOf(tried[tried.length - 1]!.path), "caught=0 missed=1").
  - Fix: tripLoopHazards.test.ts 'the 200's hazards are the shipped attempt's runs' - five rows (re-seed, re-roll,
    retrace-square, closure re-request pretty / dull), each attempt answering its own hand-written runs, the 200's
    {status, attempts, route.coordinates, hazards} compared WHOLE to the shipped attempt's; plus a meta row.
  - CAUGHT after, by name: loop-hazards-first-attempt by "'a retrace-dirty first attempt, re-see...'",
    loop-hazards-pre-swap and loop-hazards-last-attempt by "'a pretty loop over a closure, re-requ...'",
    loop-hazards-dropped still by "the loop carries its hazard runs, whole" ("caught=4 missed=0 trap=0 of 4").
    loopMutants.mjs MIN_MUTATIONS 44 -> 47, --prove-floor refuses its arms, "real population: quiet".
  - No Sources/ or apps/ios file touched: no digest re-approval, no new Apple CI run needed for this fix.
- 2026-10-09T22:24:20Z agent/claude-opus-5 - rv1-t0340 FAIL (PR #234 at 94b76109) RULED BEFORE CODE. The finding is
  right: A1 ranged over one router answer with FRESH_EMPTY closures, so measuredChosen === chosen and legPath === path,
  and two tripPlanner.ts reads of the PRE-SWAP path survive the 9 trip test files - R1 `hazardsOf(chosen)` ->
  `hazardsOf(measuredChosen)` (preview days ship the closure-crossing route's runs) and R2 `hazards = hazardsOf(path)`
  -> `hazardsOf(legPath)` (a full day's runs from the leg that did not ship). P-SAFE-02 fail-open: a gravel or private
  run on the shipped route can go unshown. Closed by CLASS - every trip path whose shipped geometry differs from the
  first-requested one - and A1 is widened (acceptance block above) over the closure re-request paths the way A2 was for
  /loop: rows {preview, full} x {re-request ships, re-request refused}, each router answer carrying its own runs, the
  200's {status, route, legs, per-day hazards} compared WHOLE to the shipped path's hand-written runs, plus a meta row.
  tripMutants.mjs gains planner-route-hazards-pre-swap and planner-leg-hazards-pre-swap; MIN_MUTATIONS 100 -> 102.
- 2026-10-09T22:37:43Z agent/claude-opus-5 - rv1-t0340 CLOSED BY CLASS (tests and population only; no src/ change).
  - MISSED first, at 94b76109's tripLoopHazards.test.ts with tripMutants.mjs carrying the two new rows: "MISSED
    planner-route-hazards-pre-swap", "MISSED planner-leg-hazards-pre-swap", "RESULT caught=0 missed=2 trap=0 of 2
    (--only)" (baseline green tests=138).
  - Fix: tripLoopHazards.test.ts 'the trip's day hazards are the shipped path's runs' - four rows {preview, full} x
    {re-request ships, re-request refused} over closuresCrossingTrip's fixture (100 nearer squares, X dropped from
    the first request: on the search's detour for preview, on the day-2 leg's detour for full); every answer (the
    crossing path, the re-request, the refused re-request) carries its own hand-written runs; the 200's {status,
    reRequested: 1, route.coordinates, every day's leg coordinates, every day's hazards} compared WHOLE to the
    shipped path's; plus a meta row (every row's shipped runs differ from every other answer's in that row).
    `npx vitest run test/tripLoopHazards.test.ts` "Tests 13 passed (13)".
  - CAUGHT after, by name: planner-route-hazards-pre-swap by "'preview, a closure on the chosen rout...': the trip's
    day hazards are the shipped path's runs"; planner-leg-hazards-pre-swap by "'full, a closure on the day-2 leg,
    its...': the trip's day hazards are the shipped path's runs" ("caught=1 missed=0 trap=0 of 1" - in the pair run
    it read TRAP: that vitest run collected 0 tests, "numTotalTests":0, the loaded box; re-run alone, CAUGHT).
    tripMutants.mjs MIN_MUTATIONS 100 -> 102, "population mutations=102 (floor 102)"; --prove-floor refuses all four
    arms, "real population: quiet". Measured: tripLoopHazards.test.ts 267 lines, tripMutants.mjs 262.
- 2026-10-09T23:08:09Z agent/claude-opus-5 - A9 re-run on the merged head 49034bec (origin/main fetched and merged
  last; main brought T-0343's Swift, ops and queue files, no services/api file).
  - Touched vitest file: `npx vitest run test/tripLoopHazards.test.ts` exit 0, "Tests 13 passed (13)".
  - Bare gates: check-mutate-population exit 0 ("the floor of 147 holds"); check-hazard-copy-sites exit 0 ("ok - 14
    sites, every one approved, in 5 files"); check-pins-yaml exit 0 ("PINS-YAML ok pins=50 fields=403");
    queue-check exit 0 ("QUEUE OK (342 tasks)").
  - check-line-cap (the 20:50:56Z entry left it to CI): run bare, started at e66a715b at 22:38Z, the merge of
    origin/main landing during its run, finished in ~30 min: exit 0, "P-SRC-02: 554 Swift files tracked
    (Sources=269, Tests=198, apps/ios=87), none over 300 lines".
- 2026-10-09T23:32:03Z agent/claude-opus-5 - rv2-t0340 FAIL (PR #234 at 3efbc5b6) RULED BEFORE CODE. The finding is
  right: R1/R2 are caught, but a third pre-swap read survives - tripPlanner.ts `const pointOf = [0, ...(chosen.details
  .time ?? []).map((run) => run.to)]` -> `(measuredChosen.details.time ...)` passes all 9 trip test files, because
  shipTrip's crossing DETOUR and the re-request ROAD both have 41 points and one time run per segment, so the pre- and
  post-swap vertex->point maps coincide (P-SAFE-02 fail-open: a preview day clips the shipped route's runs at the
  wrong point, so a gravel or private run can move to the wrong day or off the day it is on). Same class as R1/R2,
  closed STRUCTURALLY (orchestrator ruling), not by a third spelling:
  - src: planTrip's lambda search and closure re-request move into one scope that returns only the path that ships;
    measuredChosen, first and shown go out of scope there, and route coordinates, edges/vertices, pointOf and the
    route's hazards all read the ONE binding `shipped`. A full day's leg request and its re-request move into one
    function that returns only the leg that ships; legPath goes out of scope, and the leg's coordinates, ETA and
    hazards read that one return. Any pre-swap read in the hazard code is then a ReferenceError, not a value.
  - fixtures: every re-request answer in TRIP_SHIP_ROWS tiles its runs differently from the crossing answer -
    a different point count AND runs that each span several segments (route re-request: ROAD split in two per edge,
    81 points, 40 paired runs; refused route re-request: split in three, 121 points; leg re-request: 5 points, one
    run spanning 4 segments; refused leg: 4 points, one run spanning 3). The meta row also asserts every row's
    shipped answer's vertex->point map differs from every other answer's in that row.
  - population: tripMutants.mjs gains planner-pointof-pre-swap; MIN_MUTATIONS 102 -> 103; R1/R2/pointof anchors
    re-pointed at the new spelling. Shown MISSED at 3efbc5b6's tests first, then CAUGHT by name.
  - Ancestry: the 23:08:09Z A9 entry names 49034bec; the head that PR #234 carried was 3efbc5b6 (a second merge of
    origin/main after it, queue-only drift). This round's A9 is quoted on the FINAL merged head below.
- 2026-10-10T00:48:09Z agent/claude-opus-5 - rv2-t0340 CLOSED BY SCOPE, A1/A8/A9 re-quoted. The final head is the Log commit on top of
  the merged head 66903d91 (origin/main fetched and merged LAST; main brought T-0338/T-0347 queue and
  test/mutate/*.mjs --only changes, no services/api src/ or test/*.ts file).
  - MISSED first: tripMutants.mjs carrying planner-pointof-pre-swap (old spelling) at 3efbc5b6's src and tests:
    "baseline green tests=143", "MISSED planner-pointof-pre-swap", "RESULT caught=0 missed=1 trap=0 of 1 (--only)".
  - Fixtures (06084b73, src still 3efbc5b6's): `npx vitest run test/tripLoopHazards.test.ts` "Tests 13 passed (13)";
    "CAUGHT planner-route-hazards-pre-swap by \"'preview, a closure on the chosen rout...': the trip's day hazards
    are the shipped path's runs\"", "CAUGHT planner-pointof-pre-swap by" the same preview row, "CAUGHT
    planner-leg-hazards-pre-swap by \"'full, a closure on the day-2 leg, its...'\"", "caught=3 missed=0 trap=0 of 3".
    Meta row seen RED: the route re-request tiled like the crossing answer (k 2 -> 1) fails "meta: every trip row
    ships one path ..." ("Tests 1 failed | 12 skipped"); restored.
  - Structure (4a810f70): measuredChosen/first/shown live only inside the search scope, legPath only inside shipLeg;
    the hazard code reads `shipped` / `shippedLeg`. Every trip-reaching file: "Test Files 9 passed (9)", "Tests 145
    passed (145)". Re-pointed anchors: every driver's 58 tripPlanner.ts anchors occur exactly once. On the new src
    the three pre-swap mutants are ReferenceErrors: "CAUGHT planner-route-hazards-pre-swap / planner-pointof-pre-swap
    / planner-leg-hazards-pre-swap by \"a 5-day trip is exactly 12 requests, ...\"", "CAUGHT planner-full-day-reads-
    route by \"every trip day carries its own hazard runs, whole\"", "caught=4 missed=0 trap=0 of 4";
    MIN_MUTATIONS 102 -> 103, "population mutations=103 (floor 103)"; --prove-floor refuses all four arms, "real
    population: quiet". crossingMutants/closuresMutants --only refuse before mutating ("STALE plan-unchecked" /
    "STALE plan-no-closures" in src/plan.ts - pre-existing on main, filed as T-0352), so their four re-pointed
    anchors are proven by the anchor count only.
  - A9 on 66903d91: check-mutate-population exit 0 ("the floor of 147 holds"); check-hazard-copy-sites exit 0 ("ok -
    14 sites, every one approved, in 5 files"); check-pins-yaml exit 0 ("PINS-YAML ok pins=50 fields=403");
    queue-check exit 0 ("QUEUE OK (344 tasks)"). Touched vitest files on 66903d91: two runs collected 0 tests
    ("Error: [vitest-pool]: Timeout starting cloudflare-pool runner", 73 node processes on the box) and the trip
    --only baseline refused the same way - environment; the merge changed no services/api src/ or test .ts file,
    so 4a810f70's green runs stand and PR CI is the confirmation on the merged head.
  - Measured: tripPlanner.ts 249 lines, tripLoopHazards.test.ts 295, tripMutants.mjs 262.
- 2026-10-10T01:50:19Z agent/rv3-t0340 - REVIEW round 3 of PR #234 on head 1c28ec70: PASS.
  - Structure: in planTrip the search and the closure re-request run inside one async scope (L157-185) that returns
    only "{ outcome, shipped: shown.path, edges: shown.edges, split: shown.split }"; measuredChosen (L164), first
    (L172) and shown (L179) are bound only inside it. legPath is bound only inside shipLeg (L195-204), which returns
    returned(legPath, ...). pointOf "[0, ...(shipped.details.time ?? []).map((run) => run.to)]" (L210),
    "routeHazards = hazardsOf(shipped)" (L211), route.coordinates "shipped.coordinates" (L237), and each day's
    leg/hazards read "shippedLeg" (L223-227). No pre-swap binding is in scope there.
  - tripMutants --only (re-applied R1/R2/pointOf): "baseline green tests=143"; "CAUGHT planner-full-day-reads-route
    by \"every trip day carries its own hazard runs, whole\""; planner-route-hazards-pre-swap,
    planner-pointof-pre-swap, planner-leg-hazards-pre-swap each "CAUGHT ... by \"a 5-day trip is exactly 12
    requests, ...\"" (ReferenceErrors - the spellings no longer reach a binding); "RESULT caught=4 missed=0 trap=0 of 4".
  - Reviewer's own mutants (applied by hand, 9 trip files incl. closuresCrossingTrip, restored after each):
    own-split-from-first (scope returns "edges: first.edges, split: first.split" - pre-swap split/vertices with the
    shipped path) RED: "a dull detour crossing a closure, re-requested to a pretty road, ships the road (whole 200)",
    1 failed | 157 passed. own-leg-refused-ships ("return again.timeMs > ceiling ? null : again;" -> "return
    again;") RED: "'full, the day-2 leg\'s re-request ref...': the trip's day hazards are the shipped path's runs"
    and "/trip paid, the last leg's re-request over its day ceiling: not shown; the crossing leg returned, X named",
    2 failed | 156 passed.
  - Gates: gh pr checks 234 "core pass 7m59s", "pins-source-only pass 3m0s" (run 38011617438); bare
    check-mutate-population exit 0 ("the floor of 147 holds"); bare queue-check exit 0 ("QUEUE OK (344 tasks)");
    LAST: git fetch origin, origin/main 4f47d06f, "git merge-base --is-ancestor origin/main origin/task/T-0340"
    exit 0.
  - Recordable: crossingMutants/closuresMutants still refuse on STALE plan.ts anchors (T-0352); their re-pointed
    tripPlanner anchors are proven by the anchor count only.
