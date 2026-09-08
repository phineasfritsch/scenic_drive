---
id: T-0099
title: every merge-readiness tool enumerates open PRs, so eleven branches of work are invisible
state: claimed
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T07:46:38Z
lease_expires_at: 2026-09-08T10:46:38Z
worktree: null
branch: task/T-0099
exclusive: []
touches: [ops/merge-rehearse, ops/pr-ci-preflight]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

**"37 of 41 merged, 0 gate failures" describes 41 of 52 branches. The other eleven have never been
rehearsed, and nobody noticed because both tools ask GitHub for pull requests instead of asking git for
branches.**

    ops/merge-rehearse:76   mapfile -t EDGES < <(gh pr list --state open --limit 200 ...)
    ops/pr-ci-preflight     same source, by construction - it gates PR CI

Measured on 2026-09-08: 62 `origin/task/*` refs exist, 41 have an open PR, and **eleven carry commits ahead
of `main` with no PR at all**:

    task/T-0069   59 commits      task/T-0086   15 commits      task/T-0078    2 commits
    task/T-0029   55 commits      task/T-0068   11 commits      task/T-0057    1 commit
    task/T-0087   28 commits      task/T-0077    8 commits
    task/T-0085    9 commits      task/T-0066    5 commits
    task/T-0079    5 commits

Ten of the eleven hold a task in `queue/claimed/` on their own head — live, owned work. `task/T-0087` alone
is the `_opts` rewrite that closes [[T-0084]] and two other overclaimed routes; `task/T-0086` is the
environment seal; `task/T-0077` is one of the two branches [[T-0093]] depends on. **None of it has ever been
merged even in rehearsal**, so nothing in this repository knows whether it collides with the 41 that have.

**Why this is the repository's own recurring defect and not an oversight.** The tool measures the set it can
see and reports a number about "the backlog". A reader — including the author, in a status report published
today — takes `37 of 41` as merge readiness. It is merge readiness *of the branches with PRs*. That is the
same shape as a floor that guards a different list than the one it names ([[T-0058]]), a guard whose
expected value comes from the thing it checks, and a suite that reports OK having inspected nothing. The
count was never wrong; the noun it was attached to was.

**`task/T-0057` is a second finding sitting inside the first.** Its task is in `queue/ready/` — unclaimed —
while a branch with a commit exists for it. Work started without a claim, so the compare-and-swap that makes
this queue safe never happened and a second agent could claim T-0057 tomorrow.

Do:

1. Enumerate **branches**, not PRs: `git for-each-ref refs/remotes/origin/task/*` filtered to those ahead of
   `origin/main`. The PR list stays useful for the *ordering* edges (`baseRefName` says what is stacked on
   what) and for CI state, but it must not decide what gets rehearsed.
2. Report the two populations separately, because they mean different things:
   `41 with a PR, 11 without` — a branch with no PR has no CI result at all, so a clean rehearsal of it says
   only that it merges, not that it passes.
3. **Vacuity guard for the enumeration itself:** if the branch set is smaller than the PR set, fail. That is
   the exact condition that would have caught this, and it is cheap.
4. `ops/pr-ci-preflight` cannot gate what has no PR — say so in its own output rather than leaving a reader
   to assume its denominator is the backlog.

Then re-run the cumulative rehearsal over all 52 and record the real number in `queue/MERGE-ORDER.md`,
replacing the one that is there.

**Do not "fix" this by opening eleven pull requests.** That hides the tool defect behind a one-time cleanup,
and the next branch without a PR is invisible again. Open them if the work is ready, but land the
enumeration fix either way.

## Log
- 2026-09-08T07:46:38Z claimed by agent/claude-opus-5; lease until 2026-09-08T10:46:38Z
