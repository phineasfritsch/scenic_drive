---
id: T-0335
title: /trip, /loop and the isochrone planner are honest when nothing pretty is reachable - score the route they would ship with routeScore.ts (T-0332) and refuse below 0.45, or rule in the Log why a planner is exempt
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-09T04:41:42Z
lease_expires_at: 2026-10-09T14:41:42Z
worktree: .worktrees/T-0335
branch: task/T-0335
exclusive: []
touches: [services/api/src/, services/api/test/, Sources/ScenicAPIClient/, Sources/ScenicKit/, Tests/, ops/lib/, ops/lib/check-safety-disclaimer-linked-digests.txt, pins/PINS.yaml]
pins_affected: [P-SAFE-04]
reviewer: agent/rv3-t0335
depends_on: [T-0332]
verify: [ops/test, ops/check-pins]
acceptance:
  - "A1 TRIP POPULATION, MISSED then CAUGHT through handleTrip (the handler ROUTES[\"/trip\"] calls), whole-body equality, in test/tripHonest.test.ts: the tripHarness road with the scenic answer's every edge scenic_score 2 (oracle 0.020000) answers, preview AND full view, 422 whose WHOLE body is {error: nothing_pretty, days: 5, extra_budget_pct: 40}, after exactly 7 router requests (1 fastest + 6 search, no day leg); on 9e9924d8 the same rows answer 200 (quoted red by test name in the Log). The two integer encodings either side of 0.45 on that road: every edge 5 (oracle 0.425000) is the same 422; every edge 6 (oracle 0.510000) is the 200 whose whole body equals expectedTrip(days 5, edgeMs SCENIC_EDGE_MS, lambda 7.75). A scenic answer with no scenic_score detail is the same 422 (R3 fail closed). Every /trip router request (search and day legs) carries details [time, distance, scenic_score] compared whole (tripRoute / tripFull REQUEST and LEG)."
  - "A2 LOOP RE-ROLL then REFUSAL through handleLoop, whole-body equality, in test/loopHonest.test.ts, every row a function of its answers list: [squareLoop 2] then [squareLoop 8] answers 200 equal to the loopShape recomputation with attempts 2, seed (S+1); [2, 2, 8] answers 200 with attempts 3 and seed (S+2), the third request's round_trip.seed S+2 and its custom_model buildCustomModel(LOOP_LAMBDA, the feed) with NO retrace areas; [2, 2, 2] and [unscored x3] and [5, 5, 5] (oracle 0.425000) answer 422 whose WHOLE body is {error: nothing_pretty, minutes: 45} after exactly 3 requests (LOOP_UPSTREAM_COST, a 4th never sent); [6] (oracle 0.510000) answers 200 attempts 1; [out-and-back 8, squareLoop 2, out-and-back 8] answers nothing_pretty (a clean loop was found and it was dull, R3); three retraced loops still answer no_clean_loop with their least fraction (loopCost, unedited). On 9e9924d8 the dull rows answer 200 (quoted red by name in the Log)."
  - "A3 EXEMPT: /isochrone (isochronePlanner.planReach) ships reach polygons only - no route, no scenic_score - so it is not scored (R1); its suites (isochroneShape, isochroneCost, isochroneVerdicts, surpriseReachParity) stay green unedited. POST /plan reroute stays exempt (T-0332 R6)."
  - "A4 NO REGRESSION: tripHarness.tripPath and loopHarness.loopPath default to a scenic_score 8 run (oracle 0.713333) so every pre-existing /trip and /loop test keeps its whole answer; vitest over tripRoute, tripFull, tripPlaces, tripRequest, loopShape, loopCost, closuresCrossing, closuresCrossingTrip, closuresDriven, closuresNearest, closuresNearestRetry, closuresRoutes, requestReadSites, reflectionSites, planHonest, isochroneShape, isochroneCost and the two new files all pass; P-COST-04 counts unchanged (trip <= 12, loop <= 3)."
  - "A5 PINS + GATES: named-tests.json P-SAFE-04 gains the A1 preview-refusal row and the A2 three-dull refusal row by name (a refusal carries no route, so the ceiling is untouched); check-pins-yaml, check-mutate-population, queue-check and check-line-cap green on the merged head; no Sources/ or apps/ios file changes (the client reading of the new 422 is the follow-up, R5)."
  - "A6 WHOLE ROUTE, BY CLASS (pre-review M1a), through handleTrip, whole-body equality, in test/tripHonest.test.ts: 14 rows, each the tripHarness road (days 5, 8 edges a day) with edges [from, to) scored inside and the rest outside, oracle.py's whole-road score quoted per row; every row below 0.45 is the 422 {error: nothing_pretty, days: 5, extra_budget_pct: 40} after 7 requests and every row above is the whole 200 expectedTrip(days 5). Rows 1-10 are each day pretty on a dull road (0.304662-0.305999, refused) and dull on a pretty road (0.610668-0.644999, shipped); rows 11-14 cover the multi-day and near-whole spans ([8,28) 2/8 0.491452, [0,20) 8/2 0.459378, [0,20) 2/8 0.457289, [1,20) 8/2 0.446527). A meta row proves through routeScoreOf that every one of the 819 strict sub-spans [a, b) of the road has a row whose whole verdict differs from that span's verdict."
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
- 2026-10-09T05:23:51Z RED by name on 9e9924d8's src (the two new files written first; `npx vitest run test/tripHonest.test.ts
  test/loopHonest.test.ts` before any src change): "Tests 9 failed (9)", every row received status 200 - the
  population MISSED, a dull route sold as scenic. /trip: "a preview trip whose chosen route scores 0.02 answers
  nothing_pretty, never a 200 trip" received 200 lambda 7.75 after 7 requests; "a full trip whose chosen route scores
  0.02 is refused before any day leg is requested" received 200 after 12 requests (7 + 5 legs); "every edge 5 (0.425,
  ...) is refused; every edge 6 (0.51, ...)" and "a chosen route with no scenic_score detail is refused (T-0332 R3,
  fail closed)" received 200. /loop: "a dull first loop re-rolls ..." received attempts 1 (the dull loop shipped);
  "dull at seed and seed + 1 re-rolls seed + 2 ..." attempts 1; "three dull loops answer nothing_pretty ..." 200
  attempts 1; "unscored loops are dull ...; every edge 5 (0.425) is dull; every edge 6 (0.51) ships" 200 attempts 1;
  "retraced, then clean but dull, then retraced again answers nothing_pretty ..." 200 attempts 2.
- 2026-10-09T05:23:51Z GREEN (0fdfa1a6): the same rows CAUGHT by name - 422 {error: nothing_pretty, days: 5, extra_budget_pct: 40}
  after 7 requests (preview and full), 422 {error: nothing_pretty, minutes: 45} after exactly 3, the re-rolls 200
  with attempts 2 / 3 and seeds S+1 / S+2. Two row pairs added for the closure re-request (R2/R3 score the route that
  would SHIP): tripHonest "a pretty detour crossing a closure, re-requested to a dull road, is refused" / "a dull
  detour crossing a closure, re-requested to a pretty road, ships the road (whole 200)"; loopHonest "a pretty loop
  crossing a closure, re-requested to a dull clean loop, keeps the pretty loop and names the crossing" / "... to a
  pretty clean loop, ships the re-request". The harness defaults (R4) and the custom-runs trip bodies (tripFull
  uneven / routeBody, tripRoute scenicRuns / scenicSumming) gained PRETTY_RUNS (score 8); reflectionSites gained
  LoopNothingPretty's constructor line. Full Worker suite, run alone: "Test Files 86 passed (86) / Tests 2492 passed
  (2492)".
- 2026-10-09T05:23:51Z PRE-REVIEW MUTANTS (.artifacts/t0335/mutants.py, each one-line, restored by git checkout; suites tripHonest,
  loopHonest, tripRoute, tripFull): 7/7 CAUGHT. T1 trip scores first.path, not the route after the closure
  re-request: RED "a dull detour crossing a closure, ..." + "a pretty detour crossing a closure, ...". T2 trip check
  moved after the day legs: RED "a full trip whose chosen route scores 0.02 is refused before any day leg is
  requested" + the fail-closed row. T3 TRIP_DETAILS without scenic_score: RED tripFull/tripRoute's whole-request rows
  ("a 5-day trip is exactly 12 requests, ..." and "a 5-day trip: the whole answer, 7 router requests, ..."). L1 third
  seed = seed + 1: RED 4 loopHonest rows. L2 loop never answers nothing_pretty: RED 3. L3 closure re-request accepts a
  dull clean loop: RED "a pretty loop crossing a closure, re-requested to a dull clean loop, ...". L4 nothing_pretty
  only when the LAST attempt was clean: RED "retraced, then clean but dull, then retraced again ...".
- 2026-10-09T05:23:51Z A5: named-tests.json P-SAFE-04 binds the two tripHonest refusal rows and the three-dull loopHonest row by name.
  Follow-up filed: T-0336 (the app reads /trip's and /loop's nothing_pretty, R5).
- 2026-10-09T05:47:46Z RENUMBERED: main took T-0336 (screenshot every screen) while this branch was open, so the follow-up filed above
  as T-0336 is T-0337 (queue/backlog/T-0337-trip-loop-nothing-pretty-client.md); the line above stays as written.
- 2026-10-09T05:47:46Z ACCEPTANCE re-run on the merged head 17080142 (origin/main 4537e7d4, PR #216 T-0329 merged in, no conflict; this
  branch changes no Sources/ or apps/ios file, so no digest row moves and no ios-compile is due):
  - A1/A2/A3/A4 `npx vitest run` tripHonest, loopHonest, trip*, loop*, closures*, requestReadSites, reflectionSites,
    planHonest, isochrone*, surpriseReachParity, routes: "Test Files 26 passed (26) / Tests 1113 passed (1113)". The
    full suite on 0fdfa1a6 (before the merge): "Test Files 86 passed (86) / Tests 2492 passed (2492)".
  - A5 run-named-tests P-SAFE-04 (Swift scratch .build/t0335): "NAMED P-SAFE-04 passed=20/20", exit 0 (on 9d9e977f);
    check-pins-yaml "PINS-YAML ok pins=49 fields=395" exit 0; check-mutate-population "P-PROC-06: every added module
    is covered or allowlisted; the floor of 144 holds" exit 0; queue-check "QUEUE OK (328 tasks)" exit 0.
- 2026-10-09T06:13:25Z PRE-REVIEW M1a CLOSED BY CLASS (agent/claude-opus-5, owner). The finding: scoring only DAY 1 of the chosen
  route (the slice to split.plan[0].end_vertex) SURVIVED the 11 suites, because every /trip row scored one value on every edge, so
  any sub-span scored the same as the whole road. RULED: the class is "a strict sub-span of the chosen route is scored in place of
  the route that ships" (one day, several days, the route minus an edge). MEASURED with oracle.py (.artifacts/t0335/m1a_days.py
  calls route_score/edges_of on the tripHarness road): day d pretty (8) on a dull (2) road scores 0.305999 / 0.305669 / 0.305336
  / 0.305001 / 0.304662 for d = 1..5 (mean ~0.320, p90 0.8, dud ~0.80, 1 episode), and that day alone scores 0.713333. Day d dull
  on a pretty road scores 0.610668 / 0.644331 / 0.644664 / 0.644999 / 0.612005, and that day alone scores 0.020000. Those 10 rows
  catch every span inside one day but miss 299 of the 819 strict sub-spans [a, b) (multi-day and near-whole ones, e.g. days 1-3,
  days 2-5, [0, 39)). A greedy cover over block rows added [8,28) 2-on-8 (0.491452), [0,20) 8-on-2 (0.459378), [0,20) 2-on-8
  (0.457289) and [1,20) 8-on-2 (0.446527, the near-whole spans [0,39) [1,38) [1,39) [1,40) [2,37) [2,38) [2,39) [3,38)). After
  those, 0 of the 819 are uncovered. Added as A6: the 14 rows (it.each over BLOCKS, whole-body through handleTrip, each one also
  checks routeScoreOf against the oracle to 6 places), the two named rows the finding asks for ("pretty day 1 on a dull road ...
  is refused whole-body", "dull day 1 on a pretty road ... ships the whole 200 trip"), and the meta row ("every strict sub-span
  [a, b) of the road has a row whose whole-road verdict differs from that span's": {spans: 819, uncaught: []}).
  - meta RED: with row 14 ([1,20) 8-on-2) removed, `vitest run test/tripHonest.test.ts -t meta` gives "Tests  1 failed | 21 skipped
    (22)". With the row restored it is GREEN.
  - MUTANTS (.artifacts/t0335/m1a_mutants.py, output in m1a_mutants.out). Each one replaces the R2 check with routeScoreOf(cut(a, b)), where cut
    slices the coordinates and shifts the detail runs. The script restores the source byte-for-byte ("restored True"). "prior
    rows" means the two describes that existed before this entry:
    M1a day 1 only: "Tests  6 failed | 17 passed (23)", prior rows failing 0 (MISSED), CAUGHT by "edges [+0, 8) scored 8 ...",
      "edges [+0, 8) scored 2 ...", "edges [+0, 20) scored 2 ...", "edges [1, 20) scored 8 ...", "pretty day 1 on a dull road ...",
      "dull day 1 on a pretty road ...".
    day 3 only: 6 failed, CAUGHT by [16,24) 8, [16,24) 2, [8,28) 2, [1,20) 8. The 2 prior failures are the days-2 closure rows,
      which crash on split.plan[2] being undefined; that is not a catch of the class.
    last day only: 3 failed, prior 0 (MISSED), CAUGHT by [32,40) 8, [32,40) 2, [0,20) 8.
    days 1-3: 5 failed, CAUGHT by [8,28) 2, [0,20) 2, [1,20) 8. The 2 prior failures are the same days-2 crash.
    all but day 1: 2 failed, prior 0 (MISSED), CAUGHT by [8,28) 2, [0,20) 8.
    all but the last edge: 1 failed, prior 0 (MISSED), CAUGHT by [1,20) 8.
  - GREEN on the source as written: `npx vitest run test/tripHonest.test.ts` "Tests  23 passed (23)" (the meta row runs in 104 ms;
    it has a 30 s timeout so a loaded box does not fail it).
- 2026-10-09T06:28:40Z ACCEPTANCE re-run on 37b743cc. `git fetch origin` shows origin/main 4537e7d4, already an ancestor, so there
  is nothing to merge. A1/A2/A3/A4/A6: vitest over trip*, loop*, closures*, requestReadSites, reflectionSites, planHonest,
  isochrone*, surpriseReachParity, routes gives "Test Files 26 passed (26) / Tests 1130 passed (1130)". That is 1113 + the 17 new
  tripHonest rows. A5: queue-check "QUEUE OK (328 tasks)"; check-line-cap "P-SRC-02: 515 Swift files tracked ..., none over 300
  lines" exit 0. PINS.yaml, named-tests.json, Sources/ and apps/ios are unchanged by this entry, so the P-SAFE-04 / pins-yaml /
  digest results quoted above stand.
- 2026-10-09T06:33:36Z RULED on rv1-t0335 FAIL (PR #220, head 876923f4), before any code (agent/claude-opus-5, owner). Both
  findings are population gaps, not wording gaps; each is closed by CLASS, rows as a function of the request.
  - B1 the class: "the /trip refusal body echoes something other than the request's own values" (extra_budget_pct read
    from the cap or default, days from a constant). Every A1/A6 refusal row sent TRIP_BODY (days 5, extra_budget_pct
    defaulted to 40), so the cap and the request's value were the same number. New tripHonest rows: the cross product
    extra_budget_pct {21, 39, 40} x days {2, 5}, each body expected WHOLE as {error: nothing_pretty, days: <the
    request's>, extra_budget_pct: <the request's>} after 7 requests. pct 0/10/20 are not used: rv1 RECORDABLE 1
    measured that this harness's fast path (scored 8) is chosen there and fails ceiling_breached later - a harness
    artifact, not a refusal row.
  - B2 the class: "a seed step of the loop ladder leaves uint32" (seed + 1 or seed + 2 without `>>> 0`). Every loop
    row used SEED = fnv1a32("device-1|2026-10-05"), far from 2^32. New loopHonest rows: the cross product of the two
    seeds at the wrap {0xFFFFFFFE (userId "agO3ON"), 0xFFFFFFFF (userId "v551St")} x answers {[2, 8], [2, 2, 8],
    [2, 2, 2]}; each row asserts fnv1a32(`${user}|2026-10-05`) equals its seed, then the WHOLE answer (200 via
    shipped() or 422 nothing_pretty) and the router seeds, the expected seeds computed as (S + i) % 2^32 (modulo, not
    the source's `>>> 0`). The preimages are rv1's meet-in-the-middle (.artifacts/t0335/preimage.mjs).
  - POPULATION (R6 amended): rv1 shows the Worker harness (services/api/test/mutate/*.mjs) never ran tripHonest or
    loopHonest, so T-0335's own mutants lived in .artifacts only. tripMutants.mjs gains "trip-refusal-pct-cap" (B1:
    extraBudgetPct -> 40, the value of MAX_EXTRA_BUDGET_PCT, written as the literal so no import line is mutated) and
    "trip-refusal-days-5" (the days half of the class); loopMutants.mjs gains "planner-reroll-no-wrap" (B2) and
    "planner-reseed-no-wrap" (the seed + 1 `>>> 0` drop) plus the --only flag tripMutants has. Each TESTS list gains
    its honest suite; each MIN_MUTATIONS floor rises by 2. MISSED at 876923f4's tests, CAUGHT by name after.
  - P-SAFE-04: named-tests.json lists the refusal rows by name, so one B1 row (pct 39, days 2) and one B2 row
    (0xFFFFFFFE, [2, 2, 2]) join it by name.
- 2026-10-09T06:46:18Z rv1 B1/B2 CLOSED BY CLASS (66ade4ce; agent/claude-opus-5, owner). One ruling above amended by
  measurement: pct 21 does NOT reach nothing_pretty in this harness (free answered 200 on the fast path scored 8, paid
  422 ceiling_breached), so rv1 RECORDABLE 1's "21 to 40" is wrong at 21. Ruled: give the harness a dull fast path
  (rv1's other option) - tripHarness.tripRouter gains `firstScenic` (the lambda-0 answer, the fastest path scored 8
  by default, so no other row moves), and the echo rows send the fast road scored 2. That lets the rows reach the
  lower bound too: extra_budget_pct {0, 21, 39, 40} x days {2, 5} x tier {free, paid}, 16 rows plus a meta row
  ({pcts, days} distinct = [4, 2]); each row is the whole 422 {error: nothing_pretty, days, extra_budget_pct} equal
  to the request's own values after 7 requests. loopHonest: 6 rows (seeds 0xFFFFFFFE "agO3ON", 0xFFFFFFFF "v551St" x
  answers [2, 8], [2, 2, 8], [2, 2, 2]) plus a meta row (the seeds the rows step to at or past 2^32: seed + 1 at
  0xFFFFFFFF in 3 rows, seed + 2 at both).
  - HARNESS STALE (found running it, pre-existing): loopMutants.mjs refused "STALE planner-areas-old-seed" and "STALE
    loop-plan-budget" - both anchors occur 0 times on origin/main 4537e7d4 too (the areas line became
    mergeClosures(feed, areas), and LOOP_UPSTREAM_COST moved to its own line); tripMutants.mjs refused "STALE
    planner-details-more" (this branch's TRIP_DETAILS). All three re-anchored to the current lines, same mutation.
  - MISSED at 876923f4's tests (its tripHonest, loopHonest, tripHarness restored into the worktree, the harnesses as
    now, so the honest suites ARE in TESTS): `tripMutants.mjs --only trip-refusal-pct-cap,trip-refusal-days-5`
    "baseline green tests=113", "MISSED trip-refusal-pct-cap", "CAUGHT trip-refusal-days-5 by "a pretty detour crossing
    a closure, re-requested to a dull road, is refused"" (the days half was already caught by the days-2 closure row;
    kept in the population as the other half of the class); `loopMutants.mjs --only
    planner-reseed-no-wrap,planner-reroll-no-wrap` "baseline green tests=37", "MISSED planner-reseed-no-wrap",
    "MISSED planner-reroll-no-wrap", "RESULT caught=0 missed=2 trap=0 of 2 (--only)".
  - CAUGHT by name now: tripMutants --only trip-refusal-pct-cap,trip-refusal-days-5,planner-details-more "baseline
    green tests=130", CAUGHT planner-details-more by "a 5-day trip is exactly 12 requests, reserved first: ...",
    CAUGHT trip-refusal-pct-cap and trip-refusal-days-5 by "extra_budget_pct +0, days 2, 'free': the whole 422
    carries the request's own values", "RESULT caught=3 missed=0 trap=0 of 3 (--only)". loopMutants --only
    planner-reseed-no-wrap,planner-reroll-no-wrap,planner-areas-old-seed,loop-plan-budget "baseline green tests=44",
    CAUGHT planner-reseed-no-wrap by "seed 4294967295, scores [ 2, 8 ]: ...", planner-reroll-no-wrap by "seed
    4294967294, scores [ 2, 2, 8 ]: ...", planner-areas-old-seed by "a loop is at most 3 upstream requests: ...",
    loop-plan-budget by "the quota is reserved once, LOOP_UPSTREAM_COST of it, ...", "RESULT caught=4 missed=0 trap=0
    of 4 (--only)". --prove-floor, both: "prove-floor real population: quiet" (floors 93 and 43).
  - ACCEPTANCE on the merged head (git fetch origin: origin/main 4537e7d4, already an ancestor, "Already up to date"):
    vitest over tripHonest, loopHonest, trip*, loop*, closures*, requestReadSites, reflectionSites, planHonest,
    isochrone*, surpriseReachParity, routes: "Test Files 28 passed (28) / Tests 1184 passed (1184)".
    `python ops/lib/run-named-tests.py P-SAFE-04` "NAMED P-SAFE-04 passed=22/22" (20 + the pct 39 days 2 free echo
    row and the 0xFFFFFFFE [2, 2, 2] wrap row). `python ops/lib/check-mutate-population.py` "P-PROC-06: every added
    module is covered or allowlisted; the floor of 144 holds" exit 0. `python ops/lib/check-pins-yaml.py`
    "PINS-YAML ok pins=49 fields=395" exit 0. `bash ops/queue-check` "QUEUE OK (328 tasks)" exit 0. Line counts:
    tripHonest 202, loopHonest 150, tripHarness 152, loopMutants.mjs 184, tripMutants.mjs 250 (all under 300).
- 2026-10-09T07:22:57Z REVIEW PASS round 3 (agent/rv3-t0335, not the owner), PR #220 head 8867f314. Closes rv2-t0335's
  one blocker (stale base). (1) Merge 8867f314 = 4e593819 + origin/main 564e6626. `git merge-tree --write-tree`
  conflicts only in ops/lib/named-tests.json, and the merge tree differs from merge-tree's result only in that file
  (just the conflict resolution, no other hand edits). Comparing named-tests by key (pin, runner, file, name):
  parent1 1381 rows, parent2 1378, merge 1383, 0 missing from either parent, 0 in neither. P-SAFE-04 keeps
  planBackRoads (T-0334) beside tripHonest/loopHonest. (2) Gates: `python ops/lib/check-pins-yaml.py`
  "PINS-YAML ok pins=49 fields=395" exit 0; `bash ops/queue-check` "QUEUE OK (328 tasks)" exit 0.
  `python ops/lib/run-named-tests.py P-SAFE-04` "NAMED P-SAFE-04 passed=24/24" exit 0, run in .worktrees/T-0335 (clean,
  same HEAD). In a fresh rv3 worktree it twice failed the same way: swift crashed with "error: fatalError" while
  compiling ScenicKit (first run: index-store "permission denied"), so the tests never ran and no test failed.
  I take that as a local toolchain problem. The PR changes no Swift. Mutants (rv2's mut.py), vitest tripHonest+loopHonest: baseline 54/54.
  X1 (422 echoes MAX_EXTRA_BUDGET_PCT) RED 12 failed; X2 (reroll seed+2 without >>>0) RED 4 failed, both
  "seed 42949672xx ... every router seed stay uint32"; src restored. (3) `gh pr checks 220` core pass 5m39s,
  pins-source-only pass 1m57s on head 8867f314; mergeStateStatus CLEAN. (4) After `git fetch origin`,
  `git merge-base --is-ancestor origin/main origin/task/T-0335` exit 0 (origin/main 564e6626), so no drift.
