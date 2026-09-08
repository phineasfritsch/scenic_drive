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

- 2026-09-08 agent/claude-opus-5 — **an independent reviewer of PR #52 returned FAIL with four findings. Three
  are code and are fixed here; the fourth is scope and is acknowledged.**

  **HIGH — the remediation this guard printed was destructive.** It printed `git rm <main's path>` without
  ever comparing main's path to the branch's own, and in the shape the docstring is written for they are the
  SAME file. Following the two printed commands verbatim deleted the branch's only copy of its task file,
  work log and all, after which the instructed re-run printed `T-9991 not found`, exit 1. **My control merged
  main and stopped — it never ran the second command I told people to run**, which is exactly why the trap
  survived my own testing. It now prints only

        git merge origin/main        # resolve the add/add on the task file, keeping YOUR copy

  and emits a `git rm` only for a path the branch does not hold, where the merge really would re-add it.
  After the merge the branch CONTAINS main's commit, so `ops/review`'s own `git mv` records a proper rename
  and nothing needs removing.

  **HIGH — it failed OPEN on a stale `origin/main`.** Nothing fetched and nothing warned, so a branch reviewed
  against a week-old ref was allowed and duplicated anyway. It does not fetch now either — a state transition
  that reaches the network is one people stop running, and `_ids_in_refs` shows what that costs — but it names
  the ref and commit its answer is about:

        (checked against refs/heads/main at bfd2b1e; run `git fetch origin` first if that is stale -
         this guard cannot see a claim pushed since)

  **MEDIUM — the query was wrong, and refused branches that were fine.** `git rev-list -1 <ref> -- <path>`
  returns the commit that LAST TOUCHED the path, not the one that created it. So a branch that genuinely
  contained the creating commit was refused the moment main appended a log line to that same file — which
  `ops/queue-sweep`, `ops/lock` and any hand edit do routinely — with a message stating something factually
  false. Now `git log --diff-filter=A --format=%H -1`. Probed:

        branch contains the creating commit; main last touched the file more recently
        -> T-9992 -> queue/review/T-9992-x.md  reviewer=agent/other        (allowed, correctly)

  **And a mistake inside the fix, caught by running the probe rather than trusting the command:** `git
  rev-list` does not accept `--diff-filter` at all. It exits with a usage message, which `_git` reports as
  "cannot answer", which this function turns into a refusal for **every** branch. The first version of this
  fix would have broken `ops/review` completely. `git log` takes the flag; `rev-list` does not.

  Control after all three: the legitimate flow still passes and the merge still yields exactly one copy.

  **MEDIUM, not fixed, acknowledged:** two of the brief's four bullets were not delivered and the PR body did
  not say so. `queue/README.md` is in this task's `touches:` and is untouched, and there is still no
  `ops/done` for the review -> done transition the brief names. Both are real omissions; recording them here
  rather than quietly leaving the brief looking satisfied.

- 2026-09-08 agent/claude-opus-5 — **this change had silently broken `ops/lib/check-lock-lifecycle`, and
  nothing reported it.** Found by the T-0087 fix agent, which noticed the check was already red while working
  nearby. Two of its three failures were mine and are fixed here.

        task/T-0032   LOCK LIFECYCLE OK     exit 0     <- where the check was written
        task/T-0063   LOCK LIFECYCLE FAIL   exit 1
        task/T-0087   LOCK LIFECYCLE FAIL   exit 1

  **The cause: three different facts collapsed into one.** `check-lock-lifecycle` copies `queue.py` into a
  `mktemp -d` and runs it there, so `ROOT` is not a git worktree at all. My guard treated that the same as
  "git cannot answer" and refused, which meant `ops/review` never reached the lock release:

        FAIL: review did not release the lock
        FAIL: review refused a task that holds no locks

  They are not the same fact and only one is a hazard:

        ROOT is not a git worktree          -> there will never be a merge. Nothing to protect.   ALLOW
        ROOT is a worktree, no main ref     -> no copy on main to duplicate against.              ALLOW
        ROOT is a worktree, git cannot read -> the answer is unknown.                             REFUSE

  The third is real on this checkout: from WSL a Windows worktree's `.git` names a path WSL's git cannot
  follow, so git fails on a tree that genuinely has a main. Keeping that refusal is the point of the guard;
  collapsing the first case into it was the defect. Both FAIL lines are gone, and the probe confirms the guard
  still refuses the branch it exists for.

  **The third failure is NOT mine and is a cross-task collision worth its own task.** `queue-check` now
  reports `only 1 task(s) visible, floor is 40` inside the fixture — [[T-0073]]'s `MIN_TASKS` floor, added in
  round two, against a throwaway tree with one task. `check-lock-lifecycle` came from [[T-0032]] and predates
  that floor, so it passes on `task/T-0032` and fails on every branch carrying both. Neither task is wrong on
  its own; together they are. Filed separately — `ops/lib/check-lock-lifecycle` is not in this task's
  `touches:` and reaching outside it to make a red check green would be the exact move this repo forbids.

  **And a gap in my own tooling, which this exposes:** `ops/merge-rehearse` (T-0065) runs `queue-check`,
  `check-exec-bits`, `check-line-cap` and a pin-id scan after each merge — it does **not** run
  `check-lock-lifecycle` or `check-brief-required`, so a collision of exactly this shape is invisible to the
  rehearsal that exists to find collisions. Recorded against T-0065.
