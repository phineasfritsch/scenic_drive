---
id: T-0230
title: ScenicKit/ops/plan - honest failure wired (plan:117): RouteScore over the chosen route < 0.45 -> a named plan state printed by ops/plan, the +40 / 'all back roads' offer at its real ETA, and couldNotUseBudget as a product state instead of a doc comment
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T13:33:10Z
lease_expires_at: 2026-10-17T13:33:10Z
worktree: .worktrees/T-0230
branch: task/T-0230
exclusive: []
touches: [Sources/ScenicKit/, Sources/ScenicPlanCLI/AutopsyCommand.swift, ops/plan, ops/mutate/, Tests/, ops/lib/check-safety-disclaimer-linked-digests.txt, queue/done/T-0182-ops-plan-o-d-b-the-m3-cli-exit-an-apple-maps-url-a.md]
pins_affected: []
reviewer: null
depends_on: [T-0182]
verify: [ops/test, ops/check-pins]
acceptance:
  - "A1 WIRED. ScenicPlanner.plan (the symbol PlanCommand.run, i.e. ops/plan, calls) scores the chosen route with RouteScore over PlanTable.scoredEdges after the ceiling and actually-different guards, and RouteScore.isHonestFailure gains its first caller in Sources; an honest failure or an unscorable route throws PlanFailure.nothingPretty(PlanNothingPretty) - no plan, no table, no URL; ops/plan prints 'ops/plan REFUSED: not much pretty within N minutes of this drive' plus the offer lines and exits 3 (R2, R3)"
  - "A2 OFFERS, whole-value equality through ScenicPlanner.plan on stub routers: more time = budget + 2400 s; all back roads = the lambda 8 (LambdaSearch.maxLambda) route at its MEASURED duration, reused when the search measured 8 and requested once when it did not, offered only when its own RouteScore >= 0.45 (dull -> not offered, score kept), and a noRecordedResponse/routerRefused on that request -> unmeasured with the reason, never a failed answer (R4)"
  - "A3 FLOOR BOUNDS through ScenicPlanner.plan, one table, geometries found at run time: RouteScore nextDown(0.45) -> nothingPretty; exactly 0.45 -> a plan; nextUp(0.45) -> a plan; an unscored chosen route (RouteScore nil, the NaN/invalid row) -> nothingPretty; the motorway-shoulder fixture (integer image of RouteScore.swift:84's realistic route) -> nothingPretty, RED by name before the wiring (R9, R10)"
  - "A4 REAL DATA: PlanCommand.run over t0221/westwood-malibu at +25 throws nothingPretty with RouteScore 0.225555 and back roads unmeasured (no lambda-8 recording), RED by name before the wiring; santa-monica-topanga and westwood-woodland-hills still plan with their URLs unchanged (R8)"
  - "A5 couldNotUseBudget: ScenicPlan.couldNotUseBudget = budget > 0 and the measured duration < fastest + 0.5 * budget; report() prints a STATE couldNotUseBudget line before TABLE; bound table through ScenicPlanner.plan at fastest + 0.5B - 1 ms (true), exact (false), + 1 ms (false), budget 0 (false), NaN budget (budgetCeilingBreached); a stub solver claiming usedBudget true does not hide it; santa-monica-topanga +25 prints it (R5)"
  - "A6 RECORD: T-0182's R4 corrected in a dated Log line here with a pointer line on T-0182's Log (R6); ops/mutate/plan.py MIN_MUTATIONS 31 -> 42 with the eleven new mutants (honest/*, budget-state/*) caught by name (--only run quoted); swift test count line for the touched suites; check-safety-disclaimer, check-mutate-population.py, check-mutate-only.py, check-line-cap, check-pins-yaml.py, check-exec-bits, queue-check bare"
---
## Brief

From the 14:13 panel (CODE, grounded): RouteScore has zero callers in Sources; PlanFailure has no honest-failure case;
the CLI today refuses the prettiest road in the canyon window under a message the Log mislabels. plan:284 makes
ops/plan the M3 exit and step 3 of Problem A is its honest failure. Ranked before T-0221 in slot order.

## Log
- 2026-09-19T21:54:54Z filed by agent/claude-opus-5[1m] (14:13 panel, grounded on pins/floor_*.txt, T-0203 Log :34, queue.py:541-548, RouteScore.swift:92-94). Not started; after PR #124 merges.
- 2026-10-16T13:33:10Z claimed by agent/claude-opus-5; lease until 2026-10-17T13:33:10Z
- 2026-10-16T13:48:18Z MEASURED by agent/claude-opus-5 (owner), before any code:
  - M1 callers. `grep -rn RouteScore Sources/` outside Scoring/ finds only PlanTable.scoredEdges (T-0332's edge
    builder) and ScenicAPIClient doc comments; ScenicPlanner.swift and PlanCommand.swift never read it.
    PlanFailure has 7 cases, none honest failure. couldNotUseBudget exists only as BudgetOutcome.swift's doc
    comment; report() prints `used-budget=<bool>` inside the LAMBDA line and no state.
  - M2 ops/plan today: main.swift maps any PlanFailure to `ops/plan REFUSED: <description>` on stderr, exit 3;
    a plan is `ROUTER` + ScenicPlan.report() + `URL`, exit 0. route-autopsy (AutopsyCommand) plans through the
    same ScenicPlanner.plan, and its golden is westwood-malibu.
  - M3 the population, through the SHIPPED ScenicPlanner.plan (LambdaSearch, 6 evaluations) over every planner
    recording on this box (Tests/Fixtures/*/ with fastest.json + lambda-*.json: 7 dirs) at every whole-minute
    budget 0..60 (throwaway test, not committed; 427 cells):
      t0182/plan-pair            B=20..60 lambda 7.75 RouteScore 0.655826 (mean 0.641 p90 0.7 dud 0.025 ep 4)
      t0221/santa-monica-topanga B=3..60  lambda 7.75 RouteScore 0.491097
      t0221/westwood-malibu      B=4..31  lambda 3.25 RouteScore 0.225555 (B=0..3 notActuallyDifferent)
      t0221/westwood-woodland-hills B=19..60 lambda 7.75 RouteScore 0.547233
      t0182/t0213-pair, t0239/topanga-malibu, t0239/zuma-agoura: never plan under LambdaSearch (no recording at
      lambda 0 / 4 - t0213-pair holds only lambda 0 for a stub solver, t0239 holds alternatives-* menu bodies).
    Plannable cells 169; below 0.45: 28 (16.6%, all westwood-malibu); distinct chosen routes 4, below 1.
    T-0332 M3 over all 44 recorded bodies (any lambda): 24 below, 20 at or above.
    used-budget false (the couldNotUseBudget cells): plan-pair B=40..60, santa-monica-topanga B=5..60
    (+25 returns 22m26s over fastest 20m14s: 132 s of 1500), westwood-malibu B=8..31, woodland-hills B=37..60.
  - M4 lambda 8: no planner recording carries lambda-8.json (ls of the 7 dirs); LambdaSearch measures 0 then
    mid-points of [0, 8] and never 8, so the back-roads ETA is one more request on a live router and
    noRecordedResponse on every recorded pair.
  - M5 floor reachability in floating point (python model of RouteScore's operation order, .build/, not
    committed): [4, 6] at equal lengths lands on nextDown(0.45) or nextUp(0.45) and never on 0.45; [2, 8, 5] at
    equal lengths under 800 m (dud 1/3, no episode) lands on exactly 0.45 for ~10% of lengths. Haversine's
    last bits are libm's, so the geometries are searched at test run time, never hard-coded.
- 2026-10-16T13:48:18Z RULED (agent/claude-opus-5, owner):
  - R1 THE FLOOR STAYS 0.45 on the shipped scale. Over the LA population M3 it is neither unreachable nor
    always hit (1 of 4 chosen routes, 28 of 169 cells; 24 of 44 bodies), and it is the Worker's floor (T-0332
    R1) - moving it here would split app and CLI. T-0171's objection is about the REFERENCE population of the
    scale (a flat region ranks like a pass), which this population cannot test; it stays T-0171's.
  - R2 REFUSAL, NOT A PLAN. Nothing-pretty is thrown from ScenicPlanner.plan as PlanFailure.nothingPretty: the
    defect T-0332's Brief measured was that ops/plan ISSUES westwood-malibu +25; printing the state above a
    table and a URL would still issue it. main.swift's existing PlanFailure branch prints it and exits 3 - no
    edit to main.swift or PlanCommand.swift. Same answer as the Worker's 422 and the app's PlanError.nothingPretty.
  - R3 ORDER AND FAIL-CLOSED. Ceiling, then actually-different, then the score - a nothing-pretty refusal is
    never a ceiling breach in disguise. A chosen route with no scored metres (RouteScore nil) is nothing-pretty
    (T-0332 R3). The stub routers of ScenicPlannerMetaTests and PlanCeilingOverLATests gain a scenic_score run
    of 8 so no existing assertion moves; their assertions are not edited.
  - R4 OFFERS. more time = budget + 40 min in seconds, no cap (PlanArguments has no maximum; the Worker's 180 is
    MAX_BUDGET_MINUTES, which ScenicKit does not carry). all back roads = the lambda-8 route at its measured
    duration, reused from the search's measurements when present; offered only when ITS RouteScore >= 0.45
    (T-0332 R5: a dull back-roads offer repeats the dishonesty); noRecordedResponse / routerRefused on that
    one request -> unmeasured with the reason printed; any other failure propagates. The offer may exceed
    fastest + budget: nothing is planned, so P-SAFE-04's ceiling is untouched.
  - R5 couldNotUseBudget is a ScenicPlan property computed from the plan's own measured numbers (never
    outcome.usedBudget - a bound read from the thing under test is not a bound), mirroring LambdaSearch's
    `budget == 0 ||` and plan:214's `ETA >= T_fast + 0.5*B`; printed as a STATE line before TABLE. RoutePath
    durations are integer milliseconds, so just-below / just-above are +-1 ms, the input's resolution.
  - R6 T-0182 R4 IS WRONG and is corrected here (next line) with a pointer appended to T-0182's Log: touches
    gain that one queue/done file.
  - R7 route-autopsy explains a route, including a nothing-pretty one (its golden IS westwood-malibu), so it
    calls the planner's pre-gate stage ScenicPlanner.checkedRoute (ceiling + actually-different, no score
    gate); plan() is checkedRoute + the gate. touches gain Sources/ScenicPlanCLI/AutopsyCommand.swift (one
    call site) and the digest table; RouteAutopsyBoundaryTests' direct planner call follows it.
  - R8 PlanCLILARecordingTests: westwood-malibu leaves the issued-plan table (it is not a plan any more) and
    gets its own nothing-pretty test through PlanCommand.run - the real-data RED.
  - R9 the motorway fixture: RouteScore.swift:84's realistic route (0.78-0.83) is not encodable in the graph's
    integer scenic_score, so the planner-level fixture is its integer image - 8 km motorway at 0, 4.2 km canyon
    at 8, arterial at 2 either side - asserted below 0.45 by the test before it asserts the refusal.
  - R10 named type: PlanNothingPretty (ScenicAPIClient already owns NothingPrettyOffer / LoopNothingPretty /
    TripNothingPretty); one type per file.
- 2026-10-16T13:48:18Z CORRECTION OF T-0182 R4 (agent/claude-opus-5): T-0182's R4 calls the actually-different
  refusal over the score-8 Topanga corridor (t0213-pair) "the plan's own 'not much pretty within 25 minutes'
  state". It is not. notActuallyDifferent = the chosen route's way-id Jaccard with the fastest route >= 0.6 (the
  scenic search found no other road); nothingPretty = the chosen route's RouteScore < 0.45 (the road it found is
  dull). A score-8 canyon is the opposite of dull. After this task the two are separate PlanFailure cases with
  separate tests; t0213-pair stays the notActuallyDifferent witness.
- 2026-10-16T13:57:30Z RED BY NAME (agent/claude-opus-5): types, checkedRoute and the tests in place, the gate and
  couldNotUseBudget NOT wired (plan() returned the checked route; couldNotUseBudget was `false`):
  `swift test --filter "ScenicPlannerHonestFailureTests|PlanCLILARecordingTests|ScenicPlannerMetaTests|PlanCeilingOverLATests|RouteAutopsy|ScenicPlanGoldenTests"`
  -> "Test run with 35 tests in 8 suites failed after 1.684 seconds with 13 issues"; the eight failing, by name:
    "the floor through ScenicPlanner.plan: nextDown(0.45) refused, exactly 0.45 and nextUp(0.45) planned" (:121, the nextDown row; the exact and nextUp rows planned - all three geometries found)
    "the motorway-shoulder route (RouteScore.swift's realistic fixture, integer image) is not much pretty"
    "a chosen route with no scored road is refused as nothingPretty, fail closed (the NaN/invalid row)"
    "all back roads reuses a lambda 8 the search measured: no extra request, its measured ETA, +40 printed"
    "all back roads not measured by the search is requested exactly once, after the search"
    "a dull or unscored back-roads route is not offered; a refused one is unmeasured; malformed propagates" (4 issues)
    "couldNotUseBudget: fastest + 0.5B - 1 ms true, exact and + 1 ms false, budget 0 false, NaN refused" (2 issues)
    "westwood-malibu +25 is not much pretty: ops/plan refuses it with the two offers and issues nothing" (:162 "Issue recorded" - ops/plan issued it)
  Every pre-existing test in those suites passed with the scored stubs (R3) and the autopsy on checkedRoute (R7).
- 2026-10-16T13:58:08Z GREEN (agent/claude-opus-5): the gate (plan() = search + RouteScore + throw) and
  couldNotUseBudget wired; same filter -> "Test run with 35 tests in 8 suites passed after 2.033 seconds". Whole
  root suite: "Test run with 897 tests in 183 suites passed after 23.545 seconds" (XCTest: 51 tests, 1 skipped, 0
  failures). Committed 0fa71b2e.
- 2026-10-16T14:10:37Z GATES (bare, agent/claude-opus-5): check-safety-disclaimer exit 0 (after the five digest rows: four
  re-approved, PlanNothingPretty.swift added); check-mutate-population.py "P-PROC-06: every added module is covered
  or allowlisted; the floor of 165 holds" exit 0; check-mutate-only.py "NAME-PAIRS OK".
- 2026-10-16T14:30:34Z MUTANTS + LINE CAP (agent/claude-opus-5): `SCENIC_MUTATE_SCRATCH=.../.build/t-0230-mutate python ops/mutate/plan.py --only honest/,budget-state/`
  on 0fa71b2e -> "population 42 mutations over 11 modules ... (running 11 selected)"; CAUGHT honest/gate-never-fires,
  honest/unscored-route-passes, honest/floor-inclusive, honest/floor-raised, honest/floor-lowered,
  honest/back-roads-offered-when-dull, honest/back-roads-always-re-requested, honest/back-roads-refusal-fails-the-answer,
  honest/more-time-is-plus-30, budget-state/inclusive-at-half, budget-state/whole-budget-instead-of-half;
  "caught 11 of 11   trapped 0   compile-only 0   MISSED 0   skipped 0". The 31 pre-existing mutants were not re-run
  (owner-approved faster-verification rule: rounds re-run the touched rows); their anchors are untouched
  (ScenicPlanner's two guard lines and the ceiling line moved into search() unchanged). --prove-floor: one mutation
  REFUSED (expected at least 42), an unmutated subject REFUSED, the shipped table accepted.
  check-line-cap: "P-SRC-02: 680 Swift files tracked (Sources=327, Tests=243, apps/ios=110), none over 300 lines";
  wc -l: ScenicPlanner.swift 149, ScenicPlan.swift 118, PlanNothingPretty.swift 79,
  ScenicPlannerHonestFailureTests.swift 231, PlanCLILARecordingTests.swift 179 (ops/mutate/plan.py 313: P-SRC-02 is
  Swift-only; hazards.py 604, handoff.py 643, segmentscore.py 648 are the precedent).
- 2026-10-16T14:42:50Z CORRECTION + ACCEPTANCE RE-RUN (agent/claude-opus-5): running ops/plan for the record showed the STATE
  couldNotUseBudget line printed AFTER the TABLE line, not before it as R5/A5 say. 610eabb6 moves it above TABLE,
  re-approves ScenicPlan.swift's digest row, adds an adjacency check to the stub table and adds
  PlanCLILARecordingTests "santa-monica-topanga +25 prints couldNotUseBudget above its table; westwood-woodland-hills
  does not". Touched rows re-run on 610eabb6: `plan.py --only budget-state/,honest/gate-never-fires` -> "caught 3 of 3
  trapped 0 compile-only 0 MISSED 0 skipped 0". wc -l ScenicPlan.swift 120, ScenicPlannerHonestFailureTests.swift 235,
  PlanCLILARecordingTests.swift 194.
  A1/A4 ops/plan, recorded (`SCENIC_PLAN_SCRATCH=.build/t-0230 bash ops/plan 34.0669,-118.4399 34.0356,-118.6894 25
  --recorded Tests/Fixtures/t0221/westwood-malibu`): exit 3, stdout empty, stderr:
    ops/plan REFUSED: not much pretty within 25 minutes of this drive: RouteScore 0.226 is under the 0.45 floor
    OFFER more-time: plan again with 65 minutes of extra time (+40 minutes)
    NO-OFFER all-back-roads: lambda 8 was not measured (no recorded response at lambda 8.0)
  santa-monica-topanga +25: exit 0, a plan with "STATE couldNotUseBudget returned=22m26s under
  fastest+half-the-budget=32m44s" (asserted by the test above).
  A2/A3/A5: the 6 ScenicPlannerHonestFailureTests tests plus the stub-table rows, green. Touched suites: "Test run
  with 36 tests in 8 suites passed". Whole root suite on b6955a99 (code identical to 0fa71b2e): "Test run with 897
  tests in 183 suites passed after 14.142 seconds".
  A6 gates, bare, on b6955a99: check-pins-yaml "PINS-YAML ok pins=51 fields=411"; check-exec-bits "P-OPS-01: 230
  files, 23 required present, all modes correct"; queue-check "QUEUE OK (368 tasks)"; check-safety-disclaimer exit 0
  (also exit 0 on 610eabb6); check-mutate-population "the floor of 165 holds"; check-mutate-only "NAME-PAIRS OK";
  check-line-cap "none over 300 lines" (on 0fa71b2e). origin/main b54f24e2 is an ancestor (fetched in the main
  checkout; nothing to merge yet - merged again below if it moves).
- 2026-10-16T16:00:57Z rv1 FIX (agent/claude-opus-5, owner; rv1 FAIL by agent/rv1-t-0230). Each finding closed by class.
  B1 (the back-roads offer's own floor, ScenicPlanner.backRoads' guard): new suite PlanNothingPrettyBoundsTests,
  "all back roads at lambda 8: nextDown(0.45) is dull, exactly 0.45 and nextUp(0.45) are offered" - the three
  floorRows() geometries placed at lambda 8 behind the dull chosen route, whole PlanNothingPretty equality
  (.dull/.offered at duration 2700 with the target score), requested == [4, 8], and the third lines() row whole.
  B2 (PlanNothingPretty.minutes' bounds): "ops/plan's refusal lines through ScenicPlanner.plan, whole, at budgets 0,
  59, 60, 61, 90 and 1500 s" - an unscored chosen route at 1800 s refused at each budget, whole state equality and
  lines() compared WHOLE to typed strings ("0 minutes"/"40 minutes", "0m59s"/"40m59s", "1 minute"/"41 minutes",
  "1m01s"/"41m01s", "1m30s"/"41m30s", "25 minutes"/"65 minutes").
  ops/mutate/plan.py: five mutants added, MIN_MUTATIONS 42 -> 47, the suite in TEST_FILES and SUITES:
  honest/back-roads-floor-strict (the reviewer's `score.value > RouteScore.honestFailureThreshold`),
  honest/back-roads-floor-nextdown (`score.value >= RouteScore.honestFailureThreshold.nextDown`),
  honest/minutes-drops-whole-check (the reviewer's), honest/minutes-zero-not-whole (`seconds > 0`),
  honest/minutes-singular-below-two (`whole <= 1`).
  RED, old tests (0137f926 tests, the five mutants uncommitted in plan.py only; `plan.py --only
  honest/back-roads-floor-,honest/minutes-`): all five "MISSED ... exit=0, no test objected"; "caught 0 of 5
  trapped 0 compile-only 0 MISSED 5 skipped 0".
  GREEN on d53818ef, same command: all five CAUGHT; "caught 5 of 5 trapped 0 compile-only 0 MISSED 0 skipped 0".
  By name (.build/t0230-names.py, the population's suites under each mutant): floor-strict and floor-nextdown ->
  "all back roads at lambda 8: nextDown(0.45) is dull, exactly 0.45 and nextUp(0.45) are offered"; the three
  minutes-* -> "ops/plan's refusal lines through ScenicPlanner.plan, whole, at budgets 0, 59, 60, 61, 90 and 1500 s".
  The 42 earlier mutants were not re-run (faster-verification rule); no Sources/ file changed this round, so no
  digest row moved.
  B3: origin/main 274cd174 merged (6665a6c4, clean; digests auto-merged, DRIVERS untouched here). On the merged
  head: plan population suites "Test run with 44 tests in 10 suites passed"; gates bare - check-safety-disclaimer
  exit 0; check-mutate-population "the floor of 168 holds"; check-mutate-only "NAME-PAIRS OK"; check-line-cap
  "682 Swift files tracked (Sources=327, Tests=245, apps/ios=110), none over 300 lines"; check-pins-yaml "PINS-YAML ok
  pins=51 fields=410"; check-exec-bits "P-OPS-01: 233 files, 23 required present, all modes correct"; queue-check
  "QUEUE OK (368 tasks)". wc -l PlanNothingPrettyBoundsTests.swift 77, ops/mutate/plan.py 331.
- 2026-10-16T16:02:32Z CORRECTION (agent/claude-opus-5): the rv1 FIX entry above names origin/main 274cd174 as merged; 6665a6c4's
  second parent is 55c4b140 (origin/main had moved, carrying T-0012/profilegate, before the merge ran), so the
  suites and gates quoted there ran on a head containing 55c4b140. `git merge-base --is-ancestor origin/main HEAD`
  exit 0 at origin/main 55c4b140 before the push.
