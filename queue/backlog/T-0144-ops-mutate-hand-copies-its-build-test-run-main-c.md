---
id: T-0144
title: ops/mutate hand-copies its build/test/run/main core across six harnesses; extract one module
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/mutate/, ops/lib/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Panel CODE lens, grounded: six harnesses under ops/mutate/ (budget, gates, hazards, retrace, guidance, route
score - 3,123 lines) each carry their own copy of the baseline build, the HEAD-drift refusal, the vacuity /
floor / dirty / blind proofs, the sentinel and the summary line. Fixes to one (the MIN_* equality, the
None-survivor hole R7-01 found in mutate-T0028.py) reach the others by hand or not at all - guidance.py and
route score are already missing the HEAD-drift refusal the others have.

Do: one `ops/lib/mutate_core.py` (build, run-one-mutation, proofs, floors as EQUALITIES, HEAD-drift, sentinel,
report) that each harness imports with its own MUTATIONS/EQUIVALENT/TEST_FILES/anchors. Every existing
acceptance line of every harness must still print the same numbers after the extraction; the diff of each
harness's output before/after is the acceptance. 300-line cap per file. Serial with any open PR that touches
ops/mutate/ (#71 at least) - do not start until it merges.

## Log
- 2026-09-18T03:05:00Z filed by agent/claude-fable-5-1 from the hourly panel's grounded synthesis (.artifacts/panel/last.md). ops/new-task allocated T-9902 again ([[T-0138]]); renamed by hand.
