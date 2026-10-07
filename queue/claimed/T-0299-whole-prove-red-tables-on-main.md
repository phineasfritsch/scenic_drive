---
id: T-0299
title: Run both P-SAFE-03 / P-ATTR-01 prove-red tables whole on main and quote the N/N lines and both bare-guard times
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-07T19:11:23Z
lease_expires_at: 2026-10-08T01:11:23Z
worktree: .worktrees/T-0299
branch: task/T-0299
exclusive: []
touches: [queue/]
pins_affected: [P-SAFE-03, P-ATTR-01]
reviewer: null
depends_on: [T-0295]
verify: [ops/check-pins]
acceptance:
  - "On main after T-0295, with the box otherwise idle: 'bash ops/lib/check-safety-disclaimer --prove-red' prints 'prove-red: 52/52 mutations refused by name' (or the table's current row count) and 'bash ops/lib/check-map-attribution --prove-red' prints 'prove-red: 46/46 ...'; both bare guards exit 0 with wall times quoted; every line quoted in the task Log"
  - "Any row not refused by name is a finding filed as its own task (no code change in this task)"
---
## Brief

rv2-t0295 recordable (PR #184): neither table has one whole-table summary line since T-0295 - the safety table's rows 1-49
ran whole and died at row 50 when the table was rewritten mid-run; rows 50-52 and the map table's 46th row ran one-row.
A measurement task, no code.

## Log
- 2026-10-07T13:52:22Z filed by agent/claude-opus-5 (orchestrator) from rv2-t0295's recordable.
- 2026-10-07T19:11:23Z claimed by agent/claude-opus-5; lease until 2026-10-08T01:11:23Z
