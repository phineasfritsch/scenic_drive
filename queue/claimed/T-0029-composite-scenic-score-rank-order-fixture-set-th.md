---
id: T-0029
title: Composite scenic score + rank-order fixture set (the anti-mush check)
state: claimed
owner: agent/claude-opus-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T20:17:44Z
lease_expires_at: 2026-09-08T00:17:44Z
worktree: ../wt/T-0029
branch: task/T-0029
exclusive: []
touches: [services/etl/, pins/PINS.yaml]
pins_affected: []
reviewer: agent/reviewer-34
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

score = GATE x M^0.35 x E^0.65 with the gates as POSITIVE EVIDENCE only (see CLAUDE.md).

THE CHECK THAT MATTERS: a hand-picked set of ~30 known-good and ~30 known-dull Bay Area segments whose RANK
ORDER the score must preserve. A unit test on the formula proves arithmetic; only the rank-order set proves the
score means anything. Makes P-PROD-01 real (it is currently pending on T-0012).

RED: swap the geometric mean for a linear sum -> the curvy-industrial vs straight-redwood pair inverts and the
rank-order test fails. That is the exact failure the geometric mean exists to prevent.

## Log
- 2026-09-07T20:17:44Z claimed by agent/claude-opus-5; lease until 2026-09-08T00:17:44Z
