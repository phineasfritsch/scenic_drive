---
id: T-0411
title: Live /plan still takes 1.8-7 s after T-0403 (failure paths 4-7 s) against the plan's p95 1.5 s - measure the remaining time per stage and cut it
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-18T17:23:19Z
lease_expires_at: 2026-10-19T17:23:19Z
worktree: .worktrees/T-0411
branch: task/T-0411
exclusive: []
touches: [services/api/src/, services/api/test/, services/api/test/mutate/, ops/lib/, queue/]
pins_affected: [P-COST-04, P-SAFE-04]
reviewer: null
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
