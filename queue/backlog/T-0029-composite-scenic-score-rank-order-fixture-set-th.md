---
id: T-0029
title: Composite scenic score + rank-order fixture set (the anti-mush check)
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/, pins/PINS.yaml]
pins_affected: []
reviewer: null
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
