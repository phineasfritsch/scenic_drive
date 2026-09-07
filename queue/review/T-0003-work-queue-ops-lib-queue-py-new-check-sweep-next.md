---
id: T-0003
title: Work queue: ops/lib/queue.py (new/check/sweep/next/claim), protocol README, seed tasks
state: review
owner: agent/claude-opus-5
owner_session: 01RJHHJcZtZChD9eMb275urx
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/queue.py, ops/new-task, ops/queue-check, ops/queue-sweep, ops/queue-next, ops/claim, queue/]
pins_affected: []
reviewer: null
depends_on: [T-0001]
verify: [ops/test, ops/check-pins, ops/queue-check]
acceptance:
  - "bash ops/queue-check on a review/ task with reviewer == owner -> reviewer == owner listed, exit 1"
  - "bash ops/queue-check on a review/ task with no reviewer -> in review/ without a reviewer, exit 1"
  - "bash ops/claim T-0004 --hours 0 then bash ops/queue-sweep -> T-0004 returned to ready/, lock released"
  - "bash ops/queue-next -> (no unblocked ready task) while T-0001 is in review/; -> T-0004 once T-0001 is in done/ (reviewer-1 finding: the original line ignored depends_on)"
---
## Brief

State is the directory; push-to-claim is the compare-and-swap. No PyYAML dependency. Reviewer != owner is
mechanical. Locks are files in queue/LOCKS created in the same commit as the claim.

## Log
- 2026-09-07T03:14:00Z reviewed by agent/reviewer-1: FAIL — acceptance line 4 "bash ops/queue-next -> T-0004" fails: command returns "(no unblocked ready task)" because T-0004 has depends_on [T-0001] which is not in done/; acceptance line cannot be satisfied in current queue state.
- 2026-09-07T03:14:00Z reviewed by agent/reviewer-1: FAIL — acceptance line 4 "bash ops/queue-next -> T-0004" fails: command returns "(no unblocked ready task)" because T-0004 has depends_on [T-0001] which is not in done/; acceptance line cannot be satisfied in current queue state.
