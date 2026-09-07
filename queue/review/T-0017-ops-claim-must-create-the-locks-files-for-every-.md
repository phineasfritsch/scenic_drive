---
id: T-0017
title: ops/claim must create the LOCKS files for every exclusive: resource, and refuse if one is held
state: review
owner: agent/claude-opus-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T07:15:18Z
lease_expires_at: 2026-09-07T10:15:18Z
worktree: ../wt/T-0017
branch: task/T-0017
exclusive: []
touches: [ops/lib/queue.py, ops/lock, queue/]
pins_affected: []
reviewer: agent/reviewer-6
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
- 2026-09-07T07:15:18Z claimed by agent/claude-opus-5; lease until 2026-09-07T10:15:18Z
- 2026-09-07T08:20:00Z DEFECT 1 WAS MIS-DIAGNOSED BY ME. I wrote that `ops/claim` accepts a task with `exclusive:` without creating the lock. It does not. Proved empirically: claiming a task declaring [floors, prod] creates both lock files, and a second claim of a task wanting `floors` is refused with exit 1. The brief was wrong.
- 2026-09-07T08:20:00Z THE REAL GAP: `exclusive:` edited AFTER a task is claimed has no lock and no way to acquire one - which is exactly what I did on T-0011. queue-check flags it, but only after the window where a concurrent write could be lost. FIX: new `ops/lock <task> [--owner x]` acquires declared-but-unheld locks for a claimed task, refuses if another task holds one, and appends to the task's ## Log.
- 2026-09-07T08:20:00Z RED/GREEN for ops/lock: edited `exclusive: [floors]` onto a claimed task -> queue-check exit 1 naming the missing lock; `ops/lock T-00xx` -> "acquired [floors]" and queue-check exit 0. A second task declaring the same resource -> `cannot lock floors: held by ...`, exit 1.
- 2026-09-07T08:20:00Z DEFECT 2 IS REAL and now fixed: next_id() scanned only the current worktree. Proof with a genuinely pushed branch (tmp/idprobe, since the fix only helps once a branch is pushed - the case that actually bit us on T-0015): branch A allocated and pushed T-0019; a second branch off origin/main allocated T-0019 with the OLD code (collision) and T-0020 with the NEW code. Probe branches deleted locally and on origin afterwards.
- 2026-09-07T08:20:00Z Residual, stated honestly: two agents allocating offline at the same instant can still pick the same id. The push is the compare-and-swap that settles it, exactly as for claims; documented in the _ids_in_refs docstring. _ids_in_refs is best-effort and offline-safe (fetch and ls-tree failures are swallowed, falling back to whatever refs exist).
- 2026-09-07T08:20:00Z Filed T-0019 for reviewer-5's finding that P-OPS-01 passes vacuously on an empty ops/ - not fixed here because pins/PINS.yaml is outside this task's touches.
- 2026-09-07T08:20:00Z moved to review/, reviewer agent/reviewer-6
