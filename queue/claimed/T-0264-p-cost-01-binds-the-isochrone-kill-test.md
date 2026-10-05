---
id: T-0264
title: P-COST-01 binds the shipped /isochrone KILL and reserve-before-call tests, so the third upstream route is pinned like /plan and /loop
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-05T17:38:34Z
lease_expires_at: 2026-10-06T05:38:34Z
worktree: .worktrees/T-0264
branch: task/T-0264
exclusive: []
touches: [ops/lib/named-tests.json, pins/PINS.yaml]
pins_affected: [P-COST-01, P-COST-04, P-PRIV-05]
reviewer: null
depends_on: [T-0261, T-0262]
verify: [ops/test, ops/check-pins]
acceptance:
  - "ops/lib/named-tests.json binds T-0262's shipped-route tests: /isochrone KILL=1 503 before the body is read (P-COST-01), reserve before the one request (P-COST-01), 1 request per call / 0 on a hit (P-COST-04), the 2-dp start refusal (P-PRIV-05); each pin's prose updated by APPENDING (never rewriting dated text) and its counts corrected"
  - "each new binding RED by a one-line mutant of src/isochrone.ts (KILL ignored on the shipped route; reserve after the fetch; a second fetch; a 3-dp start accepted) quoted in the Log, then green; run-named-tests.py for the three pins exits 0"
---
## Brief

T-0262's stillOpen 1 / rv2 recordable: P-COST-01's statement is 'KILL=1 -> 0 upstream for every route in the router
table'; T-0261 bound /plan and /loop; /isochrone shipped after it and is unbound.

## Log
- 2026-10-05T17:36:29Z filed by agent/claude-opus-5 (orchestrator) after PR #150 (T-0262) merged.
- 2026-10-05T17:38:34Z claimed by agent/claude-opus-5; lease until 2026-10-06T05:38:34Z
- 2026-10-05T17:43:58Z RULINGS before any code (author rule), agent/claude-opus-5.
  R1 (Brief vs code - where the 2 dp check lives): the acceptance names "a 3-dp start accepted" as a mutant of
  src/isochrone.ts, but the 2 dp refusal is isochroneRequest.ts parseReachRequest -> planRequest.ts
  atMostTwoDecimals, whose `toFixed(ORIGIN_DECIMALS)` -> `toFixed(3)` mutant T-0261 already showed RED under
  P-PRIV-05. RULED: the mutant stays in src/isochrone.ts as written - the shipped handler rounding the body's
  lat/lon to 2 dp before parseReachRequest (one line), the regression the /isochrone route can make on its own and
  the only one this binding adds over T-0261's.
  R2 (Brief vs code - where the reservation lives): reserve-before-call is upstream.ts guardedPlan (T-0261's
  mutant moves it for every route). RULED: the src/isochrone.ts mutant is the handler leaving the guard's order -
  the two-line `const buckets = await guardedPlan(...)` statement rewritten as ONE line that runs planReach over
  deps.upstream.fetchImpl first and guardedPlan after (`async () => b`).
  R3 ("a second fetch"): a second guarded call is refused by the budget of 1 (ISOCHRONE_UPSTREAM_COST) and would
  test guardedPlan, not the route. RULED: the second line of that statement chains an UNGUARDED second planReach
  over deps.upstream.fetchImpl after the guarded one - the second request really goes out.
  R4 (which tests bind - all drive the SHIPPED ROUTES['/isochrone'] through SELF.fetch via the harness's reach()):
  P-COST-01 +2 - isochroneCost.test.ts `KILL=1 is 503 before the body is read: zero router requests and no
  reservation` (its body is `{not json`, so one test holds both the KILL and the before-the-body halves) and `the
  surprise allowance and one monthly call are reserved before the one router request`. P-COST-04 +2 - `the request
  count is exactly 1 per call and 0 on a cache hit`, and the reservation test again, since it is the only
  /isochrone test holding ISOCHRONE_UPSTREAM_COST's VALUE (monthly calls = 1) - T-0261 rv1 B1's precedent for
  /plan's 12. P-PRIV-05 +1 - isochroneShape.test.ts `every key at every level is whitelisted, the start is at most
  2 dp and minutes is in [30, 240]`. NOT bound (outside the four acceptance properties): the 429 / tripped-month
  arms (isochroneVerdicts.test.ts names are template strings over a row table) - recorded in the pin prose.
  R5 (counts): P-COST-01 19 -> 21, P-COST-04 7 -> 9, P-PRIV-05 12 -> 13. The prose's earlier counts sit in
  sentences carrying dated RED evidence; RULED: corrected by an APPENDED dated sentence that states the new count
  and supersedes the old one, never by rewriting the dated sentence.
  R6 (acceptance "run-named-tests.py for the three pins exits 0"): the runner runs every bound file of a pin; it
  is run whole for each of the three pins after the mutants, on the merged head.
