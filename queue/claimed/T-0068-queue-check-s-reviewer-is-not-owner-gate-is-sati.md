---
id: T-0068
title: queue-check's reviewer-is-not-owner gate is satisfied by owner: null
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T01:19:37Z
lease_expires_at: 2026-09-08T05:19:37Z
worktree: wt/T-0068
branch: task/T-0068
exclusive: []
touches: [ops/lib/queue.py]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

CLAUDE.md's rule is *"the reviewer of a task is never its owner (`ops/queue-check`)"*, and P-PROC-01 states
it. The assertion beneath it is:

    elif fm.get("reviewer") == fm.get("owner"):

Both operands are fields the same agent writes into the same file, and **nothing asserts that a task in
`review/` or `done/` has an owner at all**, so the inequality is satisfied vacuously by a null.

Demonstrated, every case executed:

    control:    owner: agent/self + reviewer: agent/self in queue/done/
                -> QUEUE CHECK FAIL - reviewer == owner (agent/self)   exit 1
    evasion 1:  change one word to `owner: null`, leave reviewer: agent/self
                -> QUEUE OK (1 tasks)                                   exit 0
    evasion 2:  delete the `owner:` line entirely
                -> QUEUE OK (1 tasks)                                   exit 0

In both evasions P-PROC-01 is green while the worker graded its own work.

**This is not an exotic hand edit.** `cmd_sweep` writes `owner=None` itself when a lease expires, so a null
owner is a state the tooling produces. A task swept back to ready, re-claimed, and later moved to review by
hand can reach `done/` with no owner and no complaint.

- A task in `review/` or `done/` must HAVE an owner and a reviewer, and they must differ. Two of those three
  conditions are currently unenforced.
- Check the same shape on the other side: does anything assert the reviewer is not null? The existing code
  has `if not fm.get("reviewer")` - confirm that arm is reachable and demonstrated.
- `ops/review` (added by T-0032) refuses `reviewer == owner` at the transition. Give it the same null
  treatment, or the refusal is evadable the same way.
- Demonstrate all three states red then green.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from the self-referential-check sweep.
- 2026-09-08T01:19:37Z claimed by agent/claude-opus-5; lease until 2026-09-08T05:19:37Z
