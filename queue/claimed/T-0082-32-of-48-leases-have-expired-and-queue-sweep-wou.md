---
id: T-0082
title: 32 of 48 leases have expired and queue-sweep would clobber every one of them
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T03:28:24Z
lease_expires_at: 2026-09-08T09:28:24Z
worktree: wt/T-0082
branch: task/T-0082
exclusive: []
touches: [ops/lib/queue.py]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

**32 of the 48 tasks in `queue/claimed/` have an expired lease. None of them is abandoned.** Every one is
finished work sitting on a branch, waiting for a merge that has not been possible since 2026-09-07.

`cmd_sweep` is designed for the opposite situation - an agent that died mid-task - and does the right thing
for it: move the task back to `ready/`, clear the lease, release the locks. Run today it would do that to all
32, and each one is a compounding mistake:

1. **It sets `owner: None`.** That is precisely the state [[T-0068]] was filed to reject, and `cmd_sweep` is
   named in that brief as the tooling that produces it. A task later moved to `review/` by hand then reaches
   `done/` with no owner and, until T-0073's fix merges, no complaint.
2. **It multiplies the task-file divergence.** `main` would say `ready/<id>`; the branch says `review/` or
   `done/`. That is the add/add across two paths this session has repaired on eleven branches by hand, and it
   would be recreated on 32.
3. **It discards a signoff.** Several of these have been reviewed. Sweeping loses the reviewer along with the
   owner, and the task looks unclaimed to the next agent that runs `ops/queue-next`.

**The model is wrong, not the implementation.** A lease answers "is an agent still working on this?" The
queue is using `claimed/` to answer a different question - "has this merged yet?" - and those have completely
different timescales. An agent works for hours; a branch waits for days.

- Distinguish the two. A task whose branch is pushed and whose PR is open is not a lease candidate, whatever
  its timestamp says. `ops/claim` already records `branch:`, and `gh pr list` can say whether it is open.
- Or split the state: `claimed/` for work in progress, and something like `merging/` for work that is finished
  and waiting. The directory is the state, so this is a `git mv` and a name.
- **Whatever is chosen, `cmd_sweep` must refuse to clear an owner on a task whose branch exists on the
  remote.** That single rule makes the current 32 safe without deciding the larger question.
- [[T-0032]] releases exclusive locks on the claim -> review transition, which fixes the LOCK half. It is
  written and unmerged. This task is the OWNER half, and the two together are the whole problem.

**Demonstrate red before fixing:** run `ops/queue-sweep` against a copy of the current tree (never the real
one) and count how many task files it rewrites and how many owners it clears. That number is the finding.
[[T-0064]] is already blocked behind this: it cannot claim `scenic-index` because T-0024 holds the lock for a
task whose work is complete.

## Log
- 2026-09-08 filed by agent/claude-opus-5 after declining to sweep. The 32 figure was measured by parsing
  `lease_expires_at` from every file in `queue/claimed/`.
- 2026-09-08T03:28:24Z claimed by agent/claude-opus-5; lease until 2026-09-08T09:28:24Z
