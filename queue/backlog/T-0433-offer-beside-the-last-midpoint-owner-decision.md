---
id: T-0433
title: Owner decision - send the nothing_pretty back-roads offer beside the search's last midpoint (+1 router request per scenic plan for -1 round on the honest-failure path)
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/api/src/, services/api/test/, services/api/test/mutate/, queue/]
pins_affected: [P-COST-04, P-SAFE-04]
reviewer: null
depends_on: [T-0411]
verify: [ops/test]
acceptance: []
---
## Brief

T-0411 measured /plan over the recorded fixtures with a router that takes T per request. After T-0411 a 200 and a
no_scenic_alternative take 4 rounds, but a nothing_pretty answer takes 5: the back-roads offer (lambda 8, the
request honestFailure.backRoadsEta makes) is sent alone after the search, in round 5
(`r4:search@3.25 r5:offer@8` for westwood-malibu +25).

T-0411 built and measured the lever that removes that round. The search's last midpoint always runs alone, so the
offer can ride beside it. That made westwood-malibu +25 take 4 rounds with byte-equal answers. T-0411 dropped it
because the offer is then sent on EVERY scenic plan, including the 200s that never use it: 8 router requests
instead of 7. That changes the request-count contract that 42 tests in 5 files assert (closuresCrossing BASE
"/plan": 6 car_scenic requests, planCost, planCeiling, planRecorded, productionDeps). The 12-call reservation
does not change and P-COST-04's cap holds (at most 11 requests).

The owner needs to decide whether one extra GraphHopper request per plan (about 50 ms of router work plus one
response through the tunnel) is worth about 0.25-0.9 s on each honest-failure answer. If yes: add a `spare` request
to searchLambdaAlongside, launched in the free slot beside its last midpoint (T-0411 Log, L2), update the 42 count assertions to the
new contract with the reason, and set planStages ROUNDS for the two nothing_pretty rows from 5 to 4.

## Log
- 2026-10-18 filed by agent/claude-opus-5 from T-0411's measurement.
