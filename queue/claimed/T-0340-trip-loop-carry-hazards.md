---
id: T-0340
title: The /trip and /loop answers carry the route's hazard runs, and the trip and loop cards render them from HazardCopy - today only /plan and /reroute report surface and road_access runs
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-09T19:11:58Z
lease_expires_at: 2026-10-10T05:11:58Z
worktree: .worktrees/T-0340
branch: task/T-0340
exclusive: []
touches: [services/api/src/, services/api/test/, Sources/ScenicAPIClient/, Sources/ScenicKit/, Tests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/check-safety-disclaimer-pinned, ops/lib/check-hazard-copy-sites.txt, ops/mutate/, queue/]
pins_affected: [P-SAFE-02]
reviewer: null
depends_on: [T-0339]
verify: [ops/test, ops/check-pins]
acceptance:
  - "A1 WORKER /trip WHOLE (full equality, through handleTrip): over view {preview, full} x road hazards {none, MIX} (MIX = a surface run crossing the day-1/day-2 boundary, a road_access run inside one day, a run on the route's first edge, a run on its last edge, an upper-cased value, and whitelisted asphalt / yes / missing runs), the 200 EQUALS the harness oracle expectedTrip with each day's hazards recomputed in the test by R1's rule written out independently of src/ (preview: the chosen route's runs clipped to the day's point span, indices into route.coordinates; full: the leg's own runs, indices into leg.coordinates), and every router request's details EQUAL [time, distance, scenic_score, surface, road_access]. Test: 'every trip day carries its own hazard runs, whole'."
  - "A2 WORKER /loop WHOLE (through handleLoop): over road hazards {none, MIX'} (MIX' = surface and road_access runs incl. an upper-cased value and whitelisted asphalt / yes / missing), the 200's hazards EQUAL the list recomputed in the test, and the request still sends ROUTE_DETAILS. Test: 'the loop carries its hazard runs, whole'."
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
