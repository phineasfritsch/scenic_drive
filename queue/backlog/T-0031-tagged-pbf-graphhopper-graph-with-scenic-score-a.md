---
id: T-0031
title: Tagged PBF -> GraphHopper graph with scenic_score as an encoded value, deployed to the VPS
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/, services/routing/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

osmium writes `scenic_score=0..10` back onto ways; the ~40-line GraphHopper TagParser plugin
registers it as an encoded value so `car_scenic` custom models can reference it. Import in WSL2, rsync the
graph-cache to the RackNerd box, atomic symlink flip keeping N-1.

RED: request a route with the lambda penalty at 0 and at 8 -> duration must be monotonically non-decreasing.
That is the property the whole budget search depends on, and it is cheap to check the moment the graph exists.

## Log
