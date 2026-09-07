---
id: T-0017
title: ops/claim must create the LOCKS files for every exclusive: resource, and refuse if one is held
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

Two queue-mechanics defects, both observed on 2026-09-07:

1. `ops/claim` accepts a task declaring `exclusive: [x]` without creating `queue/LOCKS/x.lock`. The operator has
   to remember. `ops/queue-check` catches it afterwards, but the lock is the thing that prevents a concurrent
   write, so catching it late is catching it wrong. FIX: `claim` creates every declared lock atomically and
   refuses the claim if any is already held; `sweep` releases them (it already does).

2. `next_id()` scans only the CURRENT worktree, so two branches allocate the same id. Observed: T-0015 was
   created on task/T-0007 (exec bits) and again on task/T-0011 (this task) because the first was unmerged.
   `queue-check` would flag the duplicate only after both merged. FIX: allocate ids against `origin/main`
   (`git ls-tree -r --name-only origin/main queue/`) plus the local tree, and fetch first.

RED for 1: claim a task with `exclusive: [floors]` -> LOCKS/floors.lock must exist and a second claim of another
task declaring the same resource must be refused. RED for 2: create a task on two branches from the same base
and show the ids differ.

## Log
