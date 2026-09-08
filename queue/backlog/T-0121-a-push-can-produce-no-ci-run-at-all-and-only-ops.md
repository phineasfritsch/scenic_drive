---
id: T-0121
title: a push can produce no CI run at all, and only ops/merge notices
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/merge, .github/workflows/linux-core.yml]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "the cause of a PR head SHA with zero check runs is identified and written down"
  - "ops/merge prints an actionable next command when it refuses for no-checks-reported"
  - "RED: ops/merge 57 --dry-run refuses today with total=0 and no suggested remedy"
---
## Brief

**PR #57 (task T-0097) is reviewed, in `queue/done/`, and cannot merge, because its head commit has no
check runs at all.**

    $ gh pr view 57 --json headRefOid --jq .headRefOid
    4aafdd22a2c298209951a9045726ad43535ecb92

    $ gh pr view 57 --json statusCheckRollup --jq '.statusCheckRollup | length'
    0

    $ gh run list --branch task/T-0097 --limit 5 --json headSha,event,conclusion
    6db0597c4bb6  pull_request  success   2026-09-08T07:37:31Z
    55ec301d2306  pull_request  success   2026-09-08T07:27:06Z

Two runs on that branch, both successful, both for SHAs that are no longer the head. The reviewer pushed
`4aafdd2` at about 16:16 and **no run exists for it**. Not queued, not cancelled, not failed - absent.

    $ bash ops/merge 57 --dry-run
    task     T-0097 is in queue/done/ on task/T-0097
    checks   total=0 pending=0 failed=[none] mergeState=DIRTY
    MERGE REFUSED: no checks reported at all - CI did not run for this PR

**`ops/merge` refusing here is the system working**, and it is the only thing that noticed. `gh pr view`
shows a PR with no failing checks, which reads as fine.

## What has been ruled out, by measurement

  * **Not a global Actions outage.** In the same hour: `push main` x4, `pull_request task/T-0120`,
    `task/T-0103` x2, `task/T-0116`, `task/T-0108`, `task/T-0083`, `task/T-0092` all produced runs.
  * **Not a missing workflow on the branch.** `git ls-tree -r origin/task/T-0097 -- .github` lists
    `.github/workflows/linux-core.yml`.
  * **Not a `types:` filter.** `on: pull_request:` with no `types:` defaults to
    `[opened, synchronize, reopened]`.
  * **Not fixed by close/reopen.** `gh pr close 57 && gh pr reopen 57` both succeeded and the rollup stayed
    at 0, which also means the `reopened` event did not fire a run.
  * **Not the concurrency group.** `cancel-in-progress` would leave a `cancelled` run in the list. There is
    none.

**This is the second occurrence.** PR #33 (task T-0027) had the same shape earlier in the session and the
same close/reopen remedy failed there too.

Do:

1. **Find out what actually happened**, rather than papering over it. Start with
   `gh api repos/:owner/:repo/actions/runs?head_sha=4aafdd22a2c298209951a9045726ad43535ecb92` and the
   repository's Actions settings (a fork/actor restriction, a disabled workflow, or a spending limit would
   all produce exactly this and none of them show up in `gh run list`). Record what you find even if it
   turns out to be a GitHub-side quirk with no fix - the next person to hit this should not have to redo
   the elimination above.
2. **Give `ops/merge` a way to say what to do about it.** Today it refuses with the right reason and stops.
   It should also print the one command that re-triggers CI for a PR in this state, so the refusal is
   actionable rather than terminal.
3. **Consider `workflow_dispatch`** on `linux-core.yml`, so a run can be started by hand for exactly this
   case. It is two lines and it turns a stuck PR into one command. Note the trade-off: `workflow_dispatch`
   runs against a ref rather than the PR merge ref, so its result is not identical to the PR check - the
   task should say which it is and `ops/merge` must not treat a dispatch run as a PR check unless it is.

**Do not fix this by loosening `ops/merge`.** "No checks reported at all" must stay a refusal. A gate that
accepts an absence of evidence is the defect this repository is built around, and it would accept every
future PR whose CI silently did not run.

## Log
