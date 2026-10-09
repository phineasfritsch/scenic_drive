---
id: T-0335
title: /trip, /loop and the isochrone planner are honest when nothing pretty is reachable - score the route they would ship with routeScore.ts (T-0332) and refuse below 0.45, or rule in the Log why a planner is exempt
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-09T04:41:42Z
lease_expires_at: 2026-10-09T14:41:42Z
worktree: .worktrees/T-0335
branch: task/T-0335
exclusive: []
touches: [services/api/src/, services/api/test/, Sources/ScenicAPIClient/, Sources/ScenicKit/, Tests/, ops/lib/, ops/lib/check-safety-disclaimer-linked-digests.txt, pins/PINS.yaml]
pins_affected: [P-SAFE-04]
reviewer: null
depends_on: [T-0332]
verify: [ops/test, ops/check-pins]
acceptance:
  - "A1 TRIP POPULATION, MISSED then CAUGHT through handleTrip (the handler ROUTES[\"/trip\"] calls), whole-body equality, in test/tripHonest.test.ts: the tripHarness road with the scenic answer's every edge scenic_score 2 (oracle 0.020000) answers, preview AND full view, 422 whose WHOLE body is {error: nothing_pretty, days: 5, extra_budget_pct: 40}, after exactly 7 router requests (1 fastest + 6 search, no day leg); on 9e9924d8 the same rows answer 200 (quoted red by test name in the Log). The two integer encodings either side of 0.45 on that road: every edge 5 (oracle 0.425000) is the same 422; every edge 6 (oracle 0.510000) is the 200 whose whole body equals expectedTrip(days 5, edgeMs SCENIC_EDGE_MS, lambda 7.75). A scenic answer with no scenic_score detail is the same 422 (R3 fail closed). Every /trip router request (search and day legs) carries details [time, distance, scenic_score] compared whole (tripRoute / tripFull REQUEST and LEG)."
  - "A2 LOOP RE-ROLL then REFUSAL through handleLoop, whole-body equality, in test/loopHonest.test.ts, every row a function of its answers list: [squareLoop 2] then [squareLoop 8] answers 200 equal to the loopShape recomputation with attempts 2, seed (S+1); [2, 2, 8] answers 200 with attempts 3 and seed (S+2), the third request's round_trip.seed S+2 and its custom_model buildCustomModel(LOOP_LAMBDA, the feed) with NO retrace areas; [2, 2, 2] and [unscored x3] and [5, 5, 5] (oracle 0.425000) answer 422 whose WHOLE body is {error: nothing_pretty, minutes: 45} after exactly 3 requests (LOOP_UPSTREAM_COST, a 4th never sent); [6] (oracle 0.510000) answers 200 attempts 1; [out-and-back 8, squareLoop 2, out-and-back 8] answers nothing_pretty (a clean loop was found and it was dull, R3); three retraced loops still answer no_clean_loop with their least fraction (loopCost, unedited). On 9e9924d8 the dull rows answer 200 (quoted red by name in the Log)."
  - "A3 EXEMPT: /isochrone (isochronePlanner.planReach) ships reach polygons only - no route, no scenic_score - so it is not scored (R1); its suites (isochroneShape, isochroneCost, isochroneVerdicts, surpriseReachParity) stay green unedited. POST /plan reroute stays exempt (T-0332 R6)."
  - "A4 NO REGRESSION: tripHarness.tripPath and loopHarness.loopPath default to a scenic_score 8 run (oracle 0.713333) so every pre-existing /trip and /loop test keeps its whole answer; vitest over tripRoute, tripFull, tripPlaces, tripRequest, loopShape, loopCost, closuresCrossing, closuresCrossingTrip, closuresDriven, closuresNearest, closuresNearestRetry, closuresRoutes, requestReadSites, reflectionSites, planHonest, isochroneShape, isochroneCost and the two new files all pass; P-COST-04 counts unchanged (trip <= 12, loop <= 3)."
  - "A5 PINS + GATES: named-tests.json P-SAFE-04 gains the A1 preview-refusal row and the A2 three-dull refusal row by name (a refusal carries no route, so the ceiling is untouched); check-pins-yaml, check-mutate-population, queue-check and check-line-cap green on the merged head; no Sources/ or apps/ios file changes (the client reading of the new 422 is the follow-up, R5)."
---
## Brief

T-0332 R6 (owner ruling) scoped the honest failure to POST /plan's fresh plans (reroutes exempt). tripPlanner.ts,
loopPlanner.ts and isochronePlanner.ts each ship a route without consulting RouteScore; grep of services/api/src for
routeScoreOf finds only scenicPlanner.ts. MEASURE FIRST: what each planner returns, which recorded fixtures each test
suite drives (and their RouteScore, via Tests/Fixtures/t0332/oracle.py's reading), and whether a loop or a surprise
destination should refuse or re-pick (a Surprise Me that answers "nothing pretty" may be worse than a re-roll within
the same request cap, P-COST-04). Then the acceptance: whole-answer equality through each handler, the population
MISSED before / CAUGHT after by test name.

## Log
- 2026-10-08T21:58:00Z filed by agent/claude-opus-5 (T-0332 owner) from T-0332 R6.
- 2026-10-09T04:41:42Z claimed by agent/claude-opus-5; lease until 2026-10-09T14:41:42Z
- 2026-10-09T04:51:51Z MEASURED (agent/claude-opus-5, owner), before any code (.artifacts/t0335/measure.py, which loads
  Tests/Fixtures/t0332/oracle.py and reads RouteScore with it):
  - M1 what each planner answers on 9e9924d8. tripPlanner.planTrip: fastest + searchLambda over car_scenic (6), then
    the T-0286 closure guard, then (full view) one leg a day; it ships `chosen` (route) and, full, the legs, never
    scored. Its requests ask details ["time", "distance"] only (TRIP_DETAILS): the router is never asked for
    scenic_score, so the Worker cannot score a trip today. loopPlanner.planLoop: up to 3 round_trip attempts (seed,
    seed + 1, seed + 1 with retrace areas), keeps the first retrace-clean one, never scored; its requests ask
    ROUTE_DETAILS (scenic_score included). isochronePlanner.planReach: ONE GET /isochrone, answers reach polygons
    (buckets) - no route, no path, no scenic_score anywhere in the answer. grep routeScoreOf services/api/src: only
    scenicPlanner.ts.
  - M2 what the suites drive: no /trip, /loop or /isochrone suite drives a recorded router body. The recorded
    fixtures under those directories are not router paths: t0252/loops.json {unit, loops}, t0268/trips.json {source,
    unit, route, places}, t0263/isochrone.json and la-reach.json {minutes, buckets}, t0263/points.json {body, points}.
    The synthetic bodies, through the oracle: tripHarness.tripPath (time, distance) UNSCORABLE; loopHarness
    .squareLoop (osm_way_id, road_class) UNSCORABLE; closuresCrossing.test.ts `answer` (T-0332 gave it scenic_score 8)
    0.713333. On the trip road with every edge s: s=2 0.020000 (dud 1.000), s=5 0.425000, s=6 0.510000, s=8 0.713333
    (1 episode); squareLoop with every edge s: the same four values. So under fail-closed every existing /trip and
    /loop body is an honest failure unless the harnesses gain a score - the T-0332 R3 precedent (curveRouter got 8).
  - M3 the cap left for a re-pick (P-COST-04). /trip: 1 + 6 = 7 before the guard, + 1 closure re-request only if
    used + 1 + (full ? days : 0) <= 12; preview leaves 4-5 requests, a 5-day full trip 0 after its legs. /loop: 3,
    and all 3 are already the retry ladder - a re-roll must live inside them. /isochrone: 1 of 1.
- 2026-10-09T04:51:51Z RULED (agent/claude-opus-5, owner):
  - R1 /isochrone is EXEMPT: it ships no route - reach polygons only - so there is nothing to score; the route a
    Surprise pick becomes is a separate request. Unchanged.
  - R2 /trip REFUSES, never re-picks: the destination is the driver's, and the lambda search has already chosen the
    best lambda inside the ceiling - another lambda is either over the ceiling or one the search ranked lower. The
    chosen A->B path (after the T-0286 closure re-request, so the route that would ship) is scored with routeScoreOf
    BEFORE any day leg is requested, so a refusal spends 7 (or 8) requests, never 7 + days. Below 0.45 (or
    unscorable, T-0332 R3) throws TripFailure("nothing_pretty"), answered 422 {error: nothing_pretty, days,
    extra_budget_pct} (the request's own). No offers: extra_budget_pct is already capped at MAX_EXTRA_BUDGET_PCT 40
    and there is no back-roads trip request. TRIP_DETAILS gains "scenic_score" (search, re-request and legs share
    route()). The legs are not scored on their own: they are the same lambda over the scored corridor.
  - R3 /loop RE-ROLLS within LOOP_UPSTREAM_COST, then refuses (owner intent: a calm adventure re-rolls before it
    says nothing). An attempt ships only if it is retrace-clean AND routeScoreOf >= 0.45. The ladder: seed; seed + 1;
    then, if the second attempt retraced, its retrace areas (as today), else (it was retrace-clean but dull) a third
    seed, seed + 2, over the same feed. The closure re-request accepts only a shippable attempt. When nothing ships:
    422 {error: nothing_pretty, minutes} if ANY attempt was retrace-clean (dullness is what stopped it), else
    no_clean_loop as today.
  - R4 the synthetic harness bodies (tripHarness.tripPath default details, loopHarness.loopPath) gain a scenic_score
    8 run per edge (0.713333), so no pre-existing answer moves; tripFull's malformed-detail CASES and the day legs'
    `{}` details are unchanged (edgesOf refuses those before any score, and legs are not scored).
  - R5 the app: TripReplyReader / LoopReplyReader map (422, nothing_pretty) to .unexpectedResponse(status: 422)
    today (their default). Reading it as its own error with copy is Sources/ + apps/ios work, filed as a follow-up,
    not claimed here; this PR touches no Apple file.
  - R6 P-SAFE-04: a refusal ships no route, so the ceiling is untouched; the new refusal rows are bound by name.
    No ops/mutate population: no new numeric module (routeScore.ts is T-0332's; the planners gain a comparison).
