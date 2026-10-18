---
id: T-0411
title: Live /plan still takes 1.8-7 s after T-0403 (failure paths 4-7 s) against the plan's p95 1.5 s - measure the remaining time per stage and cut it
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-18T17:23:19Z
lease_expires_at: 2026-10-19T17:23:19Z
worktree: .worktrees/T-0411
branch: task/T-0411
exclusive: []
touches: [services/api/src/, services/api/test/, services/api/test/mutate/, ops/lib/, queue/]
pins_affected: [P-COST-04, P-SAFE-04]
reviewer: agent/rv1-t-0411
depends_on: [T-0409]
verify: [ops/test]
acceptance: []
---
## Brief

T-0409 deployed T-0403's 5-round schedule (live 839220da) and timed 5 places from Westwood (34.07,-118.44, +25):
- 200 answers: 1.8-4.3 s (Topanga dropped from 4.17 s to 2.41 s).
- Honest-failure 422 answers (no_scenic_alternative, nothing_pretty): still 4-7 s.

The quoted lines are in T-0409's Log. Each warm router call through the tunnel takes 0.25-0.9 s, and GraphHopper's
own work is about 50 ms of that.

This is a MEASUREMENT task first. Use a timed fake router plus Worker-side timing over the recorded fixtures to
attribute the remaining time:
- the rounds on the failure paths (the nothing_pretty offer computes lambda-4 and lambda-8 extras)
- the re-request that confirms the chosen route
- KV and D1 reads
- the plan cache

Rule which lever pays without changing any answer, and keep the ETA ceiling and the <= 2 in-flight cap. Candidate
levers:
- compute the failure-path extras concurrently within the cap
- cache the fastest route per (H3-8 origin, H3-8 destination, hour bucket)
- skip the confirming re-request when the bracket already holds the chosen route

Answer equality must stay byte-exact on the recorded fixtures (T-0403's oracle).

## Log
- 2026-10-18 filed by agent/claude-opus-5 from T-0409's live timings.
- 2026-10-18T17:23:19Z claimed by agent/claude-opus-5; lease until 2026-10-19T17:23:19Z
- 2026-10-18T17:40Z agent/claude-opus-5: RULINGS before any src change (Brief vs code vs reality).
  R1 "the nothing_pretty offer computes lambda-4 and lambda-8 extras" - code: scenicPlanner.planScenic sends ONE extra after the search, the back-roads offer at MAX_LAMBDA=8 (honestFailure.backRoadsEta); lambda 4 is the search's first midpoint, not an extra. Ruled: the failure-path extra is the lambda-8 offer only.
  R2 "the re-request that confirms the chosen route" - code has no confirming re-request. The only post-search request besides the offer is the closure re-request (closuresNearest `returned`, T-0286 C4), sent only when the chosen route crosses a stored closure the request did not send. Over every recorded fixture (FRESH_EMPTY closures) it is 0 requests, so the "skip the confirming re-request" lever buys nothing; ruled out.
  R3 "the plan cache" - there is no plan cache on /plan (plan_token in PLANS is a reroute memory written after the answer). The fastest-route cache lever: car_fast already rides alongside lambda 4 in round 1, so caching it removes no round by itself, adds one serial KV read and a stale-graph risk to every answer. Ruled out here; filed as follow-up T-0433 only if a later measurement shows round 1 alone.
  R4 KV and D1: the handler awaits 5 Worker-side reads in series before the first router request (measured below: d1-place, kv-closures, identify, quota-read, quota-reserve; plus one PLANS put after a 200 in production). These are Worker-local (tens of ms each per Cloudflare's published latencies, not measured live: this task may not touch the tunnel or prod) against 0.25-0.9 s per router round (T-0409 Log). Ruled: router rounds dominate; KV/D1 are not this task's lever.
  R5 the "timed fake router" is T-0403's test/timedRouter.ts (virtual clock, every request T ms). The Brief's "Worker-side timing" is measured as the count of serial awaits (no real clock in the harness).
  R6 byte-exactness: GOLDEN for the new table is captured from this branch's src (main 311aefaf) BEFORE any src change, and planSchedule.test.ts's 50-row GOLDEN (T-0403, from 0399dcea) must stay green unchanged.
- 2026-10-18T17:40Z agent/claude-opus-5: BEFORE measurement (new test/planStages.test.ts "prints the attribution table", src = main 311aefaf, T = 1 round; rN = the round a request started in):
    santa-monica-topanga +25 (200): rounds=5 requests=7 peak=2 serial-reads=5   r1:fast r1:search@4 r2:search@0 r2:search@6 r3:search@7 r4:search@7.5 r5:search@7.75
    westwood-woodland-hills +25 (200): rounds=5 requests=7 peak=2 serial-reads=5   (same schedule)
    westwood-malibu +25 (422 nothing_pretty): rounds=6 requests=8 peak=2   r1:fast r1:search@4 r2:search@0 r2:search@2 r3:search@3 r4:search@3.5 r5:search@3.25 r6:offer@8
    every scenic route on the fastest's ways (422 no_scenic_alternative): rounds=5 requests=7 peak=2   (search 4,0,6,7,7.5,7.75)
    every scenic route overshoots (502): rounds=5 requests=7   r1:fast r1:search@4 r2:search@0 r2:search@2 r3:search@1 r4:search@0.5 r5:search@0.25
    dull at every lambda (422 nothing_pretty, no offer): rounds=6 requests=8   ... r5:search@7.75 r6:offer@8
    westwood-malibu back roads 32 (200): rounds=1 requests=2   r1:fast r1:search@8
    dull back roads 40 (422 nothing_pretty): rounds=2 requests=3   r1:fast r1:search@8 r2:search@8 (the offer re-sends the identical lambda-8 request)
  Attribution: rounds 3-5 of every full plan carry ONE request (a free slot under the cap of 2), the nothing_pretty offer is a whole extra round 6, and an all-back-roads honest failure re-sends the request it already holds. At 0.25-0.9 s/round that is 1.25-4.5 s for a 200 and 1.5-5.4 s for nothing_pretty, matching T-0409's live 1.8-4.3 s / 4-7 s.
- 2026-10-18T17:40Z agent/claude-opus-5: LEVERS chosen (each keeps every answer byte-exact - same recorded samples, same routes):
  L1 speculative midpoint: while midpoint m is in flight and a slot is free, send m's upper child (the midpoint the search needs next if m fits the ceiling - every live T-0409 plan landed at lambda 7.75, i.e. every midpoint fit). Never recorded unless the search reaches it; at most MAX_SPECULATIVE = 2 per plan, so a plan sends at most 1 fast + 1 floor + 5 midpoints + 2 spec + 1 offer + 1 closure retry = 11 <= PLAN_UPSTREAM_COST 12, and the closure re-request's `used + 1 <= 12` gate is never closed by it.
  L2 the offer in the free slot: when the in-flight midpoint is the search's last, the lambda-8 offer request is sent alongside it; used only on the honest-failure path (else one unused request per scenic plan - the router-load cost of this lever, ruled acceptable: 8 vs 7 requests, the 12-call reservation is unchanged).
  L3 an all-back-roads honest failure reuses the lambda-8 route it already measured (identical request body) instead of re-sending it.
## Acceptance
1. `cd services/api && npx vitest run test/planStages.test.ts` - every row's whole answer (status, length, sha256) equals GOLDEN captured before the change; rounds exactly: 200s 5->4, no_scenic_alternative 5->4, nothing_pretty 6->4, overshoots 5, back roads 1, dull back roads 2->1; peak <= 2; requests <= 12.
2. `cd services/api && npx vitest run test/planSchedule.test.ts test/lambdaSearch.test.ts` - T-0403's 50-row GOLDEN unchanged and green; the 400-row searchLambda oracle green with the new schedule.
3. `node services/api/test/mutate/planMutants.mjs` - every mutant CAUGHT, floor raised for the new schedule entries.
4. `cd services/api && npx vitest run` and `npx tsc --noEmit` - green.
5. `bash ops/check-pins --source-only` - P-COST-04 and P-SAFE-04 hold.
6. `bash ops/queue-check` - QUEUE OK.
- 2026-10-18T17:45Z agent/claude-opus-5: RED (src unchanged, ROUNDS set to the targets above): `npx vitest run test/planStages.test.ts` -> "Tests  6 failed | 4 passed (10)"; the 6 failing rows are the rounds targets (topanga, woodland-hills, malibu nothing_pretty, no_scenic_alternative, dull at every lambda, dull back roads); overshoots (5) and back roads 32 (1) already hold.
- 2026-10-18T18:40Z agent/claude-opus-5: L2 RULED OUT after building it. Sending the offer beside the last midpoint made both nothing_pretty rows take 4 rounds with byte-equal answers. But the offer then goes out on EVERY scenic plan: 8 requests instead of 7 on every 200. That broke 42 request-count assertions in 5 files (closuresCrossing 34 rows, BASE "/plan" 6 -> 7 car_scenic; planCeiling 2; planCost 2; planRecorded 1; productionDeps 3). Trading one router request per plan for one round on honest failures is a cost call for the owner, so it is filed as T-0433 and not made here. The shipped levers are L1 and L3.
- 2026-10-18T18:40Z agent/claude-opus-5: AFTER (test/planStages.test.ts "prints the attribution table", the same rows):
    santa-monica-topanga +25 (200): rounds=4 requests=7 peak=2   r1:fast r1:search@4 r2:search@0 r2:search@6 r3:search@7 r3:search@7.5 r4:search@7.75
    westwood-woodland-hills +25 (200): rounds=4 requests=7 peak=2   (same schedule)
    westwood-malibu +25 (422 nothing_pretty): rounds=5 requests=8 peak=2   r1:fast r1:search@4 r2:search@0 r2:search@2 r3:search@3 r3:search@3.5 r4:search@3.25 r5:offer@8
    every scenic route on the fastest's ways (422 no_scenic_alternative): rounds=4 requests=7 peak=2
    every scenic route overshoots (502): rounds=5 requests=9 peak=2   r1:fast r1:search@4 r2:search@0 r2:search@2 r3:spec@3 r3:search@1 r4:spec@1.5 r4:search@0.5 r5:search@0.25 (both guesses wrong: 2 extra requests, no extra round)
    dull at every lambda (422 nothing_pretty, no offer): rounds=5 requests=8 peak=2
    westwood-malibu back roads 32 (200): rounds=1 requests=2
    dull back roads 40 (422 nothing_pretty): rounds=1 requests=2   (L3: the lambda-8 route is reused, not re-sent)
  Every sha256 and length equals the BEFORE GOLDEN. At 0.25-0.9 s per round, a 200 drops from 1.25-4.5 s to 1.0-3.6 s of router time, and nothing_pretty from 1.5-5.4 s to 1.25-4.5 s. That still misses the plan's p95 1.5 s. The rest is per-round tunnel latency (0.25-0.9 s against ~50 ms of GraphHopper work), which no Worker-side lever removes. Live re-timing belongs to the separate prod-exclusive deploy task.
- 2026-10-18T18:40Z agent/claude-opus-5: GREEN: `npx vitest run test/planStages.test.ts test/planSchedule.test.ts test/lambdaSearch.test.ts` -> "Tests  87 passed (87)". Changed tests, and why: planSchedule's timed rows now expect 4/4/5/4 rounds (topanga, woodland-hills, malibu, step at 4); its first-rounds test now expects starts [0,0,T,T,2T,2T,3T]; its 50-row byte GOLDEN is untouched and green. lambdaSearch's 400-row oracle keeps whole-result equality and peak <= 2; its exact visited-set model (T-0403's extras) is replaced by: every lambda searchLambda needed is sent, every lambda sent is a bisection node the cap admits, at most 4 beyond, at most cap + 2 in total. New exact tests: at most 2 guesses (cap 10, all overshoot -> beyond [1.5, 0.75]); a slow wrong guess has settled before the search returns; a failing fastest launches only [4]; a bad budget launches nothing.
- 2026-10-18T18:40Z agent/claude-opus-5: MUTANTS (services/api/test/mutate/planMutants.mjs; 7 stale T-0403 alongside entries replaced by 11 scheduler entries + planner-back-roads-resent; planStages and planSchedule added to TESTS). First full run: "RESULT caught=77 missed=3 trap=0 of 80". The misses, seen red: alongside-launch-after-fastest-fails was unreachable (a failing fastest throws before any fill), so the guard is deleted and the entry dropped. alongside-bad-budget-launches is re-anchored on fill's budget guard and pinned by the new bad-budget test. route-empty-differs predates this task: since T-0332 the empty-ways row is 422 either way, so planCeiling now asserts the whole body {error: no_scenic_alternative}. Re-run on the closed and touched ids: "RESULT caught=5 missed=0 trap=0 of 5". Floor: MIN_MUTATIONS = 79, the real population; --prove-floor refuses 78 and passes "real population: quiet".
- 2026-10-18T18:40Z agent/claude-opus-5: follow-up filed: T-0433 (owner decision on L2). T-0434/T-0435 not used.
- 2026-10-18T19:45Z agent/claude-opus-5: PRE-REVIEW MUTANT SURVIVOR M3 closed by class (fable pass at a4cad397: M1 and M2 CAUGHT, M3 SURVIVED). M3 dropped the dedupe key on the speculative guess (`guess !== null && !runs.has(guess) && guesses` -> `guess !== null && guesses`); the full vitest stayed green because every suite lands every request after the same delay, so the fastest always lands before a guess and the bisection never stands still while a guess is re-proposed. Class ruled: "a lambda is sent twice when requests land in an order the suites never produce". Closed over landing ORDER, not this one witness: new test/lambdaSearchLanding.test.ts runs 200 generated rows x 5 landing orders (together, fastest-first, fastest-late 12 hops, fastest-last 40 hops, jitter = per-seed fastest delay and per-(seed, lambda) measure delay), each row asserting no lambda sent twice, the whole result equal to searchLambda, peak <= 2; a meta-assertion requires > 300 row-runs where a request went out after lambda 0 while the fastest was still outstanding (the state M3 needs). Plus the exact witness: a fastest that lands after 12 hops sends exactly [4, 0, 6, 7, 7.5, 7.75] with [false, false, false, true, true, true] for fastest-landed. src unchanged.
  Mutants for the class (every `runs.has` key in fill): alongside-guess-resent (M3) and alongside-pending-resent added to test/mutate/planMutants.mjs; lambdaSearchLanding.test.ts added to TESTS; MIN_MUTATIONS 79 -> 81. A third, alongside-floor-resent (`else if (!runs.has(0))` -> always), was built and DROPPED: it livelocks - lambda 0 relaunches in microtasks on every landing, so a timer-held fastest never lands and the vitest run hung 15 min with no timeout to report it (killed; src restored with git checkout). It is not a survivor - it cannot finish - but the driver has no per-run timeout to score it, so it is not in the population.
  RED: `node services/api/test/mutate/planMutants.mjs --only=alongside-guess-resent --without=test/lambdaSearchLanding.test.ts` -> "MISSED alongside-guess-resent / RESULT caught=0 missed=1 trap=0 of 1 without test/lambdaSearchLanding.test.ts". M3 applied by hand, `npx vitest run test/lambdaSearchLanding.test.ts` -> "Tests  2 failed (2)", `- "twice": [], + "twice": [` and `expected [ [ 4, false ], [ +0, false ], ...(5) ] to deeply equal [ [ 4, false ], [ +0, false ], ...(4) ]`.
  GREEN: `npx vitest run test/lambdaSearchLanding.test.ts` -> "Tests  2 passed (2)"; `node services/api/test/mutate/planMutants.mjs --only=alongside-guess-resent,alongside-pending-resent` -> "CAUGHT alongside-guess-resent by \"200 generated rows x 5 landing orders: ...\" / CAUGHT alongside-pending-resent by \"/plan, empty, clear path, router honours: ...\" / RESULT caught=2 missed=0 trap=0 of 2"; `--prove-floor` -> one short REFUSED (population 80 is below the floor 81), "real population: quiet".
- 2026-10-18T20:50Z agent/claude-opus-5: ACCEPTANCE re-quoted on 1f7b591e (git fetch origin + merge origin/main: "Already up to date", main 279152bb):
  1. `npx vitest run test/planStages.test.ts` -> "Test Files  1 passed (1) / Tests  10 passed (10)".
  2. `npx vitest run test/planSchedule.test.ts test/lambdaSearch.test.ts test/lambdaSearchLanding.test.ts` -> "Test Files  3 passed (3) / Tests  79 passed (79)".
  3. Touched ids only (owner-approved faster rounds): "RESULT caught=2 missed=0 trap=0 of 2" (alongside-guess-resent, alongside-pending-resent); `--prove-floor` "real population: quiet" at floor 81. The full 81-mutant run was not re-run this round.
  4. `npx vitest run` -> "Test Files  104 passed (104) / Tests  2774 passed (2774)". `npx tsc --noEmit` -> exit 1, "error TS2688: Cannot find type definition file for '@cloudflare/workers-types/2023-07-01'". Ruled pre-existing and not this PR: tsconfig.json and package.json are unchanged against origin/main (`git diff origin/main --stat` empty); the locked 5.20260907.1 package ships no 2023-07-01 entry, and that pin dates from T-0005. Overriding --types gives 202 errors, none in lambdaSearch.ts or planMutants.mjs. Not green; not caused here; not fixed here.
  5. `bash ops/check-pins --source-only` - started on 1f7b591e and still running after 35 min (it was in check-line-cap / check-safety-disclaimer); NOT quoted, still owed.
  6. `bash ops/queue-check` -> "QUEUE OK (405 tasks)".
- 2026-10-18T22:10Z agent/rv1-t-0411: REVIEW PASS (PR #304 at 8b1becaf; reviewer is not the owner). Detached worktree at origin/task/T-0411 after `git fetch origin` in the main checkout.
  1. `npx vitest run` (services/api) -> "Test Files  104 passed (104) / Tests  2774 passed (2774)".
  2. Measurement reproduced: src/lambdaSearch.ts + src/scenicPlanner.ts checked out from origin/main, `npx vitest run test/planStages.test.ts` -> "Tests  6 failed | 4 passed (10)"; every failure differs ONLY in rounds (4 vs 5, 4 vs 5, 5 vs 6, 4 vs 5, 5 vs 6, 1 vs 2) with sha256/length equal to GOLDEN, so GOLDEN is main's bytes and the BEFORE/AFTER rounds in this Log hold. Restored, 10/10 green.
  3. Reviewer mutant A (bisection tie: `if (a.value <= ceiling) lo = pending` -> `<`), full vitest: CAUGHT, 3 failed (lambdaSearch "a midpoint exactly at the ceiling moves the bracket up", planCeiling "exactly at the ceiling is returned", planSchedule "exactly at the ceiling ... sha256").
  4. Reviewer mutant B (guess past the cap: `nextMidpoint(pending, hi, steps + 1, cap)` -> `steps`), full vitest: CAUGHT, lambdaSearch 400-row oracle and the exact 4,6,0,7,7.5,7.75 schedule failed (routes.test.ts /__ro also failed under load; re-run alone on the clean head: 8 passed - a load flake, not this PR).
  5. Cost/ceiling read: worst case 1 fastest + 6 search + 2 guesses + 1 closure re-request + 1 offer = 11 <= PLAN_UPSTREAM_COST 12, and both later requests stay gated on `used + 1 <= PLAN_UPSTREAM_COST`; guesses are never recorded, so the chosen lambda and P-SAFE-04 ceiling check are unchanged; `finally` awaits every run.
  6. `gh pr checks 304` at 8b1becaf: core pass, pins-source-only pass. Local `ops/check-pins` (full and --source-only) hung with no output in `ops/lib/pins.py Q` on this loaded box (killed after 40 min / timed out at 580 s) - environment, not quoted as green; CI pins-source-only at the same head is the gate.
  7. `bash ops/queue-check` -> "QUEUE OK (405 tasks)". Ancestry: origin/main 279152bb is an ancestor of 8b1becaf.
