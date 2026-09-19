---
id: T-0194
title: landcover - a region-derived served WorldCover tile set (tiles_for_region + UNSERVED, the way dem.py serves 3DEP) recorded per region and pinned in manifest.yaml; LA's is N33W120 and nothing in the tree says so
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/etl/landcover.py, services/etl/tests/, services/etl/regions/, services/etl/inputs/manifest.yaml]
pins_affected: []
reviewer: null
depends_on: [T-0168]
verify: [ops/test, ops/check-pins]
acceptance:
  - "landcover.tiles_for_region(region_id) derives the WorldCover tile set from the region's bbox (tile_for's 3-degree SW-corner naming) minus an UNSERVED literal, mirroring dem.tiles_for_region; RED BY NAME first: a test asserting tiles_for_region('la') == {'N33W120'} and tiles_for_region('sfbay') == the two sfbay tiles manifest.yaml already pins, red until the function exists"
  - "the manifest test that pins every 3DEP tile a region needs (T-0142's shape) gains the WorldCover half: every tile tiles_for_region returns for each region has a manifest entry with a sha256 - red by name on a region whose tile is unpinned"
  - "regions/<id>/region.json's _comment_landcover names the derived set for the human, derived not typed; region.py refuses a comment that disagrees with the derivation the way it refuses a stale counts_from.bbox"
  - "cd services/etl && python -m pytest tests -rs -o addopts= -> count line and zero skips at the final commit"
---
## Brief

From the 23:13 panel (STRATEGY, grounded). T-0142 made LA's four 3DEP tiles a typed, derived, pinned set; the
WorldCover side has no equivalent: landcover.tile_for floors a point to a 3-degree tile and sample_codes refuses a
missing raster by name (T-0189), but nothing derives the set a REGION needs, nothing pins it in manifest.yaml, and
services/etl/inputs/ held zero WorldCover tiles for LA when T-0168 was claimed - the first real run would have
refused at the first land-cover sample. T-0168 fetches and pins LA's N33W120 by hand as its first command; this
task makes the derivation the rule so the next region cannot repeat the miss.

## Log
- 2026-09-19T05:28:52Z filed by agent/claude-fable-5-1 from the 23:13 panel's grounded synthesis. Not started; after T-0168.
