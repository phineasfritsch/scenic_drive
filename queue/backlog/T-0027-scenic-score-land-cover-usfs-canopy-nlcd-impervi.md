---
id: T-0027
title: Scenic score: land cover (USFS canopy, NLCD impervious) in a 150 m buffer
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

USFS Tree Canopy Cover and NLCD fractional impervious, both CONUS 30 m, both public domain.
canopy and (1 - impervious) are the two biggest terms in E - this is what separates a redwood road from a
strip-mall arterial.

RED: a fixture through a known industrial area must score high impervious; a fixture on Skyline must score high
canopy. Both from the raster, not hand-entered.

## Log
