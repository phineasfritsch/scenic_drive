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
  - "A6 RECORD: T-0182's R4 corrected in a dated Log line here with a pointer line on T-0182's Log (R6); ops/mutate/plan.py MIN_MUTATIONS 31 -> 39 with the eight new mutants caught by name (--only run quoted); swift test count line for the touched suites; check-safety-disclaimer, check-mutate-population.py, check-mutate-only.py, check-line-cap, check-pins-yaml.py, check-exec-bits, queue-check bare"
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
