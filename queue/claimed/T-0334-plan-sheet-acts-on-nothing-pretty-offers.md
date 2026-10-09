---
id: T-0334
title: The plan sheet acts on a nothing_pretty answer's offers - "+40" re-plans at budget + 40 and "all back roads" plans the lambda-8 route with its real ETA - instead of only showing the honest-failure line
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-09T03:46:03Z
lease_expires_at: 2026-10-09T13:46:03Z
worktree: .worktrees/T-0334
branch: task/T-0334
exclusive: []
touches: [services/api/src/, services/api/test/, Sources/ScenicAPIClient/, Sources/ScenicKit/, Tests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/, ops/lib/check-safety-disclaimer-linked-digests.txt, pins/PINS.yaml]
pins_affected: [P-SAFE-04, P-COST-04]
reviewer: null
depends_on: [T-0332]
verify: [ops/test, ops/check-pins]
acceptance:
  - "A1 OFFER BODY, through handlePlan: the recorded westwood-malibu pair at +25 answers 422 whose WHOLE body equals {error: nothing_pretty, budget_minutes: 25, more_time_minutes: 65, back_roads_eta_s: 3578.87, back_roads_budget_minutes: 32}, both numbers recomputed in the test from the recorded bytes (ceil((lambda-4 time - fastest time) / 60), R3). A table through handlePlan over synthetic curves: an extra of exactly k minutes offers k (no ceil-up), a hair above offers k + 1, exactly 180 minutes offers 180, a hair above 180 offers null with back_roads_eta_s still shown, and every row whose back_roads_eta_s is null (dull, unscored, refused) offers null. Every T-0332 A3/A4/A5 row keeps its other fields."
  - "A2 WHITELIST (P-PRIV-05), through handlePlan: back_roads is accepted only as the literal true; false, 1, 'true', null, {} and [] each answer 400 with zero upstream calls and no reservation; back_roads beside reroute answers 400; parsePlanRequest's whole result is compared for absent (allBackRoads false) and true."
  - "A3 BACK-ROADS PLAN = ONE PLAN (P-SAFE-04, P-COST-04), through handlePlan: westwood-malibu with {budget_minutes: 32, back_roads: true} answers 200 with lambda 8, evaluations 1 and eta_s equal to the recorded lambda-8 answer's time (<= fastest + 32 * 60); the router receives exactly the fastest request and ONE car_scenic request whose custom_model equals buildCustomModel(8, null) (no lambda search), the quota is reserved exactly once and sent <= PLAN_UPSTREAM_COST. The same request at budget_minutes 31 answers 500 ceiling_breached, never a 200: the ceiling is checked against the requested budget like every plan."
  - "A4 CLIENT READER: NothingPrettyOffer reads back_roads_budget_minutes fail-closed over a table through PlanResponseReader: null, 0, 32 and 180 accepted (compared whole); the key missing, -1, the next double below 0, the next double above 180, 181, 32.5, a string and a bool each -> unexpectedResponse(status: 422); a non-null budget beside a null back_roads_eta_s -> unexpectedResponse."
  - "A5 SHEET (P-SAFE-03 gate kept): ClientPlanner maps a 422 nothing_pretty whose budget echoes the ticket's to PlanOutcome.offered(PlanOffer) compared whole, and one whose budget does not echo it (or is not a whole minute) to failure(.unexpectedResponse); PlanSheet.finish puts .offered(ticket, offer) in state; takeMoreTime() returns the gate's ticket with budgetMinutes = budget + 40 and allBackRoads false, takeBackRoads() one with budgetMinutes = back_roads_budget_minutes and allBackRoads true (each compared whole); each returns nil and leaves the state unchanged with the disclaimer not accepted, with its offer field nil, and from every state that is not .offered."
  - "A6 REQUEST BYTES (full equality): a back-roads ticket through ClientPlanner over a recording transport sends ONE request whose body bytes EQUAL the sorted-keys JSON {back_roads: true, budget_minutes: 32, destination: {place}, origin: {lat, lon}, vehicle} recomputed in the test; a plain ticket's body carries no back_roads key (the existing PlanClient body tests unchanged)."
  - "A7 COPY: PlanOfferCopy.of(offer) equals its whole value over the cross product budget {0, 25} x more {nil, 65} x back-roads {nil, (eta 3578.87 s, 32 min)}: the line names the budget minutes, the +40 button names budget + 40 minutes, the back-roads button names its ETA minutes and the extra minutes it asks for; a nil offer has no button; the fallback action is chooseAnotherPlace."
  - "A8 APP + GATES: PlanSheetScreen renders .offered as PlanOfferCard whose buttons call takeMoreTime / takeBackRoads and run the ticket through the same planner path; ios-compile success and ios-screenshot success on the branch with the shots looked at (R8); P-SAFE-04 named-tests gain A3's two rows; digests re-approved; check-mutate-population, check-line-cap, check-pins-yaml and queue-check green on the merged head."
---
## Brief

T-0332 R7 (owner ruling): the Worker answers 422 `nothing_pretty` with `budget_minutes`, `more_time_minutes`
(budget + 40, or null past 180) and `back_roads_eta_s` (the MAX_LAMBDA route's real ETA when it scores >= 0.45, else
null), and the client reads them into `PlanError.nothingPretty(NothingPrettyOffer)`. The sheet shows only the
payload-free line ("Not much pretty within reach of this drive. More time might find some.") with
`.chooseAnotherPlace`: neither offer is actionable yet.

MEASURE FIRST, then write the acceptance: how PlanSheetState / PlanOutcome carry a failure today (payload-free
PlanSheetFailure), where the sheet's budget control lives, and what a back-roads plan must send - a request field the
Worker whitelists (planRequest.ts BODY_KEYS, P-PRIV-05) that plans at lambda 8 and answers that route with its real
ETA. Rule against P-SAFE-04 before code: the back-roads ETA may exceed fastest + budget, so either the request names
a budget that covers it (the driver chose more time) or the invariant's wording is ruled with the owner - never a
silent over-ceiling 200. Each offer is one more plan (P-COST-04, quota). Copy names the minutes ("within 25 minutes")
once the failure carries them to the sheet. Apple files change: ios-compile and ios-screenshot green, shots looked at.

## Log
- 2026-10-08T21:58:00Z filed by agent/claude-opus-5 (T-0332 owner) from T-0332 R7.
- 2026-10-09T03:46:03Z claimed by agent/claude-opus-5; lease until 2026-10-09T13:46:03Z
- 2026-10-09T03:51:37Z MEASURED (agent/claude-opus-5, owner, on 537167bd):
  - failure carriage: PlanOutcome = preview | failure(PlanSheetFailure); PlanSheetFailure is a payload-free String
    CaseIterable enum; PlanSheetState.failed(PlanTicket, PlanSheetFailure). ClientPlanner maps every PlanError through
    `error.failure`, so NothingPrettyOffer is dropped at ClientPlanner.swift:22. PlanSheetState is switched only in
    apps/ios PlanSheetScreen.planContent (:113) and Tests/ScenicKitTests/PlanSheet/PlanSheetTests; PlanOutcome is
    produced by ClientPlanner, apps/ios UnreachablePlanner and OnboardingPlanGateTests' fake.
  - budget control: PlanSheet.budgetMinutes (Int, clamped 0...180 by setBudget, ignored while planning) is the Stepper
    in PlanSheetScreen.form ("Extra time", step 15); the ticket carries it (PlanTicket.budgetMinutes).
  - the wire: planRequest.ts BODY_KEYS = origin, destination, budget_minutes, departs_at, vehicle, reroute. No key asks
    for a lambda. The 422 body carries no fastest ETA, so the client cannot compute a budget that covers
    back_roads_eta_s on its own.
  - population: westwood-malibu fastest 1667.261 s, lambda 3.25 (chosen at +25) 1904.238 s, lambda-4 (answered for
    lambda 8, T-0332 R5) 3578.87 s: back-roads extra 1911.609 s = 31.86 min -> 32 whole minutes; at budget 31 the
    route is over the ceiling (1667.261 + 1860 = 3527.261 < 3578.87), at 32 under it (3587.261). The only lambda-8
    recording is Tests/Fixtures/custom-model/lambda-8.json (a model, not a route).
  - screenshots: ios-screenshot.yml's SHOTS are collapsed medium fastest settings paywall surprise drive - none is the
    plan sheet, and .github/ is outside this task's touches.
- 2026-10-09T03:51:37Z RULED (agent/claude-opus-5, owner):
  - R1 ORCHESTRATOR RULING on P-SAFE-04, recorded: the ceiling is never relaxed. '+40' is a fresh plan at
    budget_minutes + 40. 'All back roads' is a fresh plan whose request names a budget that covers the shown
    back-roads ETA (the driver chose that much more time, shown before they tap), so the returned ETA is still
    <= fastest + the requested budget; the new body key asking for lambda 8 is whitelisted (P-PRIV-05, no coordinate)
    and its answer is checked against the ceiling like every plan - never a silent over-ceiling 200. Each offer is
    one plan (quota, P-COST-04). Copy names the minutes.
  - R2 the request key is `back_roads`, literal `true` only (anything else 400), refused beside `reroute` (a reroute
    keeps the lambda it remembered). planScenic with it skips searchLambda: ONE car_scenic request at MAX_LAMBDA with
    the same closures model, then every guard a searched plan passes - the ceiling (ceiling_breached 500), Jaccard
    overlap, the closure re-request, the honest failure. Worst case 1 + 1 + 1 + 1 = 4 <= PLAN_UPSTREAM_COST.
  - R3 the 422 body gains `back_roads_budget_minutes` = ceil((back_roads_eta_s - fastest) / 60), floored at 0; null
    when back_roads_eta_s is null or the minutes exceed MAX_BUDGET_MINUTES 180. back_roads_eta_s keeps T-0332's
    meaning (shown even when no budget can be asked); the app offers the button only with a budget. The Worker
    computes it because only the Worker knows the fastest ETA; whole minutes because PlanClient's budget is Int.
  - R4 the app: ScenicKit gains PlanOffer (Int budget / more / back-roads budget, Double back-roads ETA),
    PlanOutcome.offered and PlanSheetState.offered; PlanSheetFailure stays payload-free and its .nothingPretty row stays
    the fallback copy. ClientPlanner refuses an offer whose budget does not echo the ticket's (it is not this plan's
    answer). takeMoreTime / takeBackRoads go through the same gate as startPlanning (disclaimer, start, destination),
    and the sheet's budget becomes the minutes the driver tapped, so the Stepper shows what was asked.
  - R5 copy (calm, owner-route-intent): line 'Not much pretty within N extra minutes of this drive.' ('... without extra
    time.' at 0); '+40' button 'Try M extra minutes'; back-roads button 'All back roads: about E min, B extra minutes'.
  - R6 no ops/mutate population: the new Sources/ code is range checks and a whole-minute conversion held by A4/A5
    tables (T-0332 R9 precedent); the ceil is in services/api, held by A1's exact / hair-above rows.
  - R7 PlanTicket gains `allBackRoads` (internal init unchanged in spirit: only the sheet issues tickets).
  - R8 no screenshot shows the plan sheet (MEASURED); ios-screenshot is still dispatched and its shots looked at for
    regressions, and a plan-sheet shot (a -screen launch value plus a SHOTS entry in .github/) is a follow-up.
