---
id: T-0225
title: etl tests - the motor_vehicle limb of the access rule anchored on Gates.swift by identifier: test_assemble.py pins closedAccess only; PR #82's `mv != 'yes'` is the mutant, red first
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/tests/]
pins_affected: [P-PROD-01]
reviewer: null
depends_on: [T-0217]
verify: [ops/test, ops/check-pins]
acceptance:
  - "test_assemble.py gains a _swift_set-style anchor over the motor_vehicle line of Sources/ScenicKit/Gates (the identifier and the refused value, `tags['motor_vehicle'] == 'no'`) compared to accessrule.MOTOR_VEHICLE_KEY / MOTOR_VEHICLE_REFUSED; RED first with the Swift line mutated on a copy to `!= 'yes'` (GatesInvariantTests.swift:86-95's PR #82 defect), then green; the docstring at test_assemble.py:277 stops being the only mention"
  - "the ETL suite count line, check-line-cap, queue-check bare"
---
## Brief

From the 11:13 panel (CODE, fable-grounded): #122's accessrule.access_refused IS Gates.verdict's two rules, and
assemble re-exports CLOSED_ACCESS by identity so the parity pin at test_assemble.py:247 keeps binding - but that pin
covers only the set literal; the motor_vehicle limb is pinned on the Python side (test_extractadapter.py:143-146)
and nowhere against Swift. rv1-pr122 signed off before this was raised, so it is a task, not a round.

## Log
- 2026-09-19T20:26:45Z filed by agent/claude-fable-5-1 (11:13 panel, fable-grounded on T-0112:72-73, T-0209 Log 15:26:14Z, CLAUDE.md 74615e0). Not started; cheap; after the LA chain.
