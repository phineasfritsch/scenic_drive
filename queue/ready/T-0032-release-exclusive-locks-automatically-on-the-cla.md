---
id: T-0032
title: Release exclusive locks automatically on the claimed/ -> review/ transition
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/queue.py, queue/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`ops/claim` takes a `LOCKS/<resource>.lock` for every resource a task declares in `exclusive:`. Two things
release one: `queue.py sweep`, when the lease expires, and deleting the file by hand. Nothing else.

**There is no supported claimed -> review transition at all.** Every agent in this repo performs it with
`git mv` plus a hand edit of `state:` and `reviewer:`. That is why the lock is never released: there is no
code path at the moment the work stops.

This is currently latent and it is armed. `cmd_check` already treats an orphaned lock as an error -

    LOCKS/<res>.lock held by T-nnnn, which is not in claimed/

- so the moment a task holding `exclusive:` moves to `review/`, `ops/queue-check` starts FAILING for every
agent in every worktree, not just the owner's. Today exactly one lock exists (`scenic-index.lock`, held by
T-0024, still claimed), so nobody has hit it. T-0024 is signed off work away from hitting it.

Fail-closed is the right behaviour for that check and should not change. The gap is that the transition has
no home.

- Add the transition as a command - `queue.py review <id> --reviewer <name>`, wrapped as `ops/review` in the
  style of `ops/claim` - that moves the file, sets `state:` and `reviewer:`, releases every lock the task
  holds, and appends to `## Log`. One operation, so the lock cannot be forgotten independently of the move.
- It must refuse when `reviewer` equals `owner`. `cmd_check` already rejects that after the fact; refusing at
  the transition is the same argument as T-0056's brief check - the last moment it can still be prevented.
- Releasing at review, not at done, is the judgement to argue. For: review takes hours or days, and a task
  sitting in review is not editing the serial resource it locked, so holding `scenic-index` or `prod` that
  long starves everyone. Against: a FAIL sends it back to the owner, who may need the resource again. The
  answer to that is `ops/lock`, which already exists to acquire the locks a claimed task declares - so the
  round trip is supported, and this is not a one-way door.
- Only release locks THIS task holds. A lock whose file names a different task id must be left alone and
  reported, not silently taken over.
- Demonstrate red: with a task holding `exclusive:`, perform the hand `git mv` that everyone does today and
  show `ops/queue-check` failing; then perform the same transition through the new command and show it clean.
  That red run is the whole justification for the command existing, so it belongs in the log verbatim.

## Log
