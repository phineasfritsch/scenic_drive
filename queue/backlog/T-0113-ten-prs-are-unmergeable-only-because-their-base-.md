---
id: T-0113
title: ten PRs are unmergeable only because their base branch's PR already merged
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/merge, queue/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "the ten retargeted PRs report mergeable != CONFLICTING"
  - "ops/merge refuses a PR whose base is a task branch without an explicit reason"
  - "RED: ops/merge --dry-run on such a PR passes its base check today"
---
## Brief

**Thirty-one open PRs. Eighteen are based on `main`. Ten are based on a branch whose own PR merged months
of commits ago, and one on a branch that never had a PR at all.** Every one of those eleven reports
`mergeable: CONFLICTING`, and for ten of them the conflict is an illusion.

Measured, per PR - commits and files in the diff against the current base, versus against `main`:

    PR    head      base            c/base  c/main  f/base  f/main
    #26   T-0024    task/T-0038         43      51      51      51
    #33   T-0027    task/T-0026         99      43     132      50
    #38   T-0033    task/T-0025          3      38      52      52
    #35   T-0040    task/T-0023          3       3      28      28
    #43   T-0043    task/T-0037          4       6       8       7
    #29   T-0046    task/T-0038         21      29      28      28
    #41   T-0049    task/T-0044         15      12      12      12
    #37   T-0051    task/T-0047          3       9       7       7
    #34   T-0052    task/T-0026          8      42      54      54
    #40   T-0056    task/T-0039          3       3       7       7
    #56   T-0081    task/T-0069         27      53      26      58

**For nine of them the files-changed set is byte-identical either way.** #33 gets SMALLER against main
(132 -> 50). The base branch's extra commits contribute nothing to the diff, because the shared history
already reached `main` when the base's own PR merged. Retargeting is a metadata edit, not a rebase, and it
turns ten CONFLICTING PRs into reviewable ones:

    gh pr edit 26 33 38 35 43 29 41 37 34 40 --base main     # one at a time; gh takes a single PR

**#56 is the exception and must NOT be retargeted with the rest.** Its base `task/T-0069` never had a PR at
all, and its diff grows 26 -> 58 files against main. That is real unmerged work from somewhere else being
pulled into the PR, not an illusion. It needs its own look.

## The structural cause, which is the part worth fixing

The stack grows the wrong way. `task/T-0023` merged into `main` as PR #14. Then `task/T-0024` merged into
`task/T-0023`, `T-0025` into `T-0024`, `T-0026` into `T-0025`, and so on - **each child merging DOWN into a
parent whose PR had already merged**, building a tower on branches that no longer have a route back to
`main`. `origin/task/T-0023` today is 24 commits ahead of `main` and none of them is reachable from it.

Six more went the same way earlier today. PRs #50, #51, #52, #64, #66 and #67 all merged at 12:23-12:24, and
every one had a base of `task/T-00xx`, not `main`. They are marked MERGED, they moved no work into `main`,
and their green checks now sit on a closed PR where no reviewer will look at them again.

That is also how six PRs got merged without the `ops/merge` review gate: `ops/merge` refused each of them
correctly (`MERGE REFUSED: T-0063 is not in queue/done/ - a reviewer has not signed it off`), and a direct
`gh pr merge` went around it. `ops/merge`'s own header predicted this exactly: *"HONEST LIMITATION: this is
a client-side gate. Nothing stops someone typing `gh pr merge` directly."*

Do:

1. Retarget the ten. Confirm each one's `mergeable` leaves CONFLICTING afterwards; if one does not, say which
   and stop rather than forcing it.
2. **Make the default base `main`.** A task branch should be cut from `main` and target `main` unless its
   task declares `depends_on:`, in which case targeting the dependency is deliberate and should be recorded
   in the task file. Today the base is whatever branch the worktree happened to be created from, which is why
   the tower exists - nobody chose it.
3. **Give `ops/merge` a base check.** It gates on review and on checks; it does not look at where the PR
   points. A PR whose base is another task branch should require the same kind of explicit reason
   `--no-task-reason` already demands, so that merging sideways is a decision someone typed rather than a
   default nobody noticed.
4. Branch protection now requires `core` and `pins-source-only` on `main` (verified via the API), so the
   client-side gate is no longer the only thing standing there. Note in `ops/merge`'s header that its
   "HONEST LIMITATION" paragraph is now partly obsolete - and do not delete the paragraph, because the gate
   it describes is still the only thing checking the QUEUE state.

**RED FIRST.** For step 3 the red run is a PR whose base is a task branch passing `ops/merge --dry-run`
today; it must refuse afterwards. #56 is a live example that can stay unmerged while it is used as one.

## Log
- 2026-09-08T20:50:00Z **THE PREMISE OF THIS TASK IS WRONG AND THE MECHANICAL FIX IT IMPLIES IS UNSAFE.** Checked all 18 open PRs whose base is a task branch, asking of each whether the base is already contained in `main`:

  ```
  for p in 69 68 63 62 56 49 44 43 42 41 40 39 38 37 35 34 33 29; do
    git merge-base --is-ancestor "origin/$base" origin/main && echo safe || echo "base still unmerged"
  done
  ```

  **All 18 report `base still unmerged`. Not one is safe to retarget.**

  The title says these PRs are unmergeable *only* because their base is a task branch rather than `main`. That
  is not the situation. `gh pr edit --base main` does not just relabel a PR - it changes the merge base, so the
  PR's diff grows to include every unmerged commit on the base branch. Retargeting #63 (head `task/T-0100`,
  base `task/T-0080`) would make its diff contain all of T-0080's work, and merging it would land T-0080 on
  `main` **unreviewed**, under a PR whose title and review say nothing about it.

  That is the same failure this repository has already recorded once: [[T-0115]], seven PRs merged with a
  zero-file diff. A blind retarget would produce the mirror image - PRs merged with a diff far larger than
  anyone reviewed.

  So the tower is a **real dependency chain**, not a labelling mistake, and there is no mechanical unblock. The
  only correct path is to land the bases in dependency order, each after its own review. Two concrete chains:

  * `#33`/`#34` (base `task/T-0026`) → `#38` → ... - T-0026 first;
  * `#63` (base `task/T-0080`) - **T-0080's PR #59 is green and MERGEABLE right now**, so this chain is one
    review away from moving. T-0080 sits in `queue/claimed/` with `reviewer: null`, owned by
    `agent/pins-mutation`; it needs to reach `review/` with a reviewer who is not that owner before `ops/merge`
    will take it.

  **Rewrite this task** to be "land the tower in dependency order, starting with T-0026 and T-0080", or close
  it in favour of that. Do not leave it phrased as a retarget, because the retarget is the dangerous action and
  the title currently recommends it.
