---
id: T-0115
title: seven PRs merged with a zero-file diff, and ops/merge cannot tell
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/merge]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "ops/merge refuses a PR whose base...head diff is empty, unless an explicit reason is given"
  - "ops/merge prints the file and line count it is about to merge, and the main-bound count when base != main"
  - "RED: ops/merge --dry-run passes today on the recorded shape of PR #52, a zero-file merge"
---
## Brief

`ops/merge` gate 1 asks whether the PR's task is in `queue/done/` with a reviewer who is not its owner. That
is a question about the TASK FILE. It is not a question about the diff, and on a stacked branch the two come
apart.

**Seven merged PRs had a diff of exactly zero files.** Measured with
`git diff --name-only origin/<base>...origin/<head>` at each PR's base:

    PR    head      base            files in the PR diff
    #52   T-0063    task/T-0082                        0
    #32   T-0026    task/T-0025                        0
    #30   T-0047    task/T-0039                        0
    #27   T-0042    <base>                             0
    #25   T-0044    task/T-0022                        0
    #23   T-0038    task/T-0023                        0
    #20   T-0037    task/T-0035                        0

A zero-file PR is a merge that reviewed nothing, and every gate passes: the task file says `done`, the
reviewer field is not the owner, the checks are green because they were green on the base. Nothing in the
system can tell that apart from a real review, because nothing in the system looks at the diff.

**And the diff a reviewer sees is routinely far smaller than what the branch would bring to `main`.** The
sharpest case is PR #64:

    PR #64 (T-0102), base task/T-0087   the reviewer's diff:   1 file
    task/T-0102 against main            what it would carry:  21 files
                                        including 643 changed lines of ops/lib/queue.py,
                                        .githooks/pre-commit, and two new ops/lib scripts

The reviewer PASSed PR #64 honestly and thoroughly. They were shown one file. Opening `task/T-0102 -> main`
today and merging it on the strength of that PASS would move twenty files into `main` on a review that never
saw them.

Across all 32 stacked PRs the same measurement gives 492 file-diffs that reach `main` without being in the
diff of the PR that carries them.

## What this is NOT, checked rather than assumed

**It is not "the code is unreviewed."** Taking the union of every PR diff ever opened and the union of every
branch's main-bound diff:

    files some PR diff has shown at least once : 278
    files that differ from main across branches: 235
    files NO PR diff has ever shown            :   0

Every file has been in front of a reviewer at least once, under some task. The defect is narrower and
subtler than "unreviewed code": **the sign-off recorded against a merge is not the sign-off for that merge's
contents.** A file reviewed under T-0070 at one commit is riding into `main` under T-0102's approval at a
different commit, and `ops/merge` prints a line that reads as though T-0102's reviewer approved it.

That distinction matters, and the difference between the alarming number and the true one is why the union
was computed at all. A finding that overstates itself gets discounted the next time.

Do:

1. **Gate 1 gains a diff question.** Refuse a PR whose `base...head` diff is empty, with the same
   `--no-task-reason=`-style override for the legitimate case (a branch that is genuinely already contained
   in its base and is being closed for tidiness). An empty diff merging silently is the vacuity defect this
   repository is built around, sitting in the merge tool itself.
2. **Print what is actually being merged.** `ops/merge` currently prints `task`, `checks` and `MERGED`. Add
   the file count and line count of `base...head`, and - when the base is not `main` - the count against
   `main` too, so the gap in PR #64 is visible on the terminal at the moment of merging rather than
   reconstructable a week later.
3. **When base != main, require the reviewer to have seen the main-bound diff.** The cheapest honest form:
   refuse, and say that the branch must be retargeted to `main` and re-reviewed at that diff. See
   [[T-0113]], which is the retargeting half of the same problem.

**RED FIRST.** PR #52 is a merged, closed, zero-file PR and is the fixture: `ops/merge 52 --dry-run` against
its recorded shape must pass today and refuse after. Record both.

**Do not fix this by re-reviewing everything.** 235 files differ from `main` and all of them have been read
by someone. The fix is to make the merge tool state what it is merging and refuse the empty case, not to
restart the review queue.

## Log
