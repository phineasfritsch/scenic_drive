---
id: T-0031
title: Tagged PBF -> GraphHopper graph with scenic_score as an encoded value, deployed to the VPS
state: ready
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
acceptance:
  - "FIRST SLICE (this promotion): the digest-pinned GraphHopper image imports .worktrees/T-0025/services/etl/inputs/vermont-osm.pbf (45,880,330 bytes == manifest.yaml) in WSL with the scenic_score TagParser plugin and the car_scenic_base profile; the import log's way/edge counts quoted"
  - "RED BY NAME: T(lambda) non-decreasing over {0,1,2,4,8} on every fixture (plan line 215) - red with a deliberately inverted band multiplier, then green; the five durations per fixture printed and quoted"
  - "the second half (the Bay Area graph, rsync, the atomic symlink flip, N-1 kept) stays behind T-0168 and is not claimed by this slice"
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
- 2026-09-19T00:40:47Z PROMOTED to ready/ for its FIRST SLICE by agent/claude-fable-5-1 (17:13 panel, STRATEGY, grounded): the Vermont
  extract is on disk byte-matching the manifest, and the T(lambda) property is about the TagParser and the
  custom model, not California - the 20:57:28Z entry already ruled the slice. depends_on stays [T-0168] for
  the second half. Vermont carries no scenic_score tags: the slice tags them itself from a synthetic rule
  (e.g. curvature-only) and says so, or reads T-0146's assembler over a Vermont way-record fixture - rule it.
- 2026-09-19T00:49:41Z LA FIRST, by agent/claude-fable-5-1 (the owner lives in Los Angeles - memory user-lives-in-la): after the Vermont first slice, the FIRST served graph is LA (regions/la), sfbay second - the M3 exit 'you drive engine output from the CLI' is an LA drive; the plan's Bay Area fixtures stay the CI golden set.
