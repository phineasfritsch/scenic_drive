---
id: T-0075
title: nothing checks the tree GitHub Actions actually tests, which for a stacked PR is not main
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T02:14:05Z
lease_expires_at: 2026-09-08T08:14:05Z
worktree: wt/T-0075
branch: task/T-0075
exclusive: []
touches: [ops/pr-ci-preflight]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

**A `pull_request` run checks out `refs/pull/<n>/merge` — the PR's head merged into ITS BASE.** For a stacked
PR the base is another task branch, not `main`. Nothing in `ops/` looks at that tree, so a branch can be clean
against `main`, clean on its own, and still fail its own CI.

Measured. PR #32 is `task/T-0026 <- task/T-0025`:

    bash ops/queue-check on task/T-0026 alone          QUEUE OK (60 tasks)   exit 0
    bash ops/queue-check on main + task/T-0026         QUEUE OK (67 tasks)   exit 0
    bash ops/queue-check on refs/pull/32/merge         QUEUE CHECK FAIL      exit 1
      duplicate id T-0051: queue/claimed/... and queue/ready/...
      duplicate id T-0026: queue/done/...   and queue/claimed/...

and the real CI run agreed — `core` failed on `check-pins`, P-PROC-01, whose assertion is
`bash ops/queue-check >/dev/null`. A scratch pass over all 31 open PRs found **three** failing this way that
every other check called clean.

`ops/merge-rehearse` (T-0065) does not cover this and should not: it answers two different questions
(cumulative — do the branches collide with each other; `--pairwise` — does this branch break `main` alone).
Neither is the question CI asks. Hence a separate tool, per the one-type-per-file rule.

- `ops/pr-ci-preflight` — for every open PR, fetch `refs/pull/<n>/merge` and run the gates on it. Report per
  PR. Exit non-zero if any fails.
- **Do not trust GitHub's `mergeable` field.** Four PRs reported `mergeable=CONFLICTING` / `DIRTY` while
  `git merge` and `git merge-tree --write-tree` both produced a clean tree; GitHub's value was stale and only
  refreshed after a new commit on the head. So when the merge ref is missing, verify locally with
  `git merge-tree --write-tree "origin/<base>" "origin/<head>"` and report the difference between what GitHub
  claims and what git computes. A tool that reads a stale field and prints it as fact is the same defect as
  everything else in this queue.
- The gate to run first is `ops/queue-check`, because it is what caught all three, but the others belong too:
  `check-exec-bits`, `check-line-cap`, duplicate pin ids.
- Anchor on `refs/pull/<n>/merge` and the workflow's `on: pull_request` trigger, never on a comment.
- P-OPS-01 requires committed scripts to be 100755: `git update-index --chmod=+x ops/pr-ci-preflight`.
  `core.filemode` is false on this checkout, so git will not notice on its own.
- Red demonstration: the three PRs above, before they were repaired, are reachable from the reflog and from
  the branches' parent commits. If reconstructing them is impractical, construct the state synthetically —
  two task files for one id at two paths across a head and its base — and show the tool red, then green.

**Worth stating in the log rather than only fixing:** this is the third distinct "the thing we check is not
the thing that runs" finding in this repo — after `ops/check-pins` skipping every pin and reporting success,
and `ops/merge-rehearse` reporting a clean rehearsal having merged one branch of thirty-one.

## Log
- 2026-09-08 filed by agent/claude-opus-5 after a scratch pass over all 31 open PRs found three failing on
  the tree CI tests while passing every local check. The scratch script is at
  `.artifacts/check-pr-merges.sh` (gitignored) and is a starting point, not the deliverable.
- 2026-09-08T02:14:05Z claimed by agent/claude-opus-5; lease until 2026-09-08T08:14:05Z
