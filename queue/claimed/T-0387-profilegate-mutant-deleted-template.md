---
id: T-0387
title: ops/mutate/profilegate.py's 'the request profile read instead' mutant points at the deleted car_scenic_request.json - re-anchor it on the recorded models
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-17T04:13:14Z
lease_expires_at: 2026-10-18T04:13:14Z
worktree: .worktrees/T-0387
branch: task/T-0387
exclusive: []
touches: [ops/mutate/profilegate.py, services/etl/tests/]
pins_affected: [P-PROD-01]
reviewer: null
depends_on: [T-0190]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0190 deleted services/routing/profiles/car_scenic_request.json. ops/mutate/profilegate.py:88's mutant 'the request profile read instead' still names it, so it is now killed by FileNotFoundError rather than by a gate test (a vacuous kill). Re-anchor the mutant on what a careless edit would really read (a Tests/Fixtures/custom-model/lambda-*.json record), show it CAUGHT by a named test, keep the floor, and add an --prove-vacuity check that no mutant is killed by an exception outside the tests.

## Log
- 2026-10-17 filed by agent/claude-opus-5 from T-0190 stillOpen 2.
- 2026-10-17T04:13:14Z claimed by agent/claude-opus-5; lease until 2026-10-18T04:13:14Z
- 2026-10-17T04:16:37Z MEASURE 1 (the path mutant; .build/t0387/measure.py, gitignored, not shipped: apply the
  mutant to services/etl/etl/profilegate.py, run test_profilegate.py + test_gate_parity.py with --junitxml, read
  each failure's crash site = the last `path:line: Exception` line). Baseline 0 failed of 1593.
  `current: car_scenic_request.json  failed=81 kinds={FileNotFoundError@pathlib: 80, AssertionError@tests: 1}`;
  the one test-site failure is test_gate_parity.py::test_the_profile_read_is_the_shipped_file. Every one of the 7
  recorded lambdas (0, 1, 2, 2.5, 4, 7.75, 8) as PROFILE: `failed=81 kinds={ValueError@subject: 80,
  AssertionError@tests: 1}` (their `else_if`/`else` rules are refused by `priority`). The harness's report
  `caught <- failed[0]` named test_the_shipped_profile_gates_exactly_its_clauses, a FileNotFoundError.
- 2026-10-17T05:38:34Z MEASURE 2 (the whole population, 84 mutants, same script): 84 rows, every one exit=1.
  73 rows have only test-site failures; 84 - 73 = 11 rows carry
  an outside failure; of those, FOUR have ZERO test-site failures - killed only by an exception outside the tests:
  `SAND not a surface` (ValueError@subject x80), `profile: a top-level key the evaluator cannot read`
  (ValueError@subject x80), `a firing speed of 0 not an exclusion` (TypeError@subject x47: `None < 0.0`),
  `profile: ford read off road_environment` (ValueError@subject x80). Totals by kind over all rows:
  AssertionError@tests 69 mutants, Failed@tests 12, KeyError@tests 1, ValueError@subject 9, TypeError@subject 1,
  FileNotFoundError@pathlib 1.
- RULINGS.
  R1 Brief vs reality: the old mutant was NOT killed only by FileNotFoundError - 1 of 81 failures is the
  shipped-file test's assertion - but the harness reported the FileNotFoundError, and that test compares
  PROFILE to a literal path. The vacuous kills are the four rows above. Both are fixed.
  R2 Re-anchor on `lambda-2.json` (the default-ish slider record; all 7 measured identical). Renamed
  `the recorded request model read instead`. Floor stays 84 (the entry replaces one).
  R3 The Brief's "--prove-vacuity check" is enforced in the population run, not the emptied arm: with the
  tests emptied there is no failure whose site could be read. `run_tests` is replaced in ops/mutate/profilegate.py
  (only file this task touches under ops/): a failure counts only when its crash site is under
  services/etl/tests; a mutant with failures but none there prints VACUOUS and is MISSED, failing the run.
  `--prove-vacuity` keeps its emptied arm unchanged.
  R4 The four vacuous mutants get test-site assertions in test_gate_parity.py (an EMPTIED file, so the harness
  runs them): the file config.yml's `custom_model_files` names is PROFILE, every clause of it evaluates
  without a refusal (catches SAND / top-level key / road_environment at the test via pytest.fail), and a
  numeric `limit_to 0` speed rule excludes (catches the `< 0.0` mutant by assertion).
- ACCEPTANCE (written after MEASURE 2).
  A1 RED: on the harness-only commit, `python ops/mutate/profilegate.py --only "SAND not a surface" --only
     "a top-level key" --only "a firing speed of 0" --only "ford read off road_environment"` prints VACUOUS and
     MISSED for the four measured rows and exits 1.
  A2 GREEN: the same line on the tests commit catches every row, each `<-` a tests.test_gate_parity test; exit 0.
  A3 `--only "the recorded request model read instead"` prints `caught` with a test_gate_parity test; exit 0.
  A4 `python ops/mutate/profilegate.py` prints `MUTATE OK  caught=84/84 equivalent_caught=0` and no VACUOUS line.
  A5 `python ops/mutate/profilegate.py --prove-vacuity` prints `VACUITY PROVED`.
  A6 the two test files pass natively; `wc -l` of ops/mutate/profilegate.py and test_gate_parity.py <= 300;
     the bare gates (check-mutate-population, check-mutate-only, check-pins-yaml, check-exec-bits,
     check-safety-disclaimer, queue-check) exit 0.
- 2026-10-17T05:54:05Z RESULTS (commits 80242ee1 acceptance, 02d05116 harness, ae28e603 tests, 02fe7f72 merge of origin/main).
  A1 RED, run 2026-10-17T05:51:23Z on a detached 02d05116 (the harness commit, old tests; the first attempt at
  05:41:09Z was refused by the pristine guard because the test edit was still in the worktree - not a result):
  `VACUOUS 80 failures, every one raised outside the test files` / `MISSED SAND not a surface (exit 1)`, the same
  pair for `profile: a top-level key the evaluator cannot read` (80), `a firing speed of 0 not an exclusion` (47),
  `profile: ford read off road_environment` (80); `MUTATE FAILED  caught=0/4`; A1 exit=1.
  A2 GREEN 05:41:27Z on ae28e603: SAND / top-level key / ford `<- tests.test_gate_parity::test_every_clause_of_the_
  shipped_profile_is_read`; speed `<- tests.test_gate_parity::test_a_numeric_speed_of_zero_excludes`;
  `MUTATE OK  caught=4/4 equivalent_caught=0`; A2 exit=0.
  A3 05:45:30Z: `caught the recorded request model read instead <- tests.test_gate_parity::test_the_profile_read_
  is_the_shipped_file`; `MUTATE OK  caught=1/1`; A3 exit=0.
  Merge of origin/main 05:46Z: 02fe7f72, 0 conflicts. A6 on 02fe7f72: `1596 passed in 21.05s`;
  `271 ops/mutate/profilegate.py`, `186 services/etl/tests/test_gate_parity.py`.
  A5 05:46:51Z on 02fe7f72: `VACUITY: 0 caught, 84 missed, 0 skipped, of 84` / `VACUITY PROVED`; A5 exit=0.
  A4 NOT OBSERVED: the full 84-mutant run started 05:49:56Z on 02fe7f72 and was stopped at 05:51Z by the
  session's tool budget (~60 min run); its stdout was block-buffered and lost; the two subjects were restored with
  `git checkout --` and `git status --short` was empty. Predicted green, not shown: MEASURE 2 put a test-site
  failure on 80 of 84 rows, the old path row is replaced (A3) and the other three vacuous rows are A2's. The
  reviewer or a follow-up session runs `python ops/mutate/profilegate.py` and quotes `MUTATE OK  caught=84/84`.
- 2026-10-17T09:20:55Z agent/claude-opus-5 (owner, orchestrator session): A4 OBSERVED - closes rv1 B1. Merged origin/main (T-0386, T-0388; clean) as 372dabb8, then on that head: __pycache__ purged, `python ops/mutate/profilegate.py` -> 'MUTATIONS: 84 caught, 0 missed, 0 skipped, of 84', 'EQUIVALENT: 0 caught, 1 missed, 0 skipped, of 1', 'MUTATE OK  caught=84/84 equivalent_caught=0', rc 0; no VACUOUS line (grep -c VACUOUS = 0). Bare gates exit 0: check-safety-disclaimer, check-mutate-population, check-mutate-only, check-pins-yaml, check-exec-bits, queue-check.
