---
id: T-0142
title: LA region: the bbox includes eight Orange County cities the comment says it excludes; counts_from names a source the Log did not fetch; dem.tile_for still gates on TILES so la has no elevation
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/regions/la/, services/etl/etl/dem.py, services/etl/tests/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
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
