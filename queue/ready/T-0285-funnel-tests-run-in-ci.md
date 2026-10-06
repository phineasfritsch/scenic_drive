---
id: T-0285
title: the ops/funnel tests and mutation population run on every PR - a pin row (anchor source, runs_on linux) that runs ops/lib/funnel_test.py and ops/lib/funnel_mutate.py, seen red
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [pins/PINS.yaml, ops/lib/funnel_test.py]
pins_affected: [P-PRIV-05]
reviewer: null
depends_on: [T-0284]
verify: [ops/test, ops/check-pins]
acceptance:
  - "pins/PINS.yaml gains a row (id ruled, e.g. P-OPS-07 'ops/funnel's printed output and refusals are pinned') whose assertion runs funnel_test.py and funnel_mutate.py and fails on any failure, missing test or a population below its floor; it runs in CI's pins-source-only job (anchor source - no swift/node needed); seen RED by a one-line mutant of ops/lib/funnel_math.py and by a deleted test, quoted in the Log, then green"
  - "the two non-blocking gaps from T-0284's mutant pass get rows: a missing --fixture path exits 2 (not 4), and a FORMAT JSON body carrying 'statistics' is accepted - each RED by its mutant first"
---
## Brief

T-0284 stillOpen 1: nothing in ops/test, ops/check-pins or CI runs the funnel tests or its population. Also its
fable pass's X1/X2 (exit 2 for an unreadable fixture; the optional 'statistics' key never exercised).

## Log
- 2026-10-06T17:06:00Z filed by agent/claude-opus-5 (orchestrator) after PR #173 (T-0284) review PASS.
