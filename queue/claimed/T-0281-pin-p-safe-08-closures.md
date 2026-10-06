---
id: T-0281
title: register P-SAFE-08 (closures fresh within 30 min; a route never crosses an active closure; stale/unavailable never silent) over T-0276's tests, and bind T-0276's shipped-route closure tests under P-SAFE-01
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-06T14:11:11Z
lease_expires_at: 2026-10-06T22:11:11Z
worktree: .worktrees/T-0281
branch: task/T-0281
exclusive: []
touches: [pins/PINS.yaml, ops/lib/named-tests.json]
pins_affected: [P-SAFE-08, P-SAFE-01]
reviewer: null
depends_on: [T-0276, T-0261]
verify: [ops/test, ops/check-pins]
acceptance:
  - "pins/PINS.yaml gains P-SAFE-08 (the plan's statement; anchor api; runs_on linux) asserted by run-named-tests.py over the named closuresRoutes/closuresCron/closuresFeed tests: the 30-min boundary rows (fresh at exactly 30 min, stale at +1 ms), the unavailable cross-product meta-test, the every-driven-request-carries-the-areas tests and the cron active-window clock table; each binding RED by a one-line mutant of src/ quoted in the Log, then green; WHAT IT CANNOT SEE names /isochrone's missing areas (T-0276 R8), the 50-polygon cap dropping closures, and the owner's unbound CLOSURES KV"
  - "prose APPENDED with dates, never rewritten; run-named-tests for P-SAFE-08 and P-SAFE-01 exit 0"
---
## Brief

T-0276 stillOpen 2: 'P-SAFE-08 needs a PINS.yaml row and a by-name binding; pins/ was outside this task's touches'.
The T-0261/T-0269 pattern.

## Log
- 2026-10-06T14:08:18Z filed by agent/claude-opus-5 (orchestrator) after PR #167 (T-0276) merged.
- 2026-10-06T14:11:11Z claimed by agent/claude-opus-5; lease until 2026-10-06T22:11:11Z
- 2026-10-06T14:26:04Z RULINGS (before any edit). Measured first: `npx vitest run` over the four closures files in
  this worktree (after `npm ci`) - closuresRoutes 578, closuresFeed 61, closuresCron 27, closuresDriven 3, all
  passed. Row schema copied from P-SAFE-01 / P-STORE-02 (anchor api; runs_on [linux]; assertion
  `"${PYTHON:-...}" ops/lib/run-named-tests.py <PIN>`; owner; added).
  R1 statement: the plan's row verbatim - "Closure cron freshness <= 30 min in prod; route never crosses an active
  closure polygon". Plan's checker is `ops/sane + golden`; neither exists for closures, so the row is asserted by
  run-named-tests.py (as T-0261/T-0269) and the prod half (a deployed cron, a bound KV) is named as unseen.
  R2 P-SAFE-08 test list (599 names), by describe, not hand-picked rows:
  closuresRoutes.test.ts (570): every test of `a fresh set rides every driven request as areas (R7, R8)` (4; the
  three per-route rows are the record at EXACTLY 30 min - NOW - MAX_AGE_MS, the test's own literal 1_800_000);
  every test of `stale: the last good set, with the hazard (R7, P-SAFE-08)` (32 rows incl. the 30 min + 1 ms row
  per route x set, its 5-test meta, and `a record exactly 0 ms old is fresh`); every test of
  `unavailable: no set, never silent (R7)` (448 route x shape x set rows AND the 57-test meta) - Brief vs
  acceptance: the acceptance names only the meta-test, but the meta compares test-built records and calls no src/
  symbol, so the rows are what see the hazard; both are bound; every test of `read, by ruling ...` (22; fresh
  accepted shapes routed around exactly their set) and `/isochrone: the same closures-version hits the cache; ...
  a hit carries the hazard` (never silent on a cache hit). NOT bound: the KILL/reads-once rows (R9/R10, not this
  pin). closuresDriven.test.ts (3, all: loop attempts and trip day legs carry the set). closuresCron.test.ts (10:
  the clock table `the cron's clock through scheduled() ...`). closuresFeed.test.ts (16: `the recorded D7
  response` 2 and the 14 active-window rows of `the bounds a row is ACCEPTED at` whose names end " active"; the
  coordinate/decimals/chord rows are R3/R4 geometry, not this pin).
  R3 P-SAFE-01: the three `a fresh set rides ... > /plan|/loop|/trip: ... gate-clean; no car_fast model` tests
  assert rejectCustomModel(model) === null on every shipped-route model that carries the areas - those are T-0276's
  shipped-route closure tests for P-SAFE-01; appended to its named list (12 -> 15).
  R4 red: one-line mutants of services/api/src/ through run-named-tests.py, one at a time, restored by
  `git checkout`. EXCEPTION ruled: the unavailable/stale meta-tests call no src/ symbol (closuresFake imports only
  CLOSURES_KEY and types), so no src/ mutant can redden them; their binding is shown red by a one-line mutant of
  the test file's HOLDS_NO_SET call (names change -> MISSING by name), restored.
  R5 prose APPENDED: P-SAFE-08 is a new row; P-SAFE-01's why_no_test_catches_it gains a dated sentence at its end,
  nothing before it rewritten.
- 2026-10-06T14:40:37Z BOUND + RED/GREEN. ops/lib/named-tests.json gains P-SAFE-08 (599 names: closuresRoutes 570,
  closuresCron 10, closuresFeed 16, closuresDriven 3) and P-SAFE-01 gains test/closuresRoutes.test.ts (3; 12 -> 15),
  generated from the measured vitest JSON report by describe prefix (scratch script, not committed). GREEN before
  mutants: `NAMED P-SAFE-08 passed=599/599` (16 s), `NAMED P-SAFE-01 passed=15/15`. RED, one mutant at a time
  through `python ops/lib/run-named-tests.py <PIN>`, each restored by `git checkout` and `git status` clean after:
    M1 closuresStore.ts `age >= 0 && age <= CLOSURES_MAX_AGE_MS` -> `age < ...`: exit=1 NAMED P-SAFE-08
       passed=596/599 - the three `a fresh set rides ... > /plan|/loop|/trip: ...` (the record at EXACTLY 30 min) FAILED
    M2 `CLOSURES_MAX_AGE_MS = 30 * 60 * 1000;` -> `... + 1;`: exit=1 passed=590/599 - the eight `30 min + 1 ms old`
       stale rows and the /isochrone cache-hit test (its record is MAX_AGE_MS + 1 old) FAILED
    M3 withClosuresHazard `return snapshot.hazard === null ? answer` -> `snapshot.hazard?.state !== "stale"`:
       exit=1 passed=151/599 - all 448 `unavailable: no set, never silent (R7) > ...` rows FAILED
    M4 tripPlanner.ts `buildCustomModel(outcome.lambda, closures)` -> `null`: exit=1 passed=598/599 -
       `a paid trip's day legs carry the closures (R8) > every car_scenic request - the search and the five legs ...` FAILED
    M5 loopPlanner.ts `buildCustomModel(LOOP_LAMBDA, closures)` -> `null`: exit=1 passed=588/599 (/loop fresh,
       round-trip-whole and stale-over-two-closures rows FAILED)
    M6 plan.ts `request.budgetMinutes * 60, snapshot.closures));` -> `null));`: exit=1 passed=591/599 (/plan rows)
    M7 closuresCron.ts `Math.floor(nowMs / 1000)` -> `Math.ceil(...)`: exit=1 passed=596/599 - the clock table's
       `now at .500` / `.999` rows FAILED
    M8 lcsFeed.ts `start <= nowS &&` -> `start < nowS &&`: exit=1 passed=595/599 - clock rows `a window opening at
       now's second ...` and closuresFeed `the bounds a row is ACCEPTED at (R2-R4) > start == now is active` FAILED
    M9 (R4 exception, test file) closuresRoutes.test.ts `handed(row(set))]), HOLDS_NO_SET);` -> `handed(row(set))]));`:
       exit=1 passed=593/599 - six `meta: every unavailable row is a function of its set > ...: ... equals ...` MISSING by name
    M10 P-SAFE-01, customModel.ts `closure_${index + 1}` -> `surface_${index + 1}`: exit=1 NAMED P-SAFE-01
       passed=12/15 - the three gate-clean fresh rows FAILED
    M1b P-SAFE-01, M1 again: exit=1 passed=12/15, the same three FAILED.
  NOT individually reddened by a src mutant (bound, green, presence held by name): the 22 `read, by ruling` rows,
  the stale meta (5, test-internal like M9's), `the recorded D7 response` (2) and the feed rows whose bound no
  mutant above moved. PINS.yaml: P-SAFE-08 row added after P-STORE-02 (anchor api; runs_on [linux]); P-SAFE-01's
  why_no_test_catches_it gains one dated APPENDED sentence after its last word. Note: `yaml.safe_load` of
  pins/PINS.yaml fails at line 213 col 344 on HEAD 0cb8c82 too (pre-existing, not this task's line; ops/lib/pins.py
  parses it its own way).
