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
