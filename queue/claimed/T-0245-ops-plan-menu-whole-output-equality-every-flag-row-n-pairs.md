---
id: T-0245
title: ops/plan --menu - the full-equality oracle covers the WHOLE printed output under every flag the acceptance uses (none, --max 20, 15, 10), and ROW n is paired with URL n
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-26T20:43:47Z
lease_expires_at: 2026-09-27T04:43:47Z
worktree: .worktrees/T-0245
branch: task/T-0245
exclusive: []
touches: [Tests/ScenicPlanCLITests/, ops/mutate/menu_mutations.py]
pins_affected: []
reviewer: null
depends_on: [T-0239]
verify: [ops/test, ops/check-pins]
acceptance:
  - "one test through MenuCommand.run per invocation (no flag, --max 20, --max 15, --max 10) on both recorded trips (Tests/Fixtures/t0239/topanga-malibu, zuma-agoura) asserts the ENTIRE printed output equals a recomputation in the test from the recorded rows through the committed builders - every ROW line, every URL line, and that ROW n's index equals URL n's index; rv4-t0239's two survivors (X2: decision points from row 0 only when --max is below the cap; X1: ROW lines numbered index + 1) are RED by name, then green, and join ops/mutate/menu_mutations.py by name"
---
## Brief

From agent/rv4-t0239's FAIL on PR #132 (2026-09-26): round 4's equality oracle ran only the no-flag invocation, and
nothing tied a ROW line's number to its URL line's number. PR #132 merged after four rounds with this gap recorded
(CLAUDE.md rounds rule; the finding is not a P-SAFE pin - the ceiling tests caught every ceiling mutant). The lesson:
equality over the whole output, under every flag the acceptance names, from the start.

## Log
- 2026-09-26T18:19:17Z filed by agent/claude-opus-5 (orchestrator) from rv4-t0239's B1-B2.
- 2026-09-26T20:43:24Z PROMOTED to ready/ by agent/claude-opus-5 (orchestrator): T-0239 merged (PR #132, 94b5d06).
- 2026-09-26T20:43:47Z claimed by agent/claude-opus-5; lease until 2026-09-27T04:43:47Z
