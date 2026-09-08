---
id: T-0095
title: the review to done transition has no ops/done, so it carries the stale-copy defect ops/review closed
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/queue.py, ops/done, queue/README.md]
pins_affected: []
reviewer: null
depends_on: [T-0063]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

**[[T-0063]] built `ops/review` to make the `claimed/ -> review/` transition safe, and left the
`review/ -> done/` transition a hand `git mv` with the same exposure.** Found by the reviewer of PR #52 as
one half of a [medium]; the other half (`queue/README.md`) is delivered on `task/T-0063`, this is not.

    $ grep -n "def cmd_" ops/lib/queue.py
    cmd_new  cmd_check  cmd_sweep  cmd_next  cmd_claim  cmd_review  cmd_lock
    (no cmd_done)

**The defect `ops/review` closes applies unchanged one step later.** If a branch was cut before the commit
that put the task file in `main`'s `queue/review/`, that branch has no deletion to record there. A hand
`git mv` to `done/` produces `queue/done/<id>` on the branch while `main` still holds `queue/review/<id>`,
and **the merge keeps both**. `ops/queue-check` then fails on the merged tree while passing on the branch
and on `main` — invisible to per-branch CI by construction, which is the same shape eleven branches were
repaired by hand for.

This is not hypothetical at the current fleet size: 13 tasks are in `done/` and 41 branches are waiting to
merge, so the `review/ -> done/` transition is about to run dozens of times against a `main` that moves
under it.

**It is also the transition with the reviewer-is-not-owner rule attached.** `done/` is the state
`ops/merge` requires on the PR head. A hand `git mv` writes `state: done` without ever passing through a
check that the mover is not the owner, so the one mechanical defence against self-review is bypassed by
the shortest path — see [[T-0094]], which measures ten open PRs whose head never left `claimed/`.

Do:

1. `ops/done <id> --reviewer <who> [--verdict pass|fail]`, mirroring `ops/review`:
   - refuse when the task is not in `review/` on this branch;
   - refuse when `--reviewer` equals `owner:` — the rule, enforced at the moment it matters rather than
     after the fact;
   - refuse when `main` holds a copy this branch cannot delete, and print the **non-destructive** repair
     (`git merge origin/main`, then re-run) — never `git rm` a path this branch also holds, which was
     T-0063's first [high];
   - record the move as a rename (`git mv`), never a delete-plus-add;
   - `--verdict fail` sends it back to `claimed/` with a `## Log` line, which is what `queue/README.md`
     step 6 already asks a reviewer to do by hand.
2. Use the same commit-that-CREATED-the-path query `ops/review` was corrected to use —
   `git log --diff-filter=A --format=%H -1 <ref> -- <path>`, not `git rev-list -1`, which returns the commit
   that last *touched* the path and refuses legitimate branches whenever `main` appends one log line.
3. Document it in `queue/README.md` step 6 next to `ops/review`, replacing the sentence added on
   `task/T-0063` that currently says this transition is still done by hand.
4. Red demo: a branch cut before `main`'s `review/` copy exists → refusal, and the merged tree shown to
   carry both copies without it. Green: after `git merge origin/main`, the same command records a rename
   and the merged tree has one copy. Also demonstrate the reviewer-equals-owner refusal red.

**Ordering.** Stacks on T-0063 (unmerged). Do not start before it merges, or `ops/review` will be rewritten
underneath this.

## Log
