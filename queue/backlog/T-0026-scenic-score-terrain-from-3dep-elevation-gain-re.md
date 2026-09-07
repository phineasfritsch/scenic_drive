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

## Log
- 2026-09-07T13:30:00Z VERIFIED source facts (HEAD-checked 2026-09-07), so this task starts with numbers instead of exploring:
  The Bay Area needs FOUR 1-degree 3DEP tiles at 1/3 arc-second, all HTTP 200 from
  https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/current/<tile>/USGS_13_<tile>.tif
    n38w123  213 MB  (north bay / Marin / Sonoma coast)
    n38w122  477 MB  (east bay, Delta)
    n37w122  396 MB  (south bay, peninsula, Santa Cruz mountains)
    n37w123    5 MB  (almost entirely ocean - small on purpose, not an error)
  Total ~1.09 GB. Content-type image/tiff. Static (n38w123 Last-Modified 2025-08-27), so each gets a hard
  sha256 in the manifest via `ops/etl-fetch-inputs --record-digest <name>`.
- 2026-09-07T13:30:00Z 3DEP is bare-earth, which is what we want, but at 10 m it still carries enough noise to
  invent elevation gain on flat ground - hence the 3x3 smoothing pass before computing gain or relief. The flat
  fixture (Alviso / bay margin) is the check that the smoothing is actually applied.
