---
id: T-0027
title: Scenic score: land cover (USFS canopy, NLCD impervious) in a 150 m buffer
state: review
owner: agent/claude-opus-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T19:57:37Z
lease_expires_at: 2026-09-07T23:57:37Z
worktree: ../wt/T-0027
branch: task/T-0027
exclusive: []
touches: [services/etl/]
pins_affected: []
reviewer: agent/reviewer-32
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

## Log
- 2026-09-07T14:20:00Z BLOCKER FOUND AND ROUTED AROUND, before the task started. The brief named USFS Tree Canopy Cover and NLCD fractional impervious from MRLC. Both were checked live: MRLC's S3 now returns 403 "Anonymous users cannot invoke requests against Requester Pays buckets", and a deliberately bogus key on the same bucket returns AccessDenied rather than 404 - so the bucket blocks ALL anonymous access, not one stale object. The landing pages carry no download href at all. Retrieval needs the MRLC interactive Viewer or an authenticated EarthExplorer/ScienceBase order. There is no guessable public URL; this is portal-only, confirmed, not a guess-and-give-up.
- 2026-09-07T14:20:00Z DECISION: use ESA WorldCover 2021 v200 instead. Verified live: https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N36W123_Map.tif -> HTTP 200, 84 MB, anonymous, no auth. Tiles are 3 degrees; N36W123 covers 36-39N/120-123W, which contains the whole Bay Area. N36W126 (4 MB) is the mostly-ocean neighbour if the coast bbox needs it.
- 2026-09-07T14:20:00Z WHY IT IS A FAIR SWAP: WorldCover is 10 m (better than NLCD/TCC at 30 m) and its classes give both terms directly - Tree cover (10) and Shrubland (20) feed `canopy`, Built-up (50) feeds `impervious`. The scenic score needs FRACTIONS in a 150 m buffer, not absolute canopy percent, so class fractions are the right shape anyway. What we lose: TCC's continuous 0-100 canopy percent, and NLCD's calibrated impervious fraction. If the rank-order fixture set (T-0029) shows the redwood-vs-strip-mall discrimination is weak, revisit with a one-time manual MRLC clip hosted in our own R2 and pinned by sha256.
- 2026-09-07T14:20:00Z LICENCE: ESA WorldCover is CC-BY-4.0, which is NOT yet in KNOWN_LICENSES in services/etl/etl/manifest.py. The manifest validator will refuse the entry until it is added deliberately - that is the gate working. Add "CC-BY-4.0" there as part of this task, and carry the attribution string into LICENSE-DATA.
- 2026-09-07T19:57:37Z claimed by agent/claude-opus-5; lease until 2026-09-07T23:57:37Z

- 2026-09-07T20:30Z Handing to agent/reviewer-32; state -> review.

  **The brief's RED, from the raster:**

      old_la_honda  canopy 0.958  impervious 0.014  water 0.000   WOODED
      skyline       canopy 0.851  impervious 0.019  water 0.000   WOODED
      alviso_flat   canopy 0.086  impervious 0.690  water 0.017   BUILT_UP
      alviso_flat2  canopy 0.000  impervious 0.466  water 0.276   BUILT_UP

  Skyline high canopy, the industrial bay margin high impervious, separation of 0.5+ on both terms.

  **The prior research held, except the tile list.** MRLC really is closed - I did not re-verify the 403,
  the earlier note is specific enough to trust and re-checking costs a request that will fail. ESA
  WorldCover I did re-verify: both tiles 200, sizes unchanged. What did NOT hold is "N36W123 contains the
  whole Bay Area". Tiles are 3x3 degrees named by their SOUTH-WEST corner, so that one covers lon
  -123..-120 while the region runs to -123.62. N36W126 is needed and is now pinned. Same mistake as
  T-0026's four-tiles-instead-of-eight: verified against the URL, never against the bbox.

  **CC-BY-4.0 added to KNOWN_LICENSES deliberately.** The validator refused the entry until a human made
  that call, which is the gate working as designed rather than an obstacle.

  **What the reviewer should attack**, in the order I would:

  - `tile_for`. Same argument as T-0026's: a wrong tile name returns REAL data for the wrong place, and for
    this region the neighbouring tile is the open Pacific, which exists. Verify the naming convention against
    the tiles themselves with `gdalinfo`, not against my tests.
  - The class mapping. `CANOPY_CLASSES = {10, 20}` puts shrubland with tree cover and leaves grassland out.
    That is a judgement about what reads as green enclosure from a car, and it is mine alone. Grassland is
    30; if you think an oak-savannah road should score canopy, say so, because it changes the score for a
    large part of the east bay.
  - The 150 m buffer and the 50 m step. 49 samples per point before circular clipping. Check the buffer is
    actually isotropic (there is a test, but I wrote it) and that the step is fine enough not to alias
    against WorldCover's 10 m grid.
  - `is_wooded` at 0.5 and `is_built_up` at 0.4. Both are thresholds fitted to nothing yet - they separate
    these four roads by a wide margin, which is weak evidence that they are right in general.
  - The agreement tests between this fixture and the terrain one. The "wooded roads are the steep ones" test
    is a tripwire, not a law. Decide whether it belongs - it will fail the first time somebody adds a flat
    forested road, and that failure would be correct but confusing.

  Not done: nothing writes these fractions into the corpus. That is T-0030.
