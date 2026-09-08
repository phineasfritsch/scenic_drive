---
id: T-0070
title: queue-check cannot see a duplicate task, only a duplicate id, and reports OK on an empty queue
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/queue.py]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

**Two task files can carry different ids and the same brief, and nothing anywhere notices.** Found by
reading, then confirmed byte-for-byte:

    diff <(sed 's/^id: T-006[67]$/id: X/' queue/backlog/T-0066-*.md) \
         <(sed 's/^id: T-006[67]$/id: X/' queue/backlog/T-0067-*.md)
    -> IDENTICAL apart from the id line

`ops/new-task` was invoked twice for one finding during the self-referential-check sweep and allocated
T-0066 and T-0067 for the same work. `ops/queue-check` passed on that tree, because its only uniqueness
assertion is on the id:

    if tid in seen:
        problems.append(f"duplicate id {tid}: ...")

The id is exactly the field `new-task` guarantees is unique, so the check can never fire on anything
`new-task` produces. It is a gate on the one thing that cannot go wrong.

**The cost is not cosmetic.** Two ids for one defect means two agents claim, two worktrees, two branches
touching the same paths, and the collision surfaces at merge as a conflict rather than at claim as a
refusal. That is the merge-time defect class `ops/merge-rehearse` exists to find, filed into the queue by
the queue's own tooling.

**Second, unrelated hole in the same function.** The success line is

    print(f"QUEUE OK ({len(seen)} tasks)")

and `seen` is populated by iterating `tasks()`. An empty or unreadable `queue/` prints `QUEUE OK (0 tasks)`
and exits 0 - the same shape already fixed in `ops/lib/check-exec-bits` (MIN_FILES + REQUIRED) and
`ops/lib/check-line-cap` (MIN_CAPPED), and filed against `ops/check-pins` as [[T-0066]]. Demonstrate it
before fixing it: point the queue root at an empty directory and show the exit code.

- Refuse two tasks whose titles are equal after normalisation, and two whose briefs are equal ignoring the
  `id:` line. Report both paths, the way the duplicate-id arm does.
- Put a floor under the task count so an empty queue is red, not `QUEUE OK (0 tasks)`.
- `ops/new-task` should refuse at creation time, not only at check time - a duplicate that is never
  committed costs nothing, and one that is claimed costs two worktrees.
- Dead code in the same function, found while reading, worth removing in the same pass:

        if state == "done":
            for dep in fm.get("depends_on") or []:
                pass  # done tasks may reference anything

  It iterates to do nothing. Delete it or make it assert something.
- Demonstrate each case red then green in this log.

## Log
- 2026-09-08 filed by agent/claude-opus-5 after `ops/new-task` filed the same finding twice as T-0066 and
  T-0067 and `ops/queue-check` stayed green. T-0067 was deleted; T-0066 keeps the finding.
