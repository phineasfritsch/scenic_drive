---
id: T-0285
title: the ops/funnel tests and mutation population run on every PR - a pin row (anchor source, runs_on linux) that runs ops/lib/funnel_test.py and ops/lib/funnel_mutate.py, seen red
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-06T17:11:12Z
lease_expires_at: 2026-10-07T01:11:12Z
worktree: .worktrees/T-0285
branch: task/T-0285
exclusive: []
touches: [pins/PINS.yaml, ops/lib/funnel_test.py]
pins_affected: [P-PRIV-05]
reviewer: null
depends_on: [T-0284]
verify: [ops/test, ops/check-pins]
acceptance:
  - "pins/PINS.yaml gains a row (id ruled, e.g. P-OPS-07 'ops/funnel's printed output and refusals are pinned') whose assertion runs funnel_test.py and funnel_mutate.py and fails on any failure, missing test or a population below its floor; it runs in CI's pins-source-only job (anchor source - no swift/node needed); seen RED by a one-line mutant of ops/lib/funnel_math.py and by a deleted test, quoted in the Log, then green"
  - "the two non-blocking gaps from T-0284's mutant pass get rows: a missing --fixture path exits 2 (not 4), and a FORMAT JSON body carrying 'statistics' is accepted - each RED by its mutant first"
---
## Brief

T-0284 stillOpen 1: nothing in ops/test, ops/check-pins or CI runs the funnel tests or its population. Also its
fable pass's X1/X2 (exit 2 for an unreadable fixture; the optional 'statistics' key never exercised).

## Log
- 2026-10-06T17:06:00Z filed by agent/claude-opus-5 (orchestrator) after PR #173 (T-0284) review PASS.
- 2026-10-06T17:11:12Z claimed by agent/claude-opus-5; lease until 2026-10-07T01:11:12Z
- 2026-10-06T17:15:07Z rulings, before any code (agent/claude-opus-5):
  - R1 (id): the row is P-OPS-07 (P-OPS-04 is unused/retired and 07 is the next free OPS number), anchor source,
    runs_on [linux, mac]. pins_affected names P-PRIV-05, but that row is anchor api - CI's pins-source-only SKIPS
    it, so extending it would not put the funnel in the cheap gate the acceptance names. P-PRIV-05 is not edited;
    the funnel reader's blob3 refusal (the H3-cell half of that row's statement) is bound by P-OPS-07 through
    FunnelRefusals.
  - R2 (shape): the assertion is inline in pins/PINS.yaml - touches names no new script. It binds the test COUNT
    as a literal (`Ran 13 tests in ...s`) and a bare `OK` line, so a deleted test (count) and a skipped test
    (`OK (skipped=1)` is not `OK`) both fail it, not only a failing one. The population is bound through the
    runner's own printed lines: `population mutations=N (floor 22)` with the floor typed into the pin (lowering
    MIN_MUTATIONS in ops/mutate/funnel_mutations.py changes the printed floor and goes red), `RESULT caught=N
    missed=0 skipped=0 of N` (backreference: every entry caught), and `--prove-floor` exit 0. CRs are stripped
    (Windows python stdout); here-strings, not pipes into grep -q, so pipefail cannot race a SIGPIPE.
  - R3 (X1/X2): two tests in FunnelFixture, full equality on (exit, stdout, stderr): a missing --fixture path ->
    (2, "", "usage: cannot read the fixture (FileNotFoundError)\n"); the fixture plus a ClickHouse-style
    `statistics` object -> (0, EXPECTED, ""). The fixture carries no `statistics` key (measured: keys data, meta,
    rows, rows_before_limit_at_least), which is why X2 survived. Each is shown RED by its mutant of
    ops/lib/funnel.py before it is shown green. Registering X1/X2 as entries of ops/mutate/funnel_mutations.py is
    OUTSIDE touches (pins/PINS.yaml, ops/lib/funnel_test.py) and is recorded as still open, not done.
  - R4 (CI evidence): pins-source-only runs `bash ops/check-pins --source-only` without --verbose and
    .github/workflows is outside touches, so the CI proof that the row ran is the job's `PINS ok=N` line on this
    PR against main's, N one higher. Locally `python3` resolves to the WindowsApps stub, so local runs set
    PYTHON=python, as every existing python row needs.
- 2026-10-06T17:20:36Z red then green (agent/claude-opus-5). Driver: a throwaway script that rewrites one anchor
  (asserted to occur exactly once), purges __pycache__, sleeps 1.1 s, runs, and restores the file byte-identical
  in a finally; `git status --short` afterwards lists only the three touched files.
  - X1 RED 17:17:04Z, mutant ops/lib/funnel.py fixture-OSError branch `return EXIT_USAGE` ->
    `return EXIT_RESPONSE_REFUSED`: FunnelFixture.test_a_missing_fixture_path_exits_2_with_no_output exit=1,
    `AssertionError: Tuples differ: (4, '', 'usage: cannot read the fixture (FileNotFoundError)\n') != (2, '',
    'usage: cannot read the fixture (FileNotFoundError)\n')`, `FAILED (failures=1)`.
  - X2 RED, mutant `TOP_OPTIONAL = {"rows_before_limit_at_least", "statistics"}` -> `TOP_OPTIONAL =
    {"rows_before_limit_at_least"}`: FunnelFixture.test_a_body_carrying_statistics_is_accepted_and_prints_the_same_output
    exit=1, `Tuples differ: (4, '', "RESPONSE_REFUSED: top-level keys [76 chars]]\n") != (0, "FUNNEL
    scenic_telemetry, window: the [666 chars], '')`, `FAILED (failures=1)`.
  - X1 and X2 GREEN on the pristine reader: each `Ran 1 test ... OK` exit=0; whole file `Ran 13 tests in 0.141s`, `OK`.
  - P-OPS-07 appended to pins/PINS.yaml (now 386 lines, 42 rows; ops/lib/funnel_test.py now 236 lines). Its
    assertion, read through ops/lib/pins.py load() and run as pins.py runs it (`bash -o pipefail -c`), 17:18:05Z-17:20:24Z:
    - RED, mutant ops/lib/funnel_math.py `if den == 0:` -> `if den == 1:` (one line): exit=1, output ends
      `ZeroDivisionError: integer division or modulo by zero` / `Ran 13 tests in 0.099s` / `FAILED (errors=2)`.
    - RED, deleted test (FunnelFixture.test_the_sql_is_the_fixed_literal removed, not a killer of any population
      entry, so funnel_mutate.py alone stays green): exit=1, output ends `Ran 12 tests in 0.104s` / `OK` - refused
      on the count alone.
    - RED, the same test decorated @unittest.skip: exit=1, output ends `Ran 13 tests in 0.141s` / `OK (skipped=1)`.
    - RED, MIN_MUTATIONS = 22 -> 21 in ops/mutate/funnel_mutations.py: exit=1 although the output ends `RESULT
      caught=22 missed=0 skipped=0 of 22` - refused on the printed `(floor 21)` against the pinned 22.
    - GREEN, pristine: exit=0 (ok).
- 2026-10-06T17:57:31Z acceptance re-run on the merged head 70f4891 (git fetch origin; origin/main 443463e merged
  LAST - it had moved during the run; main changed one line of pins/PINS.yaml, none of funnel*.py, pins.py or
  linux-core.yml) (agent/claude-opus-5):
  - (1) P-OPS-07's assertion, read through pins.py load() and run bare (`bash -o pipefail`): exit=0. PINS.yaml 42
    rows, no duplicate id, 18 anchor source. RED rows above (funnel_math.py mutant, deleted test, skipped test,
    lowered floor) were run on 2028c50, whose funnel files the merge did not change. CI's pins-source-only on the
    PR is the run that proves the row executes in CI (R4); quoted below when it lands.
  - (2) `python ops/lib/funnel_test.py` -> `Ran 13 tests in 0.202s`, `OK`; X1 and X2 each RED by its mutant, then
    green (above).
  - ops/queue-check `QUEUE OK (277 tasks)` exit=0; ops/lib/check-exec-bits `P-OPS-01: 133 files, 23 required
    present, all modes correct` exit=0. wc -l: ops/lib/funnel_test.py 236, pins/PINS.yaml 386.
  - NOT done locally: a full `ops/check-pins --source-only` started 17:23:21Z on 2028c50 was still inside P-SAFE-03
    (check-safety-disclaimer under git-bash) after 27 minutes on this box, and the merge then changed its tree under
    it; its result is not quoted. ops/test was not run (nothing it builds was touched).
- 2026-10-06T18:10:00Z CI on PR #174 at b7ca0a7 (agent/claude-opus-5): `gh pr checks 174` -> core pass 4m11s,
  pins-source-only pass 2m11s. The pins-source-only job (112421220557) prints `PINS ok=17 skipped=24 pending=1
  expired=0 failed=0 tier=linux source-only`; main's latest run (37504896066) prints `PINS ok=16 skipped=24
  pending=1 expired=0 failed=0 tier=linux source-only` - one more source row run and passed, P-OPS-07 (R4).
- 2026-10-06T18:31:46Z rv1-t0285 FAIL on PR #174 (head 88c0301), B1 closed (agent/claude-opus-5):
  - B1 ruled: P-OPS-07 checked `population mutations=N (floor 22)` and `RESULT caught=X missed=0 skipped=0 of X`
    as two independent greps, never X == N, so a runner that runs a subset stayed green. rv1's tested fix applied
    verbatim to the assertion: N is read from the population line by `sed -n`, must be non-empty, and the RESULT
    line must be exactly `RESULT caught=N missed=0 skipped=0 of N`. P-OPS-07's why_no_test_catches_it gains one
    dated sentence saying so. No other file changed; pins/PINS.yaml stays 386 lines (edits are within two lines).
  - RED, rv1's M1 (ops/lib/funnel_mutate.py line 61 `--only` default "" -> "percent"): the runner prints
    `population mutations=22 (floor 22)` then `RESULT caught=6 missed=0 skipped=0 of 6`; P-OPS-07, read through
    pins.py load() and run with `bash -o pipefail -c`: exit=1.
  - GREEN, M1 reverted by `git checkout -- ops/lib/funnel_mutate.py` and ops/lib/__pycache__ purged (git status
    shows only pins/PINS.yaml modified): the same run exit=0.
