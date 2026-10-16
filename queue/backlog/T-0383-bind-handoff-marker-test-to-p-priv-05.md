---
id: T-0383
title: Bind T-0366's handoff-marker privacy test (HandoffMarkingMomentsTests.defaultsDomainIsOneInt) to P-PRIV-05 by name
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [pins/PINS.yaml, ops/lib/named-tests.json]
pins_affected: [P-PRIV-05]
reviewer: null
depends_on: [T-0366, T-0377]
verify: [ops/check-pins]
acceptance: []
---
## Brief

T-0366 (PR #271) keeps a handoff marker on the device: one Int under postDrive.handoffOpensLeft, no place, no
time, no route, never sent. Its privacy property is held by ScenicKitTests.HandoffMarkingMomentsTests
defaultsDomainIsOneInt(), which already runs inside P-PRIV-05's swift filter - so deleting it is green today.
T-0366's Log records the binding as NOT DONE.

Bind it by name in P-PRIV-05's named-tests.json entry (widen the swift filter only if the suite is outside it),
re-approve the check-named-table.py digest and count (77 -> 78 unless measured otherwise) in the same diff, and
append one dated T-0383 sentence to why_no_test_catches_it (do not edit earlier dated text). Demonstrate RED with
the test deleted (MISSING by name under the new table; the guard refuses the table edit without re-approval), then
green. PINS.yaml stays strict (check-pins-yaml.py).

## Log
- 2026-10-16 filed by agent/claude-opus-5 from T-0366 stillOpen (P-PRIV-05 binding not done).
