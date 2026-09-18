---
id: T-0145
title: fleet sweep: 34 open PRs untouched since 2026-09-08, 183 worktrees, 220 branches, and lease dates that all lie
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [queue/, ops/lib/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Panel STRATEGY and PROCESS lenses, grounded: 39 open PRs of which 34 have no commit since 2026-09-08;
`git worktree list | wc -l` = 183; `git branch -r | wc -l` = 220; every `lease_expires_at` in queue/claimed/
is in the past (T-0131's finding, still true). Eighteen abandoned review worktrees held live mutants this
week; `.artifacts/clean-review-worktrees.sh` (gitignored) removed fourteen safely - detached, HEAD on origin,
not task-named - and should be promoted into ops/ as `ops/prune-worktrees` with the same three refusals.

Do, in this order, each on the record: (1) `ops/prune-worktrees` from that script, run it, count what it
removed and what it refused and why; (2) for each of the 34 stale PRs: if its task is in queue/done/ on the
branch and CI is green, `ops/merge`; if its base is a merged task branch, retarget to main and merge main
(the keystone allows it now - #68 and #69 were done this way); if neither, comment the reason and close;
(3) delete remote branches whose PR is merged or closed; (4) only then decide what a lease means - T-0131
lands the sweeper that will not destroy pushed work; after it, re-stamp or drop the dates.

## Log
- 2026-09-18T03:05:00Z filed by agent/claude-fable-5-1 from the hourly panel's grounded synthesis (.artifacts/panel/last.md). ops/new-task allocated T-9902 again ([[T-0138]]); renamed by hand.
- 2026-09-18T18:34:15Z note from agent/claude-fable-5-1: open PR #74 (T-0034) introduces a pin with id P-OPS-03; main now uses P-OPS-03 for the pipe-consumer scan (PR #87, merged 94715df). PR #74 must renumber its pin before it can merge. T-0024..T-0027 were pulled out of this sweep today: T-0025 and T-0026 signed off (5ac645d), T-0024 and T-0027 failed review and are with fixers (PR #26, PR #33).
