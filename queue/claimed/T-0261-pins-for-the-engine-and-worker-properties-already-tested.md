---
id: T-0261
title: PINS rows for the properties the engine and Worker already test but no pin registers - P-SAFE-01, P-SAFE-04, P-PRIV-05, P-COST-01, P-COST-04, P-PROD-02 - each bound to the named tests, each seen red
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-05T14:47:50Z
lease_expires_at: 2026-10-06T02:47:50Z
worktree: .worktrees/T-0261
branch: task/T-0261
exclusive: []
touches: [pins/PINS.yaml, ops/lib/]
pins_affected: [P-SAFE-01, P-SAFE-04, P-PRIV-05, P-COST-01, P-COST-04, P-PROD-02]
reviewer: null
depends_on: [T-0248, T-0252, T-0253]
verify: [ops/test, ops/check-pins]
acceptance:
  - "pins/PINS.yaml gains one row per id with statement (the plan's own wording, plan Pins table), why_no_test_catches_it, anchor, runs_on: [linux], owner, added; each assertion runs the EXISTING tests that prove it by NAME (vitest -t / file filters under services/api, swift test --filter for Surprise/LambdaSearch suites) through one small ops/lib runner that FAILS if the named tests are missing, skipped or zero (a filter that matches nothing must be red, never a vacuous green)"
  - "each new row is seen RED by a one-line mutant of the shipping code it protects (e.g. quota reserved after the upstream call for P-COST-01, a 3-dp origin accepted for P-PRIV-05, the ceiling read from the scenic ETA for P-SAFE-04, a request beyond the cap for P-COST-04, a client custom_model touching road_access accepted for P-SAFE-01, the seed ignoring the date for P-PROD-02), quoted in the Log with the runner's output, then green; and once with the named test renamed (the runner refuses by name)"
  - "'bash ops/check-pins --source-only' (or CI's pins-source-only as the run of record on this box) prints the six ids ok; P-COST-03's VPS half stays unregistered and is named in why_no_test_catches_it of P-COST-01 as out of scope"
---
## Brief

T-0248 stillOpen 3, T-0252, T-0253 stillOpen 1 and T-0256: the Worker and the engine ship tests for six plan pins
(Pins table: P-SAFE-01 profile gates + Worker rejection of road_access/surface models; P-SAFE-04 budget ceiling;
P-PRIV-05 one coordinate, 2 dp; P-COST-01 quota before every VPS call and KILL=1 -> 0 upstream; P-COST-04 requests
per plan <= 12/3/12; P-PROD-02 Surprise reproducible per (user, day, seed) and >= 90% distinct) but pins/PINS.yaml
registers none of them, so ops/check-pins cannot say they hold and M6's exit (P-COST/P-PRIV green) has nothing to
read. Anchor on test names and shipping symbols, never comments (CLAUDE.md).

## Log
- 2026-10-05T14:46:01Z filed by agent/claude-opus-5 (orchestrator) after PR #144 (T-0253) merged.
- 2026-10-05T14:47:50Z claimed by agent/claude-opus-5; lease until 2026-10-06T02:47:50Z
- 2026-10-05T14:59:15Z RULINGS before code (agent/claude-opus-5, owner).
  R1 WHERE THE ROWS RUN - acceptance bullet 3 vs reality. CI's pins-source-only job is plain ubuntu-latest with
     no Swift toolchain and no `npm ci` (.github/workflows/linux-core.yml), and .github/ is not in this task's
     touches. An assertion that runs vitest or `swift test` cannot be green there, so these six rows are NOT
     `anchor: source`: they run in the `core` job's full `bash ops/check-pins`, which has swift 6.1, node 22 and
     services/api deps installed and has already built the root package in `ops/test`. Anchors: `api` for the
     five rows whose tests drive the Worker's shipped handlers (P-SAFE-01, P-SAFE-04, P-PRIV-05, P-COST-01,
     P-COST-04) and `artifact` for P-PROD-02 (the built ScenicKit test binary over Surprise.pick). The run of
     record is therefore the `core` job's check-pins step, not pins-source-only; `--source-only` skips them by
     design. Each assertion is also run directly on this box and quoted.
  R2 STATEMENTS are the plan Pins-table wording verbatim. Where the plan row says more than the existing tests
     prove, the unproved clauses are NAMED in why_no_test_catches_it as not asserted by this row (no new tests:
     this task registers what is already tested): P-SAFE-01's profile-JSON half (car_scenic_base.json's
     private/unpaved/track zero-gates - test_profiles_static.py has no test of them); P-PRIV-05's server-column
     grep, learned-speed Codable and H3-5 clauses; P-COST-01's "every route in the router table" holds only for
     the two upstream routes that exist (/plan, /loop), each by its own test - nothing iterates ROUTES; P-COST-04's
     road-trip 12 (no road-trip endpoint) and "<= 2 in flight" (tested for /plan as one-in-flight only).
     P-COST-03's VPS half stays unregistered and is named out of scope in P-COST-01.
  R3 RUNNER: ops/lib/run-named-tests.py <PIN-ID> reads its pin's names from ops/lib/named-tests.json (data,
     100644) and runs only the files/suites that hold them. Vitest: `npx vitest run <files> --reporter=json
     --outputFile=<tmp>` under services/api; a test's name is `<file> :: <describe> > ... > <it>` built from
     assertionResults' ancestorTitles + title. Swift: `swift test --scratch-path $SCENIC_SWIFT_SCRATCH (default
     .build, the path ops/test built in CI) --filter <suite regex> --xunit-output <tmp>/x.xml`, reading
     x-swift-testing.xml (and x.xml); a test's name is `<classname>/<name>`, i.e. Module.Suite/function() - the
     IDENTIFIER, not the display string. Every named test must appear at least once and every occurrence must be
     passed. Red BY NAME: MISSING (not in the report), SKIPPED/TODO/PENDING, FAILED. Red without a name: an
     unknown pin id, a pin with zero names, a missing/unparsable report. The reporter's exit status is not
     trusted either way; only the parsed report decides. Prints `NAMED <pin> passed=N/M` and exits 1 unless N == M > 0.
  R4 PER-PIN TEST LISTS (Worker paths under services/api/test; Swift under Tests/ScenicKitTests):
     P-SAFE-01: customModel.test.ts (b) rejectCustomModel - top-level, nested else_if, areas property, object
       KEY, any case; customModelGate.test.ts (f) - middle, key containing, ends a string, deep areas value,
       upper-case middle; planPrivacy.test.ts R1 "refuses a request-supplied custom_model naming road_access";
       planRecorded.test.ts "visits exactly the recorded lambdas ... no safety-gate name (P-SAFE-01)".
     P-SAFE-04: planCeiling.test.ts "POST /plan budget ceiling (R7, P-SAFE-04)" - 120 random curves, every
       overshoot -> no_route, exactly at the ceiling returned; lambdaSearch.test.ts no_feasible_lambda; Swift
       LambdaSearchTests ceilingAlwaysHolds(), nonMonotoneRouterIsSafe(), ceilingIsNotApproximate(),
       ceilingBoundaryIsExactToTheLastBit(), returnsMeasuredValues(); LambdaSearchSteeringTests (3);
       LambdaSearchRefusalTests noFeasibleLambdaThrows(); PlanCeilingOverLATests everyPlanStaysUnderTheCeiling().
     P-PRIV-05: planPrivacy.test.ts "POST /plan privacy - one coordinate, two decimals (R2, P-PRIV-05)" (all 7);
       loopShape.test.ts "the /loop body whitelist (R1, P-PRIV-05)" (5) and "the one request carries one point -
       the 2 dp start".
     P-COST-01: planCost.test.ts R4 (6) + shipped-route KILL; loopCost.test.ts R8 (5) + shipped-route KILL;
       upstream.test.ts guardedUpstream "reserves BEFORE calling, not after", NO-call arms (daily, volume, manual
       kill), guardedPlan "reserves before the plan body runs", "makes NO call at all when the plan is refused".
     P-COST-04: planCost.test.ts R5 "7 upstream requests - at most 12 - one in flight"; loopCost.test.ts R5
       "at most 3 upstream requests", "guardedPlan at LOOP_UPSTREAM_COST refuses a 4th request before fetch";
       upstream.test.ts "refuses the call past the budget, and does not make it", "the reservation is an upper
       bound on calls actually made"; quota.test.ts "a plan is priced in upstream calls, not in plans".
     P-PROD-02: SurpriseRankTests reproducible(), distinct(), permutation(); SurpriseFeedbackTests wrongTime().
       permutation() and wrongTime() are in the list because reproducible()/distinct() alone cannot see a pick
       that ignores the DATE (it stays reproducible and distinct) - the oracle permutation binds (user, day).
  R5 MUTANTS (one line each, shipping code, applied and reverted by hand, outputs quoted below):
     P-SAFE-01 customModel.ts mentioned(): `includes(word)` -> `=== word`; P-SAFE-04 Worker lambdaSearch.ts
     feasibility read from the scenic duration and Swift LambdaSearch.swift likewise; P-PRIV-05 planRequest.ts
     atMostTwoDecimals toFixed(ORIGIN_DECIMALS) -> toFixed(3); P-COST-01 upstream.ts reserve deferred to a
     microtask (lands after the first upstream call); P-COST-04 upstream.ts `spent > budget` -> `spent > budget + 1`;
     P-PROD-02 Surprise.draw key drops the date. Plus, per runner: one named test renamed in its file.
- 2026-10-05T15:22:59Z RED THEN GREEN (agent/claude-opus-5). Runner ops/lib/run-named-tests.py (166 lines, 100755)
  + ops/lib/named-tests.json (100644), committed 87eb577. Local Swift runs used SCENIC_SWIFT_SCRATCH=.build/t0261.
  Baseline before any mutant: `NAMED P-SAFE-01 passed=12/12`, `P-PRIV-05 12/12`, `P-COST-01 18/18`,
  `P-COST-04 6/6`, `P-PROD-02 4/4`, `P-SAFE-04 15/15`, each exit=0.
  MUTANTS (one line of shipping code each, applied by exact-once replacement, reverted with git checkout):
  - P-SAFE-01 customModel.ts mentioned() `lowered.includes(word)` -> `lowered === word`:
    `NAMED P-SAFE-01 passed=3/12` exit=1; RED by name: customModel (b) top-level / nested else_if / areas property
    / ROAD_ACCESS case, customModelGate (f) all five. (The /plan R1 test stays green - the body whitelist refuses
    a custom_model key before rejectCustomModel is reached; the recorded-lambda test too - the built model is clean.)
  - P-PRIV-05 planRequest.ts atMostTwoDecimals `toFixed(ORIGIN_DECIMALS)` -> `toFixed(3)`: `passed=10/12` exit=1;
    RED: planPrivacy `refuses an origin latitude with more than 2 decimals, with zero upstream calls`, loopShape
    `refuses a start with more than 2 decimals`.
  - P-COST-01 upstream.ts `await deps.counters.reserve(args.userId, budget, now);` ->
    `void Promise.resolve().then(() => deps.counters.reserve(args.userId, budget, now));`: `passed=14/18` exit=1;
    RED: planCost `the quota is reserved once, before the first upstream call`, loopCost `the quota is reserved
    once, LOOP_UPSTREAM_COST of it, before the first upstream call`, upstream `reserves BEFORE calling, not after`,
    `reserves before the plan body runs, not before each call`.
  - P-COST-04 upstream.ts `spent > budget` -> `spent > budget + 1`: `passed=4/6` exit=1; RED: loopCost `guardedPlan
    at LOOP_UPSTREAM_COST refuses a 4th request before fetch`, upstream `refuses the call past the budget, and does
    not make it`.
  - P-SAFE-04 (Worker) lambdaSearch.ts `if (duration <= ceiling && (` -> `if (duration <= duration + budget && (`:
    `passed=11/15` exit=1; RED: planCeiling 120-curves and every-overshoot -> no_route, lambdaSearch
    no_feasible_lambda and non-monotone. (Swift) LambdaSearch.swift `if d <= ceiling, best == nil` ->
    `if d <= d + budget, best == nil`: `passed=7/15` exit=1; RED: LambdaSearchTests ceilingAlwaysHolds(),
    nonMonotoneRouterIsSafe(), ceilingIsNotApproximate(), ceilingBoundaryIsExactToTheLastBit(), steering x2,
    noFeasibleLambdaThrows(), PlanCeilingOverLATests/everyPlanStaysUnderTheCeiling().
  - P-PROD-02 Surprise.draw key `"\(userId)|<date>|\(step)"` -> `"\(userId)|\(step)"`: `passed=2/4` exit=1; RED:
    SurpriseRankTests/permutation(), SurpriseFeedbackTests/wrongTime(); reproducible() and distinct() GREEN under
    the mutant, which is ruling R4's reason for binding the other two.
  RENAMED / SKIPPED / EMPTY (each refused by name, each reverted):
  - P-SAFE-01 `refuses road_access in a top-level condition` renamed: `passed=11/12` `RED ... MISSING - no test of
    this name ran`. P-PRIV-05 origin-latitude test renamed: `11/12` MISSING. P-COST-01 `the quota is reserved once,
    before the first upstream call` renamed: `17/18` MISSING; its KILL=1 test `it.skip`: `17/18` `SKIPPED -
    ['skipped']`. P-COST-04 `refuses the call past the budget, and does not make it` renamed: `5/6` MISSING.
    P-SAFE-04 `func everyPlanStaysUnderTheCeiling()` renamed: `14/15` MISSING. P-PROD-02 `func reproducible()`
    renamed: `3/4` MISSING; its swift filter pointed at a suite that does not exist: `passed=0/4`, all four MISSING
    (zero matched tests is red). Table emptied for a pin: `NAMED P-COST-04 REFUSED: P-COST-04 has no entry in
    named-tests.json`; an unknown pin: `NAMED P-NOPE REFUSED`. All exit=1.
  GREEN through ops/lib/pins.py's own run() over the appended PINS.yaml rows (PINS.yaml parsed: 38 rows):
  `ok P-SAFE-01 anchor=api :: NAMED P-SAFE-01 passed=12/12`, `ok P-SAFE-04 anchor=api :: passed=15/15`,
  `ok P-PRIV-05 anchor=api :: passed=12/12`, `ok P-COST-01 anchor=api :: passed=18/18`, `ok P-COST-04 anchor=api
  :: passed=6/6`, `ok P-PROD-02 anchor=artifact :: passed=4/4`; every row carries statement, why_no_test_catches_it,
  anchor, runs_on [linux], assertion, owner, added.
- 2026-10-05T15:31:45Z FINAL PRE-REVIEW (agent/claude-opus-5). R6 (ruled now, found by the gate): ops/lib/check-exec-bits
  (P-OPS-01) classifies every `*.py` under ops/ as DATA, 100644 - a .py is always run as `"$PY" ops/lib/x.py`,
  never directly, and all 22 other ops/lib/*.py are 100644. 87eb577 committed run-named-tests.py 100755 per the
  generic "new ops/ scripts executable" line and the gate refused it: `P-OPS-01: wrong git file mode:
  ops/lib/run-named-tests.py (data, should be 100644, is 100755)`. The gate wins; the file is now 100644 and every
  assertion invokes it through `${PYTHON:-...}`. Merged origin/main at 7995d95 (T-0256 #147 landed: upstream.ts's
  reserve now takes `kind, args.tier`). Re-run on the merged head: the six assertions through pins.py's run()
  (`PINS.yaml parsed: 38 rows`; `ok P-SAFE-01 passed=12/12`, `ok P-SAFE-04 15/15`, `ok P-PRIV-05 12/12`,
  `ok P-COST-01 18/18`, `ok P-COST-04 6/6`, `ok P-PROD-02 4/4`); every other mutant site still occurs exactly once;
  the P-COST-01 mutant re-applied to the new line (`await deps.counters.reserve(args.userId, budget, now, kind,
  args.tier);` -> deferred to a microtask) is `NAMED P-COST-01 passed=14/18` exit=1, the same four reserve-before
  tests FAILED by name, then restored; `QUEUE OK (253 tasks)`. The run of record for the six ids is CI's `core`
  job `bash ops/check-pins` (R1); `--source-only` skips them by design.
- 2026-10-05T16:01:19Z PRE-REVIEW MUTANT PASS SURVIVORS CLOSED (agent/claude-opus-5, owner).
  M4 (BLOCKING): index.ts `"/loop": (req, env) => handleLoop(req, env, loopDepsFromEnv(env))` ->
  `handleLoop(req, { ...env, KILL: undefined }, loopDepsFromEnv(env))` printed `NAMED P-COST-01 passed=18/18` exit 0:
  all five bound /loop R8 tests call handleLoop directly and none reached ROUTES['/loop'], so the row's "one test per
  upstream route" was false for /loop. The catching test already existed unbound. ops/lib/named-tests.json now binds
  `ROUTES['/loop'] - the shipped wiring (R10) > KILL=1 on the shipped route answers 503 planning_paused` under
  P-COST-01 / test/loopCost.test.ts (18 -> 19). Same mutant re-applied: `RED test/loopCost.test.ts :: ROUTES['/loop']
  - the shipped wiring (R10) > KILL=1 on the shipped route answers 503 planning_paused: FAILED - ['failed']`,
  `NAMED P-COST-01 passed=18/19` exit=1; restored: `NAMED P-COST-01 passed=19/19` exit=0. P-COST-01's prose: nineteen,
  the shipped /loop KILL test named, the M4 red quoted.
  M2b (emptied body): RULED a design limit of by-name binding, closed by wording, not by a test. Re-run on the
  19-binding table: M2a (`"/plan": ... handlePlan(req, { ...env, KILL: undefined }, ...)`) plus the body of the /plan
  `KILL=1 on the shipped route answers 503 planning_paused` replaced by `expect(1).toBe(1)` -> `NAMED P-COST-01
  passed=19/19` exit=0, as predicted. A second shipped-route test would need services/api/test/, outside this task's
  touches, and would only move the limit (gut both bodies); the runner reads vitest's per-test status, which carries
  no assertion content. All six rows' why_no_test_catches_it now end with a BY-NAME LIMIT sentence: the runner refuses
  deleted, renamed, skipped or not-run tests and cannot see an emptied body, so the bindings hold presence and bodies
  stay a review matter; P-COST-01's NOT ASSERTED HERE now says ONE shipped-route test per route, each a single body.
  Reviewer rules whether that gap needs a filed follow-up. PINS.yaml through pins.load: 38 rows, the six with all
  eight keys. LF only.
