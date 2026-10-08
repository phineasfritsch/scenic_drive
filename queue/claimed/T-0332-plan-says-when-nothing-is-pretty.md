---
id: T-0332
title: /plan is honest when nothing pretty is reachable - the Worker scores the chosen route with RouteScore (parity with ScenicKit's, threshold 0.45) and answers a typed honest failure ("not much pretty within N minutes of this drive") with the +40 and all-back-roads offers, instead of presenting a dull route as scenic
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-08T20:54:45Z
lease_expires_at: 2026-10-09T06:54:45Z
worktree: .worktrees/T-0332
branch: task/T-0332
exclusive: []
touches: [services/api/src/, services/api/test/, Sources/ScenicAPIClient/, Sources/ScenicKit/, Tests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/, ops/mutate/, ops/lib/check-safety-disclaimer-linked-digests.txt, pins/PINS.yaml]
pins_affected: [P-PROD-01, P-SAFE-04]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "A1 PARITY: services/api/src/routeScore.ts ports Sources/ScenicKit/Scoring/RouteScore.swift (the same weights, thresholds and boundaryTolerance) over tableRows(path) (planWaypoints.ts, the PlanTable port): every row of positive metres with a scenic_score becomes an edge of score/10, unscored metres are left out. Tests/Fixtures/t0332/route-scores.json, written by Tests/Fixtures/t0332/oracle.py (an independent Python reading), holds value, mean, p90, dudFraction, episodeCount and totalLength for ALL 44 recorded router bodies under Tests/Fixtures carrying scenic_score (24 below 0.45, 20 at or above, R2). routeScoreParity.test.ts (through routeScoreOf, the function planScenic calls) and Swift RouteScoreParityTests (through RouteScore(edges: PlanTable(path:).scoredEdges)) each equal that file field for field to 1e-9, assert the 44-file / 24-20 split, and assert the golden lists exactly the fixture files that carry scenic_score (nothing skipped)."
  - "A2 BOUNDS, one table, every row a whole-object equality to an independent recomputation: isHonestFailure (the predicate planScenic calls) is false at exactly 0.45 and true at the next double below; through scoreEdges (the function routeScoreOf calls) scores 0.25 / the next double above straddle dudThreshold, 0.6 / the next double above straddle episodeThreshold, an above-threshold run of exactly 800 m is an episode, 800 m less 4e-7 m still is (inside the 1e-9-of-route tolerance, R10) and 799.999 m is not, the 90th-percentile boundary on [9000 m @ 0.1, 1000 m @ 0.9] split k = 1..12 ways gives 0.1 every time; through routeScoreOf, no scenic_score detail or every scored row 0 m is null, and an encoded score of 11 or -1 makes the route null (RouteScore's isValid, as Swift) - never clamped."
  - "A3 POPULATION, MISSED then CAUGHT through handlePlan (the shipping entry point) on the recorded t0221 westwood-malibu pair at budget_minutes 25: on d6b48cc0 the answer is 200 with lambda 3.25 (RouteScore 0.226, R2 - quoted red by test name in the Log); after, it is 422 whose WHOLE body equals {error: nothing_pretty, budget_minutes: 25, more_time_minutes: 65, back_roads_eta_s: E}, E recomputed in the test from the body the router fake answers lambda 8 with (the recorded lambda-4 body: no lambda-8 recording exists for that pair, R5), with no plan_token remembered. The santa-monica-topanga pair (chosen route 0.491) still answers its whole previous 200 body (planWire's existing equality, unedited)."
  - "A4 OFFERS, a table through handlePlan: more_time_minutes is budget + 40 when that is <= MAX_BUDGET_MINUTES (budget 140 -> 180 exactly) and null when it is not (the next double above 140, and 180); back_roads_eta_s is the MAX_LAMBDA (8) route's own duration in seconds when that route's routeScoreOf is >= 0.45, null when it scores below 0.45, null when it has no score, null when the router refuses it; the back-roads request carries buildCustomModel(8, closures) compared whole; a refused plan's upstream calls stay <= PLAN_UPSTREAM_COST (worst case 1 + 6 + 1 + 1 = 9, counted) and the quota is reserved exactly once."
  - "A5 FAIL CLOSED: a chosen route with no scenic_score detail answers 422 nothing_pretty, never 200 (curveRouter's synthetic bodies gain a default scenic_score run so every pre-existing /plan test keeps its whole answer); a reroute (T-0319 planReroute) is exempt and keeps its whole previous answer (R6)."
  - "A6 CLIENT: Sources/ScenicAPIClient PlanResponseReader maps (422, nothing_pretty) to PlanError.nothingPretty(NothingPrettyOffer) compared whole, over a table: every field at each bound (budget_minutes 0 and 180 accepted, -0.000...1 and 180.000...1 by nextafter refused; more_time_minutes null / budget + 40; back_roads_eta_s null / positive), and each field missing, a string, a bool, or out of range -> unexpectedResponse(status: 422); nothing_pretty at any other status is not trusted. PlanError.nothingPretty.failure == PlanSheetFailure.nothingPretty and PlanFailureCopy.of(.nothingPretty) equals its whole copy (R7)."
  - "A7 PINS + GATES: P-SAFE-04's named-tests.json rows gain the A3/A4 tests (a refusal carries no route, so the ceiling holds; the back-roads ETA is an offer, never a returned route); P-PROD-01 stays TODO under T-0012 (R8); digests re-approved in ops/lib/check-safety-disclaimer-linked-digests.txt; ios-compile success on the branch; check-safety-disclaimer, check-mutate-population, check-line-cap, check-pins-yaml and queue-check green on the merged head."
---
## Brief

Plan, Problem A step 3: "Honest failure = the chosen route has no scenic episode (RouteScore < 0.45) -> 'not much
pretty within 25 minutes of this drive' + offer +40 / 'all back roads' (a lambda=8 variant, shown with its real ETA)."
Measured 2026-10-08 by T-0327's owner (PR #213): ops/plan issues westwood-malibu +25 although RouteScore calls it an
honest failure (value 0.226 < 0.45, dud 0.500, about half its metres PCH trunk at score 0); ops/plan never consults
RouteScore. grep of services/api/src finds no RouteScore and no honest-failure path: the Worker's /plan answers the
bisection's route whatever it scores. Owner intent (memory owner-route-intent): Saddle Peak beats PCH; a dull
route sold as scenic is the failure this product exists to avoid.

MEASURE FIRST, then write the acceptance (CLAUDE.md): what /plan's answer and PlanError / PlanResult kinds carry today
(app copy for an honest failure may already exist from T-0294), what path details the Worker holds per edge
(scenic_score, distance) to compute RouteScore, how the TS score is held to ScenicKit's (a shared fixture through
both, full equality to 1e-9), how many fixtures in Tests/Fixtures and services/api/test fall each side of 0.45, and
whether the +40 / all-back-roads offers are one more request each (budget ceiling and P-COST-04's request cap).

## Log
- 2026-10-08T19:42:35Z filed by agent/claude-opus-5 (orchestrator) from T-0327's stillOpen finding.
- 2026-10-08T20:54:45Z claimed by agent/claude-opus-5; lease until 2026-10-09T06:54:45Z
- 2026-10-08T21:00:59Z MEASURED (agent/claude-opus-5, owner), before any code:
  - M1 what /plan answers today: plan.ts `failure()` maps PlanFailure `no_scenic_alternative` -> 422, `ceiling_breached` /
    `no_recorded_lambda` -> 500, BudgetError / RouteError / PlanBudgetExceeded -> 502 `no_route`. grep RouteScore over
    services/api/src: 0 hits. scenicPlanner.ts returns `chosen` whatever it scores. The app side: PlanError (13 cases,
    Sources/ScenicAPIClient) -> PlanSheetFailure (13 cases, Sources/ScenicKit/PlanSheet) -> PlanFailureCopy.of, a
    payload-free line + PlanFailureAction; apps/ios uses it only as `PlanFailureCopy.of(failure)` (PlanSheetScreen:126),
    no switch over PlanSheetFailure there. No honest-failure copy exists (T-0294 has `noScenicAlternative` only).
  - M2 what the Worker holds per edge: the router body's `details` (scenic_score, road_class, osm_way_id + hazards) and
    the coordinate list; planWaypoints.ts `tableRows` is already the port of PlanTable's row cutting with the Swift
    haversine (EARTH_RADIUS_METERS 6371008.8). T-0327's AutopsyReport (PR #213, unmerged) builds RouteScore edges the
    same way: PlanTable rows with a scenic_score, `score / 10`, unscored metres left out. No Sources/ entry point builds
    ScoredEdges from a path on main.
  - M3 the population, RouteScore over every recorded router body under Tests/Fixtures carrying scenic_score (44 files;
    .artifacts/t0332/measure.py, an independent Python reading): 24 below 0.45, 20 at or above. services/api/test holds
    no router bodies of its own (it imports Tests/Fixtures/t0221/santa-monica-topanga). The rows the predicate turns on:
    westwood-malibu lambda-3.25 0.225555 (mean 0.251, p90 0.6, dud 0.500, 0 episodes - T-0327's 0.226 to 3 places),
    lambda-4 / lambda-3.5 0.647864; santa-monica-topanga lambda-4..7.75 0.491097 (the harness's 200 stays 200),
    its fastest / lambda-0 0.443212 (just below); westwood-woodland-hills fastest 0.000000, lambda-4..7.75 0.547233;
    t0239 topanga-malibu lambda-8 0.655826 (a back-roads offer would show), zuma-agoura lambda-8 0.399469 (a back-roads
    offer would itself be dull).
  - M4 cost: searchLambda measures 0 then bisects mid-points of [0, 8] - it never measures 8 - so the back-roads ETA is
    one more router request. Worst case 1 fastest + 6 search + 1 closure re-request + 1 back-roads = 9 <=
    PLAN_UPSTREAM_COST 12 (P-COST-04), inside the same guardedPlan reservation. The +40 offer is a number the client
    re-plans with: no request on this answer, one more plan only if the driver takes it.
- 2026-10-08T21:00:59Z RULED (agent/claude-opus-5, owner):
  - R1 the Worker scores `chosen` (after the T-0286 closure re-request, so the route that would ship) with routeScoreOf =
    RouteScore over tableRows; value < 0.45 (RouteScore.honestFailureThreshold, not re-tuned here) throws HonestFailure,
    answered 422 `nothing_pretty`. 422 because it is the same kind of answer as `no_scenic_alternative`: the inputs are
    fine, the planner will not stand behind a result.
  - R2 parity is held by a golden over all 44 recorded bodies written by an independent Python oracle, read by BOTH the
    TS and the Swift suite to 1e-9 (a shared fixture through both, the Brief's ask) - not TS-vs-Swift through a file
    one of them wrote.
  - R3 a chosen route that cannot be scored (no scenic_score detail, or an invalid encoded score) is an honest failure:
    fail closed; selling an unscored route as scenic is the defect. The synthetic curveRouter bodies gain a default
    scenic_score run of 8 so no existing /plan test's answer moves.
  - R4 body: {error, budget_minutes (the request's own), more_time_minutes (budget + 40, or null past
    MAX_BUDGET_MINUTES 180), back_roads_eta_s (or null)}. No route, no waypoints, no plan_token: a refusal ships
    nothing to drive, so P-SAFE-04's ceiling is untouched - the back-roads ETA may exceed fastest + budget and is shown
    as an offer with its real ETA, exactly as the plan words it.
  - R5 back-roads = the route at MAX_LAMBDA 8 with the same closures model, offered only when ITS routeScoreOf >= 0.45:
    offering a dull back-roads route repeats the dishonesty (zuma-agoura's lambda-8 is 0.399). A router refusal of that
    one request is "no offer", never a failed answer; quota / kill errors still propagate. westwood-malibu has no
    lambda-8 recording, so its A3 test answers lambda 8 with the recorded lambda-4 body (0.648), named as such.
  - R6 reroute (T-0319 planReroute) is exempt: a driver already on the road gets the rest of the drive they accepted.
    Loop / isochrone / trip planners are out of this Brief's /plan scope (follow-up filed if budget allows).
  - R7 the app: PlanError.nothingPretty(NothingPrettyOffer) carries the offers; PlanSheetFailure.nothingPretty's copy is
    payload-free like every other row ("Not much pretty within reach of this drive. More time might find some.",
    action .chooseAnotherPlace). The buttons that act on +40 / back-roads (a client re-plan at budget + 40, and a
    request variant for lambda 8) are app UI + a request field: filed as a follow-up, not claimed here.
  - R8 P-PROD-01 is a TODO pending T-0012 (ETL / profile / Gates parity); this task changes none of those three, and the
    motorway invariant holds - a motorway stretch is scored 0 and counted as dud, never excluded. Not edited.
  - R9 no ops/mutate population: CLAUDE.md requires one for a numeric module under services/etl/etl/ or Sources/; the
    Sources/ addition is PlanTable.scoredEdges (a filter + divide, held whole by A1's 44-file golden). The TS port is
    held by A1 + A2's bound table.
- 2026-10-08T21:45:50Z RULED R10 (agent/claude-opus-5, owner): A2 as first written said "the next double below 800 m
  is not an episode". RouteScore.swift's episode bound is `run >= 800 - total * 1e-9` on purpose (its own comment and
  RouteScoreBoundaryTests), so the next double below 800 m IS an episode in both ports. A2 now names the tolerated
  bound: 800 m and 800 m less 4e-7 m are episodes, 799.999 m is not. The acceptance changed, not the code.
- 2026-10-08T21:45:50Z RED by name on d6b48cc0's src (the tests written first, `npx vitest run test/planHonest.test.ts
  test/planReroute.test.ts`, before scenicPlanner/plan changed): 8 failed - "westwood-malibu +25 (RouteScore 0.226)
  answers nothing_pretty with both offers, never a 200 route" received `{ status: 200, ... "lambda": 3.25, "eta_s":
  1904.238, "fastest_eta_s": 1667.261, "plan_token": null ... }` (the population MISSED: the dull route sold as
  scenic), and the six A4 rows plus the R3 fail-closed row each received 200. The reroute-exempt row and "a pretty
  chosen route still answers 200" were green before and after (they guard against over-applying the refusal).
- 2026-10-08T21:45:50Z GREEN: same files 19/19 after honestFailure.ts + the planScenic / plan.ts change (CAUGHT by name:
  westwood-malibu +25 now 422 nothing_pretty, more 65, back_roads_eta_s = the lambda-8 answer's own time). The first
  full suite run then failed 38: closuresCrossing's 35 synthetic answers carried no scenic_score (now honest failures
  under R3 - given a per-edge score of 8, nothing else in the rows changed), reflectionSites (HonestFailure's
  constructor added to its whitelist), requestReadSites (a comment of mine said `.json`; reworded) and
  configAnswerPath's known 5 s timeout (environment; green re-run alone). A1/A2: routeScoreParity 3/3 and
  routeScoreBounds 25/25 through vitest; Swift `swift test --filter
  "RouteScoreParityTests|PlanFailureCopyTests|PlanSheetGateTests|NothingPrettyReaderTests|PlanClientResponseTests|RouteScore"`:
  "Test run with 40 tests in 6 suites passed", XCTest "Executed 30 tests, with 0 failures".
- 2026-10-08T21:45:50Z PRE-REVIEW MUTANTS (.artifacts/t0332/mutants.sh, each restored): M1 more_time `<=` -> `<`
  CAUGHT ("budget 140 offers exactly 180"); M2 dud `<=` -> `<` CAUGHT ("scoreEdges: 0.25 is a dud"); M3 offer a dull
  back-roads route CAUGHT ("a dull back-roads route is not offered" + 2); M4 an unscored route is not a failure
  CAUGHT ("isHonestFailure: an unscorable route (null) is" + 2); M5 episode bound `>= 800 - tol` -> `> 800` CAUGHT
  ("scoreEdges: 0.9 over exactly 800 m is an episode" + 1). 5/5.

