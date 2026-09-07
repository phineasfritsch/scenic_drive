---
id: T-0063
title: ops/review must handle main's stale claimed copy, or every branch duplicates on merge
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/queue.py, queue/README.md]
pins_affected: []
reviewer: null
depends_on: [T-0032]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

**All thirty open branches duplicate their own task file on merge, and not one of them can see it.**

`main` says `queue/claimed/<id>`, the branch says `queue/review/<id>` or `queue/done/<id>`, and on merge BOTH
survive:

    QUEUE CHECK FAIL
     - duplicate id T-0039: queue/claimed/T-0039-...md and queue/ready/T-0039-...md

`ops/queue-check` passes on the branch. It passes on main. Only the merged result fails - so no per-branch CI
could ever have caught it, and it cascades: once one duplicate exists every later merge reports the same one,
which masks the rest.

**The cause is structural, not carelessness.** `ops/claim` moves `ready/ -> claimed/` on MAIN. Worktrees here
are created from OTHER task branches in order to stack them, and those bases predate the claim - so the branch
never contains `claimed/<id>` and has nothing to delete. Writing the review copy on the branch cannot remove a
file the branch does not have. Add-then-remove in one commit does not help either: git compares trees against
the merge base, and the base never had the file.

The manual fix, verified on `task/T-0052` and then applied across the idle branches: `git merge origin/main`
to bring `claimed/<id>` in, then `git rm` it, so the deletion is recorded against a base that has the file.

**Make it impossible to forget.** T-0032 added `queue.py review <id> --reviewer <name>` (wrapped as
`ops/review`) precisely so the claimed -> review transition has one home instead of being a habit. This
belongs there:

- `ops/review` should refuse, or fix, the case where the task also exists in another queue directory
  reachable from `origin/main`. Decide which - refusing is safer and teaches the rule; fixing silently is
  friendlier and risks hiding a genuine duplicate somebody created another way.
- Whatever it does, `ops/review` must leave the branch in a state where MERGING it does not produce a
  duplicate. That is the actual acceptance test, and it cannot be checked by running `queue-check` on the
  branch - it needs a rehearsal merge against main.
- The same applies to the review -> done transition a reviewer performs. There is no `ops/done` yet.
- Document the rule in `queue/README.md` next to the claim protocol, because until `ops/review` is merged
  every agent is doing this by hand.

**Demonstrate red properly.** On the branch, `queue-check` passes. Merge the branch into a throwaway copy of
main and show `queue-check` failing there; then run the fixed transition and show the same merge clean. A
demonstration that only runs `queue-check` on the branch proves nothing about this bug, which is the whole
point of it.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from a full merge rehearsal: thirty branches merged into a throwaway
  in dependency order with the gates run after each. The same rehearsal found an ADD/ADD conflict on
  ops/lib/gh-stub-for-merge-tests across T-0022/T-0044/T-0049, the exec-bits trap T-0041 predicted, and a
  436-line test file (T-0062) that no single branch could see.
