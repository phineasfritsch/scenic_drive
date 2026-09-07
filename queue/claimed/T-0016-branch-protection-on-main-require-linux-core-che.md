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
touches: [.github/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

(what, why, and the exact demonstration that proves it — including the red run)

## Log
- 2026-09-07T07:05:00Z raised backlog -> ready: main went red on 2026-09-07 because a PR was merged while checks were UNSTABLE. Until this exists, nothing mechanically stops that.
- 2026-09-07T09:11:42Z claimed by agent/claude-opus-5; lease until 2026-09-07T12:11:42Z
