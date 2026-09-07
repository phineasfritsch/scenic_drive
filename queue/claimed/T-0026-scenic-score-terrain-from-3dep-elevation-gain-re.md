---
id: T-0026
title: Scenic score: terrain from 3DEP (elevation gain, relief) with a smoothing pass
state: claimed
owner: agent/claude-opus-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T17:41:07Z
lease_expires_at: 2026-09-07T21:41:07Z
worktree: ../wt/T-0026
branch: task/T-0026
exclusive: []
touches: [services/etl/]
pins_affected: []
reviewer: agent/reviewer-31
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
- 2026-09-07T17:50Z CORRECTION, before any of the above is relied on: the tile list is HALF the region.

  The earlier note says "The Bay Area needs FOUR 1-degree 3DEP tiles" and lists n38w123, n38w122, n37w122,
  n37w123. Those four URLs are real - I re-checked all four, still HTTP 200, sizes unchanged - but the list
  was verified against the URLs and never against the bbox.

  A tile `nXXwYYY` covers latitude [XX-1, XX] and longitude [-YYY, -YYY+1]. Those four therefore cover
  lat 36-38, lon -123..-121. The region is lat 36.85-38.92, lon -123.62..-121.55 (as tightened in T-0024),
  which also needs everything north of 38 and everything west of -123:

      n38w123   222,936,410   lat 37-38  lon -123..-122   (in the original list)
      n38w122   499,782,172   lat 37-38  lon -122..-121   (in the original list)
      n37w122   415,276,131   lat 36-37  lon -122..-121   (in the original list)
      n37w123     5,494,012   lat 36-37  lon -123..-122   (in the original list)
      n39w123   488,805,186   lat 38-39  lon -123..-122   MISSING - Sonoma, Napa, north bay
      n39w122   490,935,937   lat 38-39  lon -122..-121   MISSING - Solano, the north Delta
      n38w124     1,656,024   lat 37-38  lon -124..-123   MISSING - the outer coast
      n39w124   153,554,813   lat 38-39  lon -124..-123   MISSING - the Sonoma coast

  All eight HEAD-checked 2026-09-07: HTTP 200, content-type image/tiff. Total 2,278,440,685 bytes, not the
  ~1.09 GB the earlier note gives.

  `n37w124` (lat 36-37, lon -124..-123) returns **HTTP 404**. It is entirely ocean, so USGS does not publish
  it. That is a fact the fetcher and the sampler both have to handle deliberately: a tile that does not exist
  is not a fetch failure, and a coordinate with no tile is "no elevation here", not zero. Zero metres would
  read as sea level, which is a real elevation and would quietly flatten every coastal way's relief.

  What went wrong with the original note is worth naming, because it is the failure this repo keeps finding:
  four URLs were checked and all four returned 200, so the list looked verified. Nothing checked the list
  against the thing it was a list FOR. Missing the north half of the region would not have crashed anything -
  Sonoma and Napa would simply have scored no elevation gain, and the scenic index would have quietly
  preferred the flat south bay.

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
- 2026-09-07T17:41:07Z claimed by agent/claude-opus-5; lease until 2026-09-07T21:41:07Z
