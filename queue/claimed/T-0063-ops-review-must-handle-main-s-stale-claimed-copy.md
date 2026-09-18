---
id: T-0063
title: ops/review must handle main's stale claimed copy, or every branch duplicates on merge
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T03:35:43Z
lease_expires_at: 2026-09-08T09:35:43Z
worktree: wt/T-0063
branch: task/T-0063
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
- 2026-09-08T03:35:43Z claimed by agent/claude-opus-5; lease until 2026-09-08T09:35:43Z

- 2026-09-08 agent/claude-opus-5 — `ops/review` now refuses a branch that would duplicate on merge, and the
  first version of this guard DID NOT FIRE, which is the useful part of this entry.

  **RED**, reproduced in a throwaway git repo shaped exactly like the real failure — `main` claims
  `ready/ -> claimed/`, the branch is cut from a base that predates that claim, the branch writes the file at
  `claimed/` itself. Unpatched `ops/review`:

        T-9991 -> queue/review/T-9991-a-stacked-task.md  reviewer=agent/other      exit 0
        merged tree holds: queue/claimed/... queue/ready/... queue/review/...
        QUEUE CHECK FAIL - 2 tasks share one brief

  Three copies. `queue-check` passes on the branch, passes on main, fails only on the merge.

  **THE FIRST GUARD WAS WRONG AND I PROVED IT RATHER THAN SHIPPING IT.** It asked *"does the branch's working
  tree hold main's path?"* It does — the branch WROTE the file there — so the check found nothing stale and
  allowed the transition, producing the identical three-copy merge. The question was wrong, not the code:
  **the two copies share no history at that path**, so git keeps both regardless of what the working tree
  looks like.

  **The right question is about history**, and the brief said so all along: *"it needs a rehearsal merge
  against main."* A branch can delete a file only by recording a deletion against a base that HAS it, so:

        commit = git rev-list -1 <main> -- <path>
        git merge-base --is-ancestor $commit HEAD

  If the branch does not contain the commit that put the file at that path, it has no deletion to record and
  the merge re-adds main's copy every time. **GREEN:**

        T-9991: main holds this task where this branch cannot delete it:
            queue/claimed/T-9991-a-stacked-task.md
        This branch does not contain the commit that put the file there, so it has no deletion to record.
        ...
            git merge origin/main
            git rm queue/claimed/T-9991-a-stacked-task.md
        exit 1   — nothing moved

  **CONTROL, and it matters as much as the fix**, because a guard that only ever refuses is an outage rather
  than a repair. The branch does what the refusal says, then reviews:

        merged main; branch now holds: queue/claimed/T-9991-a-stacked-task.md
        T-9991 -> queue/review/T-9991-a-stacked-task.md   exit 0
        merged back into main cleanly
        copies of T-9991 in the merged tree: 1            CONTROL PASSES

  **Refused rather than silently repaired**, per the brief's own framing. `git merge origin/main` inside a
  state transition is a history-changing act hidden in a rename, and the same code would swallow a genuine
  duplicate created some other way. The refusal costs one run and teaches the rule once.

  Fails closed, consistently with [[T-0082]]: `_git` returns `ok=False` both for a failed command and for a
  git that cannot run, and `_would_duplicate_on_merge` returns `None` — "could not ask" — which the caller
  refuses on. From WSL against this Windows checkout that is a live state, not a hypothetical.

  `ops/lib/queue.py` is now **788 lines**, from 711. Fourth growth in one session while [[T-0059]] waits,
  blocked because six unmerged branches hold the file. That is no longer a footnote: the file has grown 90%
  past its exemption in a day, and every increment was a real defect that could not wait for a merge that has
  not come.
