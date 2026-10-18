---
id: T-0403
title: A live /plan takes 12.1 s (6 router evaluations across the tunnel) against the plan's p95 1.5 s - measure where the time goes and cut it
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-18T01:56:19Z
lease_expires_at: 2026-10-19T01:56:19Z
worktree: .worktrees/T-0403
branch: task/T-0403
exclusive: []
touches: [services/api/src/, services/api/test/, ops/lib/, queue/]
pins_affected: [P-COST-04, P-SAFE-04]
reviewer: null
depends_on: []
verify: [ops/test]
acceptance: []
---
## Brief

Measured 2026-10-17 (T-0395), one live request through the deployed Worker (c6f2da75) to the pilot router (the
owner's Windows box, WSL docker, Cloudflare Tunnel scenic-router.phineasfritsch.com): origin 34.07,-118.44 ->
Topanga place, budget 25 -> HTTP 200 in 12.1 s total; evaluations 6, lambda 7.75. The plan's target is p95 < 1.5 s
against the CI router. The phone pilot will feel 12 s as broken.

This is a MEASUREMENT task first: time each upstream call (Worker -> tunnel -> Caddy -> GraphHopper) and the
Worker's own work, for at least 5 live plans to different seeded places (privacy rule: one 2-dp origin per request).
Quote the per-call times. Then rule which lever pays: parallel bracketing evaluations within the <= 2 in-flight cap
(P-COST-04), a smaller lambda search when the first bracket already fits, router-side JVM warmup / ch.disable cost,
or tunnel RTT. File the fix as its own acceptance once the population is measured. The ceiling (ETA <= fastest +
budget) must hold through any change.

## Log
- 2026-10-17 filed by agent/claude-opus-5 from T-0395's live /plan probe.
- 2026-10-17T17:52:30Z agent/claude-opus-5: first measurement, POST /route Westwood -> Topanga place, secret header, from WSL: car_fast localhost 5.56 s (COLD - first call after idle; GraphHopper MMAP pages in) then 0.43 s; car_fast via tunnel 0.73 s / 0.91 s; car_scenic ch.disable + custom model localhost 0.99 s / 0.23 s, via tunnel 0.40 s / 0.25 s. GraphHopper took 50 ms of it. So the 12.1 s live plan is ~one cold start (~5 s) + 6 sequential evaluations at ~0.3-0.9 s each through the tunnel. Levers to measure next: a keep-warm request (the Worker cron already runs every 15 min), evaluations in parallel within the 2-in-flight cap, fewer bisection steps.
- 2026-10-18T01:56:19Z claimed by agent/claude-opus-5; lease until 2026-10-19T01:56:19Z
- 2026-10-18T02:18:42Z agent/claude-opus-5 (author rule - rulings before code):
  - R1 Brief vs this worktree: the Brief asks for >= 5 live plans timed per call. The task text forbids this session from touching the pilot router, the tunnel or production; live timing is the orchestrator's job after merge. Ruled: this PR ships the one lever that pays on every warm plan WITHOUT changing any answer, proven on a timed fake router; the live 5-plan population is quoted by the orchestrator after deploy (the cold start is a separate lever, below).
  - R2 Where the time goes (read from src, not guessed): planScenic makes 1 car_fast request, then searchLambda's 6 sequential evaluations (lambda 0, then 5 midpoints 4, 6|2, ... - the cap binds, never the tolerance: 8/2^5 = 0.25 > LAMBDA_TOLERANCE 0.05). 7 router round trips, strictly one after the other; at the Log's 0.25-0.9 s per warm call through the tunnel that is 1.8-6.3 s, plus a ~5 s cold start on the first call after idle = the 12.1 s.
  - R3 The lever pulled - a schedule, not a search change. Two facts of the current search: (a) the first midpoint is always MAX_LAMBDA/2 = 4 (cap >= 2 and width 8 > tolerance), and MEASURING it needs nothing - only its feasible/infeasible decision needs the ceiling, i.e. the fastest; (b) lambda 0 never moves the bracket (lo starts at 0 whatever it answers) - it is only a candidate. So: round 1 = car_fast || lambda 4; round 2 = lambda 0 || midpoint 2; rounds 3-5 = midpoints 3-5. 7 requests in 5 rounds instead of 7, never more than 2 in flight (P-COST-04). The SAMPLE SET is identical (same lambdas, same requests, same count), and every output of the search is a function of the set, not its order: best = longest feasible, tie -> larger lambda (lambdas are distinct); violatesMonotonicity is over all pairs; evaluations = |set|; the no_feasible message uses min and count. So lambda, eta_s, evaluations, used_budget and the route are byte-equal by construction, and acceptance 1 proves it on the recorded fixtures. All back roads (T-0334): car_fast || lambda 8, 1 round instead of 2.
  - R4 Errors keep today's precedence: results are RECORDED in today's order (fastest, lambda 0, then midpoints in bisection order) after both requests of a round settle, so the error searchLambda would throw is the error thrown. Only an error path can now cost one request today's code did not make (lambda 4 already in flight when car_fast fails; midpoint 2 when lambda 0 fails) - at most 9 requests, inside PLAN_UPSTREAM_COST 12; a midpoint whose answer is unusable launches no successor.
  - R5 Levers ruled out: two bracketing lambdas per round (quartile search) and early stop at tolerance both change the sample set, hence lambda/eta on some curves - not byte-equal; reusing a lambda-8 answer - /plan's search never measures lambda 8 (only back roads and the honest-failure ETA do), so speculating it adds a request to every plan; speculating both children of a midpoint needs 3 in flight (P-COST-04 forbids) or wasted calls on the owner's box; a keep-warm request for the cold start lives in the router/cron, outside this worktree's touches and forbidden to this session - left to the orchestrator (follow-up id from T-0422..T-0424 if it files one).
  - R6 Scope: /trip keeps the sequential searchLambda unchanged (its budget is a function of the fastest, its tests pin request order, it is not in this Brief). The new schedule is searchLambdaAlongside in src/lambdaSearch.ts, sharing searchLambda's validation and candidate rules; only planScenic calls it.
  - R7 P-COST-04 binds the test `one plan makes 7 upstream requests - at most 12 - one in flight at a time`, which asserts maxInFlight 1 - that is exactly the property this task changes. Ruled: rename it to `... at most 12 - at most 2 in flight`, assert 2, update ops/lib/named-tests.json and append a T-0403 sentence to the pin's prose (which says '<=2 in flight' was proven only as one in flight).

## Acceptance
1. `cd services/api && npx vitest run test/planSchedule.test.ts` - the byte-equal table: for every row the WHOLE answer (`status` + sha256 and length of the exact response text) equals the value captured from main 0399dcea's code before any src change (capture quoted in the Log). Rows: santa-monica-topanga +25, westwood-woodland-hills +25, westwood-malibu +25 (422 nothing_pretty, with its lambda-8 back-roads ETA), westwood-malibu back roads 32 (200) and 31 (500 ceiling_breached), the step-at-lambda-4 curve (infeasible branch), the all-overshoot curve (502 no_route), the exactly-at-ceiling curve, a router refusing car_fast, a router refusing every scenic model, and 40 seeded random curves incl. non-monotone ones.
2. Same file, the timed fake router (a virtual clock: every router request takes T = 100 ms and records start/end; the answer's wall time is the clock when it resolves): santa-monica-topanga +25, westwood-woodland-hills +25 and the step curve answer at wall <= 5T = 500 ms (main: 7T = 700 ms); westwood-malibu +25 at <= 6T (main 8T); back roads 32 at <= 1T (main 2T); peak requests in flight <= 2 on every row and == 2 on the full plans. Seen RED on main's src first.
3. `npx vitest run test/lambdaSearch.test.ts` - searchLambdaAlongside against searchLambda over generated curves (seeded; monotone, non-monotone, all-infeasible, NaN/negative answers, rejected requests, caps 0..10, invalid fastest/budget): the WHOLE outcome toEqual (or the same BudgetError reason AND message, or the same rejection), the same SET of measured lambdas, evaluations <= the cap; and planCost's `... at most 12 - at most 2 in flight`: 7 requests, <= 12, peak in flight 2.
4. Ceiling: planCeiling.test.ts (120 random curves, never over fastest + budget) and planBackRoads' 31-minute `ceiling_breached` stay green; row `back roads 31` of acceptance 1 is 500 `{"error":"ceiling_breached"}` byte-equal.
5. `npx vitest run` (whole Worker suite) green; bare gates: check-safety-disclaimer, check-mutate-population.py, check-mutate-only.py, check-pins-yaml.py, check-exec-bits, queue-check, and `ops/lib/run-named-tests.py P-COST-04` green.
