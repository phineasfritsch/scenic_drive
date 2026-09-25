---
id: T-0238
title: check-drive-copy runs in CI (a pin names it), sees a HandoffDrive case inside a string interpolation, and CI runs --prove-red for it and for check-map-attribution
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/check-drive-copy, ops/lib/check-map-attribution, pins/PINS.yaml, .github/workflows/linux-core.yml]
pins_affected: []
reviewer: null
depends_on: [T-0236]
verify: [ops/check-pins]
acceptance:
  - "a pin in pins/PINS.yaml names ops/lib/check-drive-copy (runs_on: linux) and ops/check-pins --source-only runs it; shown RED on a branch commit that hard-codes a HandoffDrive case outside the typed site list, then green"
  - "the gate strips only the literal text of a string, never an interpolation's contents: a hard-coded case inside a string interpolation in DriveCopy (rv1-t0236's M3d, which exits 0 on main) is RED, as a new --prove-red row"
  - "CI runs 'check-drive-copy --prove-red' and 'check-map-attribution --prove-red' on every push; rv1-t0236's M3a (the typed site list widened in the same edit that hard-codes a case) is caught by a prove-red row that CI now runs - shown red then green in the Log"
---
## Brief

From agent/rv1-t0236's FAIL on PR #130 (recordable R1-R3, 2026-09-25): 'check-drive-copy is not referenced by
pins/PINS.yaml or .github/workflows, so CI never runs it'; 'the gate strips string literals, interpolations
included ... a hard-coded case in an interpolation fails OPEN'; 'only prove-red's THIRD case row stands in the way,
and nothing in CI runs prove-red'. A check CI never runs is a check that has never been seen red in CI.

## Log
- 2026-09-25T23:35:28Z filed by agent/claude-opus-5 (orchestrator) from rv1-t0236's recordables. After #130 merges.
