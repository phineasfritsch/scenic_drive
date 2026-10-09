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
