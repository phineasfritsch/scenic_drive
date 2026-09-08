---
id: T-0094
title: queue-check reports OK while a task with an open PR sits in claimed with reviewer null
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

**The reviewer-is-not-owner gate cannot fire, because the state it inspects is never reached.**
`ops/queue-check` enforces `reviewer != owner` — CLAUDE.md names it as the mechanism — but only for tasks
that are *in* `queue/review/` with a `reviewer:` set. A task whose PR is open while its file still says
`state: claimed` / `reviewer: null` is not checked against anything, and `queue-check` reports `QUEUE OK`.
Found by the reviewer of PR #54 as a [low] on one task. It is not one task.

Measured on 2026-09-08, on **each PR's own head** (not on main — a task moved to `review/` on its branch
correctly still reads `claimed` on main until it merges, so main is the wrong place to look):

    PR#17..#46   31 PRs   ->  queue/review/ or queue/done/, reviewer set on every one
    PR#47 T-0071 -> CLAIMED reviewer=null        PR#52 T-0063 -> CLAIMED reviewer=null
    PR#48 T-0075 -> CLAIMED reviewer=null        PR#53 T-0083 -> CLAIMED reviewer=null
    PR#49 T-0062 -> CLAIMED reviewer=null        PR#54 T-0060 -> CLAIMED reviewer=null
    PR#50 T-0070 -> CLAIMED reviewer=null        PR#55 T-0065 -> CLAIMED reviewer=null
    PR#51 T-0082 -> CLAIMED reviewer=null        PR#56 T-0081 -> CLAIMED reviewer=null

    10 of 10 consecutive PRs, all opened in one session, all reporting QUEUE OK on their own head.

The process held for 31 PRs and then failed 10 times in a row without a single check going red. That is
the signature this repository was built to catch: **a gate that passes because the work never enters the
state the gate reads.** `queue/README.md` step 6 is the only thing asking for the transition, and step 6
is prose.

**What makes this load-bearing rather than tidiness.** `reviewer != owner` is the one mechanical defence
against an agent reviewing its own work. Ten open PRs currently carry no reviewer at all, so for those ten
the rule is not merely unchecked — there is nothing for it to check. A merge that lands one of them lands
work whose reviewer field was never populated, and `ops/merge` does not ask.

Do:

1. `ops/queue-check` gains a rule: **a task whose branch has an open PR must not be in `claimed/`, and
   must carry a non-null `reviewer:`.** Ask GitHub through the same stub seam the merge tests already use
   (`ops/lib/gh-stub-for-merge-tests`), so this is testable offline and does not make `queue-check` require
   the network — a check nobody can run offline is a check people stop running.
2. When GitHub cannot be reached, the rule must **say it was skipped and why**, and must not silently pass.
   A guard that reads an unavailable fact in silence is the fail-open class T-0063 and T-0082 both hit.
3. Red demo: a fixture task in `claimed/` with `reviewer: null` and a stubbed open PR on its branch → exit
   non-zero, naming the task and the PR. Green: the same task in `review/` with a reviewer set → exit 0.
   Also demonstrate the offline path prints the skip line and does **not** report OK as though it checked.
4. Then transition the ten real tasks above with `git mv` on each branch — a copy left in two directories
   is what makes `queue-check` fail (see [[queue-transition-on-stacked-branches]]); each must get a
   `reviewer:` that is not `agent/claude-opus-5`.

**Do not** make the rule key on "a PR exists" alone: a `device/*` or `tmp/*` branch has no task file and
must not be dragged in. Key on the task id parsed from the head ref, the way `ops/merge` already does.

## Log
