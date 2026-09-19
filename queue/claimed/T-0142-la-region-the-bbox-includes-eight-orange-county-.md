---
id: T-0142
title: LA region: the bbox includes eight Orange County cities the comment says it excludes; counts_from names a source the Log did not fetch; dem.tile_for still gates on TILES so la has no elevation
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T02:59:00Z
lease_expires_at: 2026-09-19T10:59:00Z
worktree: .worktrees/T-0142
branch: task/T-0142
exclusive: []
touches: [services/etl/regions/la/, services/etl/etl/dem.py, services/etl/tests/, services/etl/inputs/manifest.yaml]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "LA TERRAIN (the 20:13 panel's miss, grounded): dem.tile_for resolves through dem.tiles_for_bbox of the ACTIVE region, not the sfbay TILES constant - a test that tile_for(34.07, -118.45) with la active returns 'n35w119' (RED today: dem.py returns None; tests/test_dem_tiles.py already pins tile_name for UCLA), and services/etl/inputs/manifest.yaml carries entries with sha256 lines for 3dep-n34w118.tif, 3dep-n34w119.tif, 3dep-n35w118.tif, 3dep-n35w119.tif (the digest recorded by `python -m etl.fetch --record-digest NAME` or by hashing the file the orchestrator pre-downloaded into the shared inputs/, and quoted); the sfbay eight are untouched"
  - "services/etl/regions/la/region.json: the bbox and its _comment_counties / _comment_bbox agree - either the bbox is cut back to exclude northern Orange County (the eight cities the reviewer of PR #68 listed) or the comments say it includes them; a pytest RED by name today (a point-in-bbox test over Anaheim's coordinates contradicting the comment), then green"
  - "the counts block re-recorded from the same extract if the bbox moves (counts_from names it); the DEM tile list re-derived by dem.tiles_for_bbox and quoted"
---
## Brief

Found by agent/rv-pr68 while PASSING PR #68 (T-0107, the LA region), reported as non-blocking with the
reasoning recorded; filed so it is not rediscovered. Three findings, each with the reproduction the reviewer
ran; none blocked because none is a numeric inconsistency - the counts were measured over the box that is
recorded, and `counts_from` ties them to it.

### 1. The bbox includes northern Orange County, and the prose says it does not

`regions/la/region.json` records `bbox -119.0,33.7,-117.85,34.45`. The Brief of T-0107 says the box
*"deliberately EXCLUDES Orange County"*, and the file's `_comment_counties` names the clipped slivers as
Ventura and San Bernardino only. Any point test against that box puts these INSIDE it: Anaheim
(33.8366, -117.9143), Santa Ana (33.7455, -117.8677) - the county seat - Fullerton, Buena Park, Garden
Grove, Westminster, Seal Beach, La Habra. Eight unambiguously Orange County cities, not a sliver.

**The fix is the comment, NOT the bbox.** Editing the bbox now would correctly fail the region load until a
re-extract, because `counts_from` pins the counts to the box they were measured over - that is the guard
working. Say what the box holds. It also softens one sentence of T-0107's ratio argument: `primary` at 8.51x
sfbay is partly an OC arterial grid the Log does not acknowledge.

### 2. `counts_from.source` names a file the run did not fetch

`counts_from.source = "california-osm.pbf"`; T-0107's Log (the 2026-09-08 extract entry) says
`california-latest.osm.pbf` was fetched, 1.3 GB, md5-verified against Geofabrik's sidecar.
`CountsFrom.problems()` only checks the field is non-empty, so nothing breaks - but a reviewer with the
container, matching the source by name, has an extra hop. Record the name the fetch used, and consider
having `problems()` require the source to be one `inputs/manifest.yaml` knows.

### 3. `dem.tile_for` still gates on `TILES`, so `la` has no elevation

`services/etl/etl/dem.py:90` - `return name if name in TILES else None`. T-0107 made the tile set
DERIVABLE (`tiles_for_bbox`) and pinned it (`test_la_needs_exactly_four_tiles` asserts four literals), but
did not wire it: the four LA tiles are absent from `inputs/manifest.yaml` until their sha256 exists, and
`tile_for` reads the old constant. Disclosed in T-0107's Log as deliberately sequenced behind the dem.py
work in flight. Recorded here so the next task does not assume LA scoring has terrain. Closing it means:
the four tiles fetched and sha256'd into the manifest, `tile_for` reading `tiles_for_bbox` of the active
region, and a test that a Westwood coordinate resolves to `n34w119`.

### Also on the record from the same review

* `.artifacts/record-provenance.py` - the script T-0107's Log says wrote both regions' counts from their
  `meta.json` "with nothing transcribed by hand" - is gitignored, so that claim is not reproducible from
  the tree. Repo convention for scratch; an unverifiable claim rather than a checked one.
* `ops/sane` code 4 cannot run for `la` on this box (no `work/la/meta.json`), so the +/-15% comparison is
  unexercised for this region.
* No `curated.yaml` for `la`; T-0107's Brief's twelve Westwood-adjacent seeds are not in the tree.

## Log
- 2026-09-18T02:20:00Z filed by agent/claude-fable-5-1 from agent/rv-pr68's review of PR #68, which PASSED and
  merged as `ef5768d`. `ops/new-task` allocated **T-9902 for the sixth time** ([[T-0138]]); renamed by hand.
- 2026-09-19T02:11:14Z PROMOTED to ready/ by agent/claude-fable-5-1 (19:13 panel, grounded): T-0168 clips regions/la next; the clip should land on the bbox the file's comment claims. Whether the owner's commute crosses -117.85 or 33.70 is FOR THE HUMAN.
- 2026-09-19T02:58:56Z RE-SCOPED by agent/claude-fable-5-1 (20:13 panel, STRATEGY F1 + grounding): finding 3 is a HARD prerequisite of
  T-0168, not a nicety - `dem.tile_for` (dem.py:90) returns None for every point outside sfbay's eight tiles, so
  a regions/la clip would score with terrain silently zeroed and T-0168's check-4 numbers and top-10 read would
  mean nothing. New first acceptance bullet above; `services/etl/inputs/manifest.yaml` added to touches. Two
  corrections to the brief's section 3: the Westwood/UCLA tile is n35w119 (tests/test_dem_tiles.py:47), not
  n34w119; and the bbox itself does NOT move in this task - finding 1 is the COMMENT fix only, until the owner
  answers where they commute (FOR THE HUMAN). The four LA tiles were started downloading into the main
  checkout's shared services/etl/inputs/ by the orchestrator at 2026-09-19T02:58:56Z (log under .artifacts/fetch/); hash what is
  there rather than re-downloading, and say which you did.
- 2026-09-19T02:59:00Z claimed by agent/claude-opus-5; lease until 2026-09-19T10:59:00Z
