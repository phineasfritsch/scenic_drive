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
depends_on: [T-0168]
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
- 2026-09-18T19:52:17Z header corrected by agent/claude-fable-5-1 (13:13 panel, grounded): this task's own brief has osmium write
  `scenic_score=0..10` back onto ways, and T-0146 is the only producer of that value; `depends_on: []` said
  otherwise, and `ops/queue-next` reads headers, not prose. T-0029 (blocked, owned, with a named reviewer)
  has the same missing dependency - T-0146's brief says "Unblocks T-0029" - and is left for its owner.
- 2026-09-18T20:57:28Z amended by agent/claude-fable-5-1 (14:13 panel, grounded): (a) depends_on now names T-0168, the task that
  actually writes `scenic_score` onto ways (T-0146 was cut to its fixture half). (b) This task's RED tests
  lambda at 0 and at 8 only; plan line 215 reads "`T(lambda)` non-decreasing over {0,1,2,4,8} on every
  fixture" - the RED must run all five and assert each step. (c) The property is about the TagParser's
  encoded value and the custom model, not about California: the FIRST SLICE imports a small extract already
  on this box (`vermont-osm.pbf`, manifest-pinned, 45,880,330 bytes; or the filtered sfbay extract in
  `.worktrees/T-0028/services/etl/work/sfbay/`) in WSL and proves monotonicity there; the rsync, the atomic
  symlink flip and the full Bay Area graph stay in this task's second half.
