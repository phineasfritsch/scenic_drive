---
id: T-0016
title: Branch protection on main: require linux-core checks before merge
state: review
owner: agent/claude-opus-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T09:11:42Z
lease_expires_at: 2026-09-07T12:11:42Z
worktree: ../wt/T-0016
branch: task/T-0016
exclusive: []
touches: [.github/, ops/merge, queue/README.md]
pins_affected: []
reviewer: agent/reviewer-7
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

main was broken on 2026-09-07 by merging PR #6 while `gh` reported mergeStateStatus=UNSTABLE. The intended fix
was GitHub branch protection requiring the linux-core checks.

THAT IS NOT AVAILABLE: both `branches/main/protection` and `rulesets` return 403 "Upgrade to GitHub Pro or make
this repository public" - the repo is private on a free personal plan. Verified directly against the API.

So the gate lives in the repo instead: `ops/merge <pr> [--wait]` refuses unless
  (1) the PR's queue task is in queue/done/ on the PR head (a reviewer signed it off),
  (2) every check run has concluded and none failed,
  (3) mergeStateStatus is CLEAN,
  (4) at least one check actually reported (a PR with no CI at all is refused, not waved through).

HONEST LIMITATION, stated in the script itself: this is client-side and bypassable with `gh pr merge`. It makes
the safe path the easy path. Server-side enforcement needs GitHub Pro (~$4/mo) or a public repo - a decision for
the owner, recorded here rather than silently dropped.

## Log
- 2026-09-07T07:05:00Z raised backlog -> ready: main went red on 2026-09-07 because a PR was merged while checks were UNSTABLE. Until this exists, nothing mechanically stops that.
- 2026-09-07T09:11:42Z claimed by agent/claude-opus-5; lease until 2026-09-07T12:11:42Z
- 2026-09-07T09:30:00Z FINDING that changes the task: GitHub branch protection is NOT available here. `gh api repos/phineasfritsch/scenic_drive/branches/main/protection` and `.../rulesets` both return 403 "Upgrade to GitHub Pro or make this repository public". Private repo, free personal plan. Recorded rather than silently dropped; the owner's options are Pro (~$4/mo), a public repo, or the client-side gate built here.
- 2026-09-07T09:30:00Z GREEN: ops/merge 11 --dry-run with checks finished -> "checks total=2 pending=0 failed=[none] mergeState=CLEAN" then "DRY RUN: every gate passed", exit 0.
- 2026-09-07T09:30:00Z RED 1 (review gate): ops/merge 9 -> "T-0017 is not in queue/done/ on task/T-0017 - a reviewer has not signed it off", exit 1.
- 2026-09-07T09:30:00Z RED 2 (THE outage case): throwaway PR #11 on tmp/merge-probe, run while CI was still going -> "checks total=2 pending=2 failed=[none] mergeState=UNSTABLE" then "MERGE REFUSED: 2 check(s) still running", exit 1. UNSTABLE is exactly the state I merged PR #6 in when main broke.
- 2026-09-07T09:30:00Z RED 3 (bad input): nonexistent PR -> "MERGE REFUSED: PR 999 does not exist or is not readable", exit 1; no args -> usage, exit 2; unknown option -> exit 2.
- 2026-09-07T09:30:00Z SELF-CAUGHT during the demos: the first version did not check `gh pr view`'s output, so a nonexistent PR fell through the review gate ("branch names no task") before failing later for the wrong reason. Fixed to fail fast.
- 2026-09-07T09:30:00Z Added --dry-run so the green path is provable without merging a throwaway commit into main. Probe PR #11 closed, tmp/merge-probe deleted locally and on origin, worktree removed.
- 2026-09-07T09:30:00Z queue/README.md step 7 now mandates ops/merge over gh pr merge and states the bypassability limitation.
- 2026-09-07T09:30:00Z moved to review/, reviewer agent/reviewer-7
