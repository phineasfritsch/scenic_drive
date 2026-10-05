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
- 2026-10-05T17:56:17Z RED then GREEN by name (driver .build-t0264/mutants.py, gitignored; each mutant applied to
  services/api/src/isochrone.ts, run under the OLD table from HEAD f3baf0d and the NEW ops/lib/named-tests.json,
  then restored). The OLD-table rows show the gap the Brief names (every mutant green 19/19, 7/7, 12/12); the
  NEW-table rows are red by name; GREEN is the restored source. Verbatim:
  ```
  M1 KILL ignored on the shipped route - OLD table (HEAD)
      P-COST-01 exit=0
        NAMED P-COST-01 passed=19/19
  M1 KILL ignored on the shipped route - NEW table
      P-COST-01 exit=1
          RED test/isochroneCost.test.ts :: ROUTES['/isochrone'] spend control (R4, R5, P-COST-01) > KILL=1 is 503 before the body is read: zero router requests and no reservation: FAILED - ['failed']
        NAMED P-COST-01 passed=20/21
  M2 reserve after the fetch - OLD table (HEAD)
      P-COST-01 exit=0
        NAMED P-COST-01 passed=19/19
      P-COST-04 exit=0
        NAMED P-COST-04 passed=7/7
  M2 reserve after the fetch - NEW table
      P-COST-01 exit=1
          RED test/isochroneCost.test.ts :: ROUTES['/isochrone'] spend control (R4, R5, P-COST-01) > the surprise allowance and one monthly call are reserved before the one router request: FAILED - ['failed']
        NAMED P-COST-01 passed=20/21
      P-COST-04 exit=1
          RED test/isochroneCost.test.ts :: ROUTES['/isochrone'] spend control (R4, R5, P-COST-01) > the surprise allowance and one monthly call are reserved before the one router request: FAILED - ['failed']
        NAMED P-COST-04 passed=8/9
  M3 a second, unguarded fetch - OLD table (HEAD)
      P-COST-04 exit=0
        NAMED P-COST-04 passed=7/7
      P-COST-01 exit=0
        NAMED P-COST-01 passed=19/19
  M3 a second, unguarded fetch - NEW table
      P-COST-04 exit=1
          RED test/isochroneCost.test.ts :: ROUTES['/isochrone'] request count and the daily cache (R5, R6, P-COST-04) > the request count is exactly 1 per call and 0 on a cache hit: FAILED - ['failed']
          RED test/isochroneCost.test.ts :: ROUTES['/isochrone'] spend control (R4, R5, P-COST-01) > the surprise allowance and one monthly call are reserved before the one router request: FAILED - ['failed']
        NAMED P-COST-04 passed=7/9
      P-COST-01 exit=1
          RED test/isochroneCost.test.ts :: ROUTES['/isochrone'] spend control (R4, R5, P-COST-01) > the surprise allowance and one monthly call are reserved before the one router request: FAILED - ['failed']
        NAMED P-COST-01 passed=20/21
  M4 a 3-dp start accepted (rounded to 2 dp before the parse) - OLD table (HEAD)
      P-PRIV-05 exit=0
        NAMED P-PRIV-05 passed=12/12
  M4 a 3-dp start accepted (rounded to 2 dp before the parse) - NEW table
      P-PRIV-05 exit=1
          RED test/isochroneShape.test.ts :: POST /isochrone takes one coordinate at 2 dp and nothing else (R1, P-PRIV-05) > every key at every level is whitelisted, the start is at most 2 dp and minutes is in [30, 240]: FAILED - ['failed']
        NAMED P-PRIV-05 passed=12/13
  GREEN - src restored, NEW table
      P-COST-01 exit=0
        NAMED P-COST-01 passed=21/21
      P-COST-04 exit=0
        NAMED P-COST-04 passed=9/9
      P-PRIV-05 exit=0
        NAMED P-PRIV-05 passed=13/13
  DONE
  ```
  pins/PINS.yaml: one dated sentence APPENDED to each of P-COST-01, P-COST-04, P-PRIV-05 why_no_test_catches_it
  (no earlier text changed) carrying the corrected counts 21 / 9 / 13 and these mutants.
- 2026-10-05T18:11:53Z FINAL pre-review re-run of the whole acceptance block. `git fetch origin` + `git merge origin/main`:
  "Already up to date" (origin/main = e923e39, this branch's base), so the merged head is 4f468a0. Re-quoted:
  1. "ops/lib/named-tests.json binds T-0262's shipped-route tests ..." - DONE: P-COST-01 +2 (isochroneCost KILL
     before the body; reserve before the one request), P-COST-04 +2 (1 request per call / 0 on a hit; the
     reservation test, which holds ISOCHRONE_UPSTREAM_COST = 1), P-PRIV-05 +1 (isochroneShape 2 dp whitelist).
     Counts 19 -> 21, 7 -> 9, 12 -> 13 corrected by one APPENDED dated sentence per row; no earlier text changed
     (git diff of pins/PINS.yaml: 3 lines, each the old line plus a suffix).
  2. "each new binding RED by a one-line mutant of src/isochrone.ts ... then green; run-named-tests.py for the
     three pins exits 0" - DONE: M1-M4 above red by name under the new table (green under the old one), then on
     the merged head 4f468a0:
       NAMED P-COST-01 passed=21/21   run-named-tests P-COST-01 exit=0
       NAMED P-COST-04 passed=9/9     run-named-tests P-COST-04 exit=0
       NAMED P-PRIV-05 passed=13/13   run-named-tests P-PRIV-05 exit=0
  Gates: `QUEUE OK (255 tasks)` queue-check exit=0; `P-PROC-06: ... 0 added by this branch ... the floor of 55
  holds` check-mutate-population exit=0. check-line-cap: this PR touches no Swift; the local run did not finish
  on this box (a `find` over Sources), CI is its run of record.
  Noted, not this task's: PyYAML refuses pins/PINS.yaml already at e923e39 (line 213, and P-COST-01's T-0261 text
  `"/loop": ...` carries bare double quotes inside its double-quoted scalar); this task did not introduce it, its
  appended sentences carry no double quote or backslash, and CI's ops/check-pins is the run of record. Ready for
  review by an agent other than agent/claude-opus-5.
