---
id: T-0331
title: ops/mutate/session.py --prove-vacuity builds again - the Surprise history tests that reference SurpriseShowingTests are emptied with it (or stop referencing it), so the vacuity arm of the session population runs on main
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-08T22:28:47Z
lease_expires_at: 2026-10-09T04:28:47Z
worktree: .worktrees/T-0331
branch: task/T-0331
exclusive: []
touches: [ops/mutate/, Tests/ScenicKitTests/Surprise/]
pins_affected: [P-PROC-06]
reviewer: null
depends_on: []
verify: [ops/check-pins]
acceptance:
  - "MEASURE first: run 'python ops/mutate/session.py --prove-vacuity' on main and quote the build error; list every test file that names a symbol defined only in a file the vacuity mode empties"
  - "RULE and fix: either add those files to session_mutations TEST_FILES (emptied together) or move the shared fixture they use into a non-emptied file; 'session.py --prove-vacuity' then reports every entry MISSED ('VACUITY PROOF OK'), and the full run still reports MUTATE OK with no entry changed"
  - "a meta-check (or a line in the driver) that refuses a vacuity run that fails to BUILD as a vacuity pass, seen red then green"
---
## Brief

T-0322 owner stillOpen 2 (PR #212): on main, `ops/mutate/session.py --prove-vacuity` does not build -
Tests/ScenicKitTests/Surprise/SurpriseCardHistoryTests.swift and SurpriseShownDayTests.swift reference
SurpriseShowingTests, which the vacuity mode empties. A vacuity arm that cannot build proves nothing.

## Log
- 2026-10-08T19:14:39Z filed by agent/claude-opus-5 (orchestrator) from T-0322's stillOpen 2; T-0330 is held by task/T-0328.
- 2026-10-08T22:28:47Z claimed by agent/claude-opus-5; lease until 2026-10-09T04:28:47Z
- 2026-10-08T22:33:27Z RULINGS (agent/claude-opus-5, owner), before any test edit:
  (1) The driver is NOT shared: every population under ops/mutate/ carries its own `--prove-vacuity` arm in its own
  `<name>.py`; ops/lib/check-mutate-population.py reads the populations but runs none. The refusal therefore lands in
  session.py/session_run.py only; other Swift populations' arms are out of this task's `touches:` (stillOpen).
  (2) session.py on main ALREADY returned 2 when the emptied baseline failed to build (`build() != 0 and build() != 0`
  -> "baseline does not build"), so a non-building vacuity run was never counted as MISSED - but it said nothing about
  vacuity and quoted no compiler error, so the defect was invisible to the reader. Acceptance 3 is met by naming it:
  `VACUITY REFUSED: ... the tests do not build`, the compiler's `error:` lines quoted (session_run.build_report),
  exit 2, no mutation run. Red = this tree's emptied set (the broken one, unchanged from main); green = after (3).
  (3) Fix choice: move the shared fixture (today, yesterday, place, a, b, shown) out of SurpriseShowingTests into a
  new non-emptied Tests/ScenicKitTests/Surprise/SurpriseShownFixture.swift, NOT widen session TEST_FILES - the two
  dependents (SurpriseCardHistoryTests, SurpriseShownDayTests) are shownhistory's population, FILTER names neither,
  and emptying them in session's arm would couple two populations. Values are byte-identical; no MUTATIONS entry
  changes (all anchors are in Sources/).
  (4) MEASURED by grep before the run: the only test files that name a symbol defined only in an emptied file are
  SurpriseCardHistoryTests.swift (SurpriseShowingTests.today/.yesterday/.a/.b/.place/.shown, lines 10-18) and
  SurpriseShownDayTests.swift (SurpriseShowingTests.a/.shown, lines 68/71); of the seven ScenicAPIClientTests
  suite names only SessionAccountTests occurs outside its own file, in PlanBearerTests and SessionSkewTests - all
  three emptied together, so that edge builds.
- 2026-10-08T22:43:02Z MEASURE + RED (acceptance 1 and 3, red arm): at e3f05200 (main's tests, the refusal committed),
  `SESSION_MUTATE_SCRATCH=<repo>/.build/t0331 python ops/mutate/session.py --prove-vacuity` -> exit=2:
  `PROVING NON-VACUITY: the 8 test files replaced by empty suites; every mutation must report MISSED.`
  `VACUITY REFUSED: with the 8 test file(s) emptied the tests do not build - a vacuity arm that cannot build proves
  nothing; no mutation was run`
  `build error: ...\Tests\ScenicKitTests\Surprise\SurpriseShownDayTests.swift:68:17: error: cannot find 'SurpriseShowingTests' in scope`
  `build error: ...\SurpriseShownDayTests.swift:71:36: error: cannot find 'SurpriseShowingTests' in scope`
  `build error: ...\SurpriseCardHistoryTests.swift:10:24: error: cannot find 'SurpriseShowingTests' in scope`
  `build error: ...\SurpriseCardHistoryTests.swift:11:28 / 13:20 / 14:20: error: cannot find 'SurpriseShowingTests' in scope`
  (the 12-line quote cap reached; lines 15, 16, 18 of SurpriseCardHistoryTests are the same reference). Exactly the
  two files ruling (4) named. The quote also carried swiftc's caret lines (`|  `- error:`); build_report now keeps
  only `<file>:<line>:<col>: error:` lines.
- 2026-10-09T00:54:50Z GREEN at a022b7d9 (acceptance 2 and 3, green arm; runs finished 2026-10-08T23:35Z-23:38Z,
  quoted from the saved stdout after a session restart):
  `python ops/mutate/session.py --prove-vacuity` -> exit=0:
  `PROVING NON-VACUITY: the 8 test files replaced by empty suites; every mutation must report MISSED.`
  `BASELINE    --filter AttestClientTests|...|SessionSkewTests exit=0` (the emptied set BUILDS now - the refusal did not fire)
  `caught by the test that names it: 0 of 81   (wrong killer 0, trapped 0, compile-only 0, MISSED 81, skipped 0)`
  `VACUITY PROOF OK: with the 8 test file(s) emptied, caught=0 (need 0) and MISSED=81 of 81`
  `python ops/mutate/session.py --only 35,36,39` (the three SurpriseShowing entries, the file whose fixture moved) -> exit=0:
  `population  mutations=81 (floor 81)  equivalent=3 (floor 3) ... test files=8`
  `caught by the test that names it: 3 of 3   (wrong killer 0, trapped 0, compile-only 0, MISSED 0, skipped 0)`
  `MUTATE OK  caught=3/3 equivalent_caught=0  (--only: 3 of 81 entries)`
  The three suites that share the fixture, `swift test --filter SurpriseShowingTests|SurpriseCardHistoryTests|SurpriseShownDayTests`:
  `Test run with 8 tests in 3 suites passed` exit=0. No MUTATIONS/EQUIVALENT entry changed:
  `git diff 53aa41fa -- ops/mutate/session_mutations.py` is empty (floors 81/3 unchanged). The full non-vacuity run is
  replaced by --only over the entries whose test file moved, per the owner-approved faster-verification rule; every
  anchor is in Sources/, which this branch does not touch.
- 2026-10-09T02:00:32Z ACCEPTANCE RE-RUN on the merged head b3882536 (origin/main 309de74c merged; main's diff
  touches no session subject, no session test file and no Surprise test), tree clean after the runs:
  (1) red: quoted at 2026-10-08T22:43:02Z above - `VACUITY REFUSED`, exit 2, the two dependents named.
  (2) `python ops/mutate/session.py --prove-vacuity` -> exit=0:
  `PROVING NON-VACUITY: the 8 test files replaced by empty suites; every mutation must report MISSED.`
  `caught by the test that names it: 0 of 81   (wrong killer 0, trapped 0, compile-only 0, MISSED 81, skipped 0)`
  `VACUITY PROOF OK: with the 8 test file(s) emptied, caught=0 (need 0) and MISSED=81 of 81`
  `python ops/mutate/session.py --only 35,36,39` -> exit=0:
  `caught by the test that names it: 3 of 3   (wrong killer 0, trapped 0, compile-only 0, MISSED 0, skipped 0)`
  `MUTATE OK  caught=3/3 equivalent_caught=0  (--only: 3 of 81 entries)`
  `swift test --filter SurpriseShowingTests|SurpriseCardHistoryTests|SurpriseShownDayTests`:
  `Test run with 8 tests in 3 suites passed` exit=0.
  (3) the refusal: red above (exit 2 on the broken emptied set), green here (the emptied set builds, BASELINE exit=0).
  Gates: `python ops/lib/check-mutate-population.py` -> `P-PROC-06: 301 modules, 167 covered by 37 populations,
  113 allowlisted, 0 added by this branch` exit 0; `bash ops/lib/check-exec-bits` -> `P-OPS-01: 191 files, 23
  required present, all modes correct` exit 0; `bash ops/queue-check` -> `QUEUE OK (324 tasks)` exit 0.
  STILL OPEN: the other Swift populations' drivers (accounttoken, autopsy, corpusfetch, drive, ledger, ...) still
  return 2 on a failed emptied build without naming it as a vacuity refusal - safe (never counted as MISSED) but
  silent; outside this task's touches.
- 2026-10-09T02:16:22Z main moved (PR #215 T-0332, ScenicAPIClient plan-failure files and tests; no session subject,
  no session test file); merged again at 9cd792eb and re-ran the touched rows only: the eight suite names occur in
  Tests/ only in their own (emptied) files and in SurpriseShownFixture.swift's doc comment;
  `session.py --only 35,36,39 --prove-vacuity` -> `VACUITY PROOF OK: with the 8 test file(s) emptied, caught=0
  (need 0) and MISSED=3 of 3` exit=0 (the emptied set builds on this head); `session.py --only 35,36,39` ->
  `MUTATE OK  caught=3/3 equivalent_caught=0` exit=0; check-mutate-population exit 0 (302 modules, 0 added by
  this branch), check-exec-bits exit 0, tree clean after the runs.
