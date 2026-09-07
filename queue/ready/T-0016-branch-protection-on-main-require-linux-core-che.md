---
id: T-0016
title: Branch protection on main: require linux-core checks before merge
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
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
