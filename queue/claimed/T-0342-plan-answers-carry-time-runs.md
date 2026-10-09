---
id: T-0342
title: The /plan and reroute answers carry GraphHopper's per-edge time runs, and ScenicAPIClient hands them to the preview, so RetimedPreview can clear the estimate badge (T-0325 R2 follow-up)
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-09T14:53:12Z
lease_expires_at: 2026-10-10T00:53:12Z
worktree: .worktrees/T-0342
branch: task/T-0342
exclusive: []
touches: [services/api/src/, services/api/test/, Sources/ScenicAPIClient/, Sources/ScenicKit/, Tests/ScenicAPIClientTests/, Tests/ScenicKitTests/, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-SAFE-07]
reviewer: null
depends_on: [T-0325, T-0333]
verify: [ops/test, ops/check-pins]
acceptance:
  - "A1 cd services/api && npx vitest run test/planTimeRuns.test.ts test/closuresCrossing.test.ts test/planCeiling.test.ts test/planReroute.test.ts test/loopShape.test.ts -> every test passes; planTimeRuns' table (fresh AND reroute x every time-detail row) compares each 200 body WHOLE to its recomputation, the request details to the literal list"
  - "A2 swift test --scratch-path .build/t0342 --filter 'PlanTimeRunsTests|PlanResponseDecodeTests|PlanClientResponseTests|RetimedPreviewTests' -> exit 0"
  - "A3 RED first: the new Worker and Swift tests run against the shipped code before any Sources/ or src/ change fail BY NAME (quoted in the Log)"
  - "A4 python ops/mutate/plansheet.py --only <the new entries> -> MUTATE OK, each caught by a test it names; MIN_MUTATIONS raised to the new count"
  - "A5 Worker mutants (no TS population root exists - P-PROC-06 reads Sources/ and services/etl/etl/): runs from measuredChosen instead of chosen, each tiling bound of timeRunsOf dropped, the reroute's runs dropped - each red by test name, quoted"
  - "A6 python ops/lib/run-named-tests.py P-SAFE-07 -> passed=N/N with the new tests bound; ops/lib/check-safety-disclaimer exit 0 (rows re-approved); check-learned-speeds-sites.py ok (no new site)"
  - "A7 check-mutate-population, check-pins-yaml, queue-check ok on the merged head; ops/check-pins --source-only exit 0"
---
## Brief

Filed by T-0325 (R2, R7). T-0325 ruled that per-edge free-flow times are GraphHopper's `details=time`, never a
length split of eta_s (its Log has the worked example: a length split makes a free-flow drive read 13 min against a
true 10 and clears the badge on it). The device half ships in T-0325: CorridorTimeRun (from, to, whole ms),
CorridorRoute(route:timeRuns:) holding the runs to tile the drawn route edge for edge (tripPlanner.ts edgesOf's rule),
RetimedPreview.of(_:timeRuns:by:departsAt:). Today scenicPlanner.ts ROUTE_DETAILS has no `time` and
ScenicPlanResult carries eta_s only, so no preview has runs and the badge is always on (fails safe).

The claimer MEASURES then RULES: adding `time` to ROUTE_DETAILS changes every request-body equality test of /plan,
/loop and reroute (count them); the response field's name and shape (the chosen path's runs over route.coordinates,
whole ms); whether the reroute answer carries them too (DriveSession takes a reroute's line, CorridorClock stops
recording after one until it does); PlanResponse decode and PlanPreview's new field (ClientPlanner), refusals by full
equality; P-PRIV-05 is untouched (the runs come FROM the server). T-0333 is changing the Worker and ScenicAPIClient
now - merge it first (memory parallel-worker-prs-conflict).

## Log
- 2026-10-09T11:37:54Z filed by agent/claude-opus-5 (T-0325 owner) from T-0325 R2/R7.
- 2026-10-09T14:53:12Z claimed by agent/claude-opus-5; lease until 2026-10-10T00:53:12Z
- 2026-10-09T15:01:15Z MEASURE then RULE (agent/claude-opus-5, before any code).
  MEASURED. (a) ROUTE_DETAILS (scenicPlanner.ts) = scenic_score, road_class, osm_way_id, surface, road_access; no
  `time`. It is sent by every /plan request (the fastest and each car_scenic), by reroutePlanner (imports `route`) and
  by loopPlanner.ts:125 (imports ROUTE_DETAILS). Request-body equality sites over it in services/api/test: ONE literal
  - planCeiling.test.ts:117 "asks the router for the surface and road_access details" (one test, its 7 requests) - and
  THREE that compare to the imported constant and follow it unchanged: closuresCrossing.test.ts:279, loopShape.test.ts:44,
  planReroute.test.ts:64 (routeBody, 5 uses over 11 tests). /trip's TRIP_DETAILS (time, distance, scenic_score) is
  separate and unchanged (tripFull.test.ts:15, tripRoute.test.ts:19 literals stay). (b) Recorded router bodies: every
  Tests/Fixtures/t0221/*/*.json carries details osm_way_id, road_class, scenic_score only - no `time` - so every
  recorded-fixture /plan answer omits the new field; planHarness.syntheticPath sends no `time` unless `extra` names it;
  closuresCrossing.answer() is the one /plan router fake that sends `time` (runs [i, i+1, totalMs/n], whole for its
  shapes: n = 1..3 over 1_200_000 ms). Its drive() returns status, requests, areas, coordinates and hazard - not the
  whole body - so no existing whole-answer comparison changes. (c) ScenicPlanResult has no runs field; planReroute
  builds the same shape. tripPlanner.edgesOf is the tiling rule: first from 0, each from == previous to, to > from,
  last to == coordinates.length - 1, Number.isInteger values >= 0, not all zero. (d) Swift: PlanResponse has no runs;
  PlanPreview (ScenicKit) has none; ClientPlanner.preview maps 7 fields; RetimedPreview.of rebuilds PlanPreview field by
  field (a new field would be DROPPED by a retime unless carried). CorridorTimeRun is not Codable and not in
  check-learned-speeds-sites IDENTIFIERS. PlanResponse/PlanPreview constructions: 11 test files + 2 apps/ios fixtures,
  all by the memberwise init, so a defaulted parameter changes none of them (no apps/ios edit, no Apple CI).
  (e) Populations: plansheet covers ClientPlanner (FILTER PlanSheetTests|...|PlanRerouteWireTests), traffic covers
  RetimedPreview; P-PROC-06's roots are Sources/ and services/etl/etl/ - no TS module needs a population.
  RULED. R1: "time" is APPENDED to ROUTE_DETAILS (the one list; /loop's requests carry it too - its answer is
  unchanged, the loop preview has no retime; out of scope). The planCeiling literal is rewritten to the six names; the
  three import sites follow; planTimeRuns asserts every request's details equal the literal list.
  R2: the field is `time_runs`, a list of {from, to, ms} - indices into route.coordinates, ms GraphHopper's whole
  milliseconds as sent - read from the path the answer SHIPS (`chosen`, after the closures guard's swap), by one
  function timeRunsOf (new file services/api/src/timeRuns.ts). It is PRESENT only when the runs tile the route edge
  for edge by edgesOf's rule (>= 2 coordinates; non-empty; first from 0; each from == previous to; to > from; last to
  == last index; every ms a Number.isSafeInteger >= 0; some ms > 0). Anything else OMITS the field and the plan is
  still answered: the runs only feed the device's badge-off decision, their absence keeps the badge on (fails safe),
  and refusing a route the ceiling already accepted over an optional detail costs the user the drive for nothing. A
  details entry that is not [from, to, value] stays what decodeRoutePath already makes it (502 malformed_response).
  No sum check against paths[0].time: the ceiling reads path time, the device's retime reads the runs only when every
  edge is learned (T-0325 R4), and our router's per-edge vs path time has not been measured - not invented here.
  R3: the reroute answer carries `time_runs` by the same function over its own chosen path (planTimeRuns runs every row
  under both variants, fresh and reroute). Feeding a reroute's runs to CorridorClock is T-0343's (the app).
  R4: client. PlanResponse.timeRuns: [CorridorTimeRun]? - key ABSENT -> nil (the badge stays on); key PRESENT -> it
  must be a list of objects with integer from, to, ms that make CorridorRoute(route:timeRuns:) non-nil over the
  decoded route (the shipping tiling rule, not a copy), else the decode throws and PlanClient answers
  unexpectedResponse(200): the Worker sends only tiling runs, so anything else is a broken contract. null is refused
  (the Worker omits, never nulls). PlanPreview gains timeRuns (default nil); ClientPlanner.preview passes it whole;
  RetimedPreview.of carries preview.timeRuns through. Tests are Swift Testing (the plansheet runner's FAIL_LINE), in
  Tests/ScenicAPIClientTests/PlanTimeRunsTests.swift, full equality on PlanResponse/PlanPreview.
  R5: P-PRIV-05 untouched - the runs come FROM the server and nothing new is sent; no IDENTIFIERS change.
  R6: P-SAFE-07 named-tests gain the new Swift tests (filter widened); Sources/ digest rows re-approved for
  PlanResponse, ClientPlanner, PlanPreview, RetimedPreview; plansheet population gains the Swift mutants (A4).
  R7: closuresCrossing's row gains the answer's time_runs for the /plan routes (fresh and reroute): the runs over the
  row's final shape at SCENIC_MS / n, so a swap-ignoring read of measuredChosen is red there.
- 2026-10-09T15:35:59Z RED then GREEN, PINS, MUTANTS (agent/claude-opus-5; code 76734a60, pins 9c7a1feb, 4eaeec55).
  RED (A3), Worker, at 203e5dde plus the new tests only (src/ unchanged): `npx vitest run test/planTimeRuns.test.ts
  test/closuresCrossing.test.ts test/planCeiling.test.ts` exit 1, "Tests 71 failed | 92 passed (163)": "fresh: every
  row's 200 equals the plan without the detail plus the row's time_runs, whole", "reroute: every row's 200 equals ...",
  "asks the router for the surface and road_access details the hazards are read from", every /plan and /plan reroute
  row of "requests, areas, the returned path and the hazard equal the row's" and the three re-request rows per /plan
  route ("the re-request exactly at the ceiling: the clear path is returned ..." among them); the meta row was red on
  my own miscount (5 kept rows written, 4 in the table) and was corrected to 4 kept / 16 omitted before any src/ code.
  RED, Swift, with the API surface stubbed (PlanResponse.timeRuns and PlanPreview.timeRuns stored, never decoded or
  passed): `swift test --filter PlanTimeRunsTests` exit 1, "Test run with 2 tests in 1 suite failed ... with 22
  issues" - "a 200's time_runs decode whole when they tile the route; absent is nil; every bound refused" (20 issues:
  17 refusal rows decoded, 3 run rows nil) and "a response's runs reach the preview whole, and a retime keeps them" (2).
  GREEN at 76734a60 (A1, A2): the five vitest files "Tests 184 passed (184)"; `swift test --filter 'PlanTimeRunsTests|
  PlanResponseDecodeTests|PlanClientResponseTests|RetimedPreviewTests|PlanSheetTests|PlanRerouteWireTests'` "Executed 30
  tests, with 0 failures" and "Test run with 18 tests in 4 suites passed". closuresCrossing's ceiling row now expects
  the SWAPPED path's own run, [{from 0, to 1, ms PLAN_CEILING_MS}], never the first path's (R7).
  PINS (A6): check-safety-disclaimer named the four changed files (ClientPlanner, PlanResponse, PlanPreview,
  RetimedPreview), rows re-approved, exit 0; named-tests P-SAFE-07 filter widened by
  `|ScenicAPIClientTests\\.PlanTimeRunsTests` and both tests bound: "NAMED P-SAFE-07 passed=18/18";
  check-learned-speeds-sites "ok - 17 sites, every one approved, in 7 files" (no new site, R5).
  POPULATION (A4): plansheet entries 49-54 (time_runs never read, the tiling check dropped, null read as absent, ms
  read from `to`, ClientPlanner drops the runs, a retime drops the runs), RESPONSE and RETIMED added to SUBJECTS (the
  first run refused with a KeyError on the unregistered file - fixed in 4eaeec55), FILTER gains PlanTimeRunsTests,
  MIN_MUTATIONS 48 -> 54, MIN_TEST_FILES 5 -> 6. `python ops/mutate/plansheet.py --only 49,...,54` at 4eaeec55: "MUTATE
  OK caught=6/6", 49-52 by the decode table, 53-54 by the preview test. check-mutate-population "every added module is
  covered or allowlisted; the floor of 147 holds".
  WORKER MUTANTS (A5), each alone over planTimeRuns, closuresCrossing, planCeiling, planReroute: "WORKER MUTANTS
  caught=11/11" - W1 runs from measuredChosen (4 red: the /plan "the fixture ... router honours" rows, where the swap
  ships another path), W2 the reroute's runs dropped (34 red), W3 first-from, W4 to past from, W5 isInteger for
  isSafeInteger, W6 a negative ms kept, W7 the last-vertex check, W8 the some-time check, W10 a zero ms refused, W11
  some time read as >= 0 (each 2 red: the fresh and reroute tables), W9 time not requested (3 red, the planCeiling
  literal among them).
- 2026-10-09T16:02:18Z ACCEPTANCE RE-QUOTED on the merged head 15e23279 (agent/claude-opus-5; origin/main be0960a8
  merged - one queue filing, T-0346 - no conflict; T-0341 and T-0344 are not on main yet).
  A1 the five vitest files: "Test Files 5 passed (5)", "Tests 184 passed (184)". A2 `swift test --filter
  'PlanTimeRunsTests|PlanResponseDecodeTests|PlanClientResponseTests|RetimedPreviewTests'`: "Executed 30 tests, with 0
  failures" and "Test run with 4 tests in 2 suites passed". A3 RED quoted in the entry above. A4 "MUTATE OK
  caught=6/6" (entries 49-54; Sources/ unchanged since 4eaeec55). A5 "WORKER MUTANTS caught=11/11" (src/ unchanged
  since 76734a60). A6 "NAMED P-SAFE-07 passed=18/18"; check-safety-disclaimer exit 0; check-learned-speeds-sites "ok -
  17 sites, every one approved, in 7 files". A7 check-mutate-population "every added module is covered or allowlisted;
  the floor of 147 holds"; check-pins-yaml "PINS-YAML ok pins=49 fields=395"; queue-check "QUEUE OK (336 tasks)";
  check-line-cap "548 Swift files tracked ... none over 300 lines". `ops/check-pins --source-only` did not finish
  inside 12 minutes on this loaded box (no output written) - left to CI's run of it, named in the PR.
- 2026-10-09T16:28:49Z MERGE OF PR #227 (T-0341) and R8 (agent/claude-opus-5; merge fd1fdfac). PR #229 read CONFLICTING: main had
  merged T-0341, which adds closures_hazard / closures to the same PlanResponse, PlanPreview and ClientPlanner init
  lines and digest rows. Resolved as a union: PlanResponse(..., continued:, closuresHazard: = .clear, timeRuns: = nil),
  PlanPreview(..., continuation:, closures: = .clear, timeRuns: = nil), ClientPlanner passes both; the four digest rows
  re-approved over main's (main's other new rows kept). R8, found at the merge: main's RetimedPreview.of (T-0325) and
  PlanPreview.closures (T-0341) landed in parallel, so a retime rebuilt the preview with closures DEFAULTED to .clear -
  a retimed preview would have dropped an `unavailable` or crossing closures line. RetimedPreview now carries
  `closures: preview.closures`; PlanTimeRunsTests' preview test runs both variants with closures `unavailable` and
  compares the retimed preview whole; plansheet entry 55 "a retime drops the closures line" (closures: .clear, the
  pre-merge behaviour) - MIN_MUTATIONS 54 -> 55; mutant 54's anchor narrowed to the `timeRuns:` argument.
  RE-QUOTED on fd1fdfac: A1 "Test Files 5 passed (5)", "Tests 184 passed (184)"; A2 (plus ClosuresHazardTests and
  PlanSheetTests) "Executed 30 tests, with 0 failures" and "Test run with 16 tests in 4 suites passed"; A4 `--only
  49,...,55` "MUTATE OK caught=7/7", 55 by "a response's runs reach the preview whole, and a retime keeps them"; A6
  check-safety-disclaimer exit 0, check-hazard-copy-sites "ok - 12 sites, every one approved, in 5 files",
  check-learned-speeds-sites "ok - 17 sites"; A7 check-mutate-population "the floor of 147 holds", check-pins-yaml
  "PINS-YAML ok pins=49 fields=395", check-line-cap "552 Swift files ... none over 300 lines". The earlier
  `ops/check-pins --source-only` (on 15e23279) did finish after the entry above was written: "PINS ok=20 skipped=28
  pending=1 expired=0 failed=0 tier=linux source-only", exit 0.
