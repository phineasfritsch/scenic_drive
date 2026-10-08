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
