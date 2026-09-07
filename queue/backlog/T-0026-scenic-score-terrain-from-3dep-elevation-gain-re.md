---
id: T-0026
title: Scenic score: terrain from 3DEP (elevation gain, relief) with a smoothing pass
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

USGS 3DEP 1/3 arc-second COGs. Elevation gain per km sampled every 25 m, relief = (max-min) within
1 km. 3x3 smoothing first: 3DEP is bare-earth, but noise at 10 m still produces phantom gain on flat roads.

RED: a known-flat fixture (Alviso/Bay margin) must score near 0 gain; a known-steep one (Old La Honda) must not.

## Log
