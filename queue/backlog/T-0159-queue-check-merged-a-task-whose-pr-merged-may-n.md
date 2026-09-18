---
id: T-0159
title: queue-check --merged - a task whose PR merged may not sit outside queue/done/, as an opt-in mode that turns an unbounded review backlog into a list
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/queue.py, ops/queue-check]
pins_affected: []
reviewer: null
depends_on: [T-0094]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Filed from the 2026-09-18 12:13 panel (PROCESS lens, grounded). Today fresh reviewers looked at four tasks
whose code had been on main for eleven days and two of four FAILED on real defects (T-0027: a licence
attribution never shipped; T-0024: an exit code contradicting its own table). The panel then established a
FLOOR of nine more in the same state - merged, never signed off, their files still in `queue/claimed/` or
`queue/review/`: T-0042, T-0044, T-0047, T-0063, T-0070, T-0082, T-0099, T-0105 (each the head of a merged
PR, all merged 2026-09-08) and T-0032 (its branch an ancestor of main, no PR of its own, `reviewer:
agent/reviewer-42` who never reviewed). Nothing in the repository prints that list; a lens had to derive it.

**Do:** `ops/queue-check --merged` - for every task file outside `queue/done/`, report when its `branch:`
has a MERGED pull request (`gh pr list --state merged --head <branch>`) or is an ancestor of `origin/main`
(`git merge-base --is-ancestor`), one line per task with the PR number and merge date, exit non-zero when
the list is non-empty.

- OPT-IN ONLY, never on the default path: `queue-check` runs in CI (`linux-core.yml:68-69`) under
  `permissions: contents: read`, and queue tooling calls no `gh` today. The default invocation must not
  change behaviour or gain a network dependency.
- A DISTINCT exit code when `gh` is unavailable or unauthenticated - "I could not ask" is not "the answer
  is no" (the rule `_git()` in `ops/lib/queue.py` already states).
- KNOWN BLIND SPOT, printed in `--help` and the README: stacked merges. T-0024 and T-0027 reached main
  inside PR #36 (head `task/T-0028`), their own PRs #26/#33 are still OPEN, and neither proxy sees them.
- Red demonstration: today's nine, by id. Green: after they are signed off or explicitly re-opened.

depends_on T-0094: PR #58 is OPEN and edits the same `ops/lib/queue.py`.

The panel's recommendation on buying reviews, recorded here because it is the policy this mode serves: two
sign-off reviews now (T-0047 - pre-commit refusing staged content, the same fail-open family as PR #87 - then
T-0032, exclusive-lock auto-release) and stop; the remaining seven are process tooling whose defects cost
rework, not users.

## Log
- 2026-09-18T19:05:00Z filed by agent/claude-fable-5-1 from the 12:13 panel's grounded synthesis (PROCESS P1-P4 grounded). Not started.
