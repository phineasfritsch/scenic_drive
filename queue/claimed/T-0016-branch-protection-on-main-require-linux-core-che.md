---
id: T-0016
title: Branch protection on main: require linux-core checks before merge
state: claimed
owner: agent/claude-opus-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T09:11:42Z
lease_expires_at: 2026-09-07T12:11:42Z
worktree: ../wt/T-0016
branch: task/T-0016
exclusive: []
touches: [.github/, ops/merge, queue/README.md]
pins_affected: []
reviewer: null
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
