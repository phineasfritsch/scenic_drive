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
- 2026-09-19T03:05:00Z RULINGS BEFORE CODE by agent/claude-opus-5 (owner and author of this task).
  **R1 THE SEAM. The Brief says "read terrain.py's call site" - there is none.** `terrain.py` imports
  `.curvature` and nothing else; `grep -rn "tile_for\|tiles_for_bbox\|sample_smoothed\|group_by_tile"
  services/etl --include=*.py` returns only `dem.py` itself, its tests, and `landcover.py`'s own unrelated
  `tile_for` (NLCD-style tiles, different naming rule, untouched). **The DEM sampler has no production caller
  yet** - T-0168's clip will be the first - so "the region passed by the caller" could not be read off an
  existing call site and had to be decided rather than discovered. Ruling, smallest change that removes the
  sfbay constant from the decision: a `tiles` argument threaded `tile_for` -> `group_by_tile` -> `sample` ->
  `sample_smoothed`, resolved ONCE per call in `group_by_tile` (per point it would be a region.json read per
  point), whose value is normally `dem.tiles_for_region(region_id)` = `tiles_for_bbox` of THAT region's own
  bbox minus `UNSERVED`. `TILES` stays exactly as it was - sfbay's hand-checked golden set - and is now
  pinned AGAINST the derivation (`tiles_for_region("sfbay") == TILES`) instead of being the gate.
  **R2 THE DEFAULT IS NOT SFBAY.** `tiles=None` resolves to `served_tiles()`, the union over every region
  under `regions/`, not to `TILES`. Defaulting to sfbay's eight would have left the exact defect this task
  closes reachable by omission: T-0168 forgetting the argument would get no tile for any LA point, terrain
  silently zero, and nothing would say so - "absence, not wrong" is the whole finding. The union keeps every
  existing sfbay assertion in `tests/test_dem.py` green (n38w123 for SF, None for n37w124, None for
  45/-100) and makes absence-by-omission impossible for a region we serve. Cached per regions-root.
  **R3 ABSENCE IS UNCHANGED.** A point outside the active region's tiles is `None`, never 0 m - 0 m is sea
  level, a real elevation. Pinned three ways in
  `test_absence_is_still_absence_outside_the_active_region`: an sfbay point with `la` active, a point in no
  region at all, and the ocean tile n37w124, which is now excluded ONCE by `dem.UNSERVED` with its 404
  reason rather than by being absent from a hand-typed per-region list.
  **R4 FINDING 1 IS THE COMMENT; THE BBOX DOES NOT MOVE.** Confirmed against the file rather than assumed:
  `counts_from.bbox` is `-119.0,33.7,-117.85,34.45` and `CountsFrom.problems()` refuses a counts_from.bbox
  that disagrees with the region's bbox, so cutting the south-east corner back would correctly fail the
  region load until the extract is re-run. Anaheim (33.8366,-117.9143) and Santa Ana (33.7455,-117.8677)
  are inside the recorded box - re-measured here, not taken on trust. The prose changed; the numbers did not.
  **R5 SIX OF THE EIGHT CITIES HAVE NO COORDINATES IN THIS TREE.** agent/rv-pr68 recorded lat/lon for
  Anaheim and Santa Ana only. Fullerton, Buena Park, Garden Grove, Westminster, Seal Beach and La Habra are
  NAMED in `_comment_bbox` and in the test's docstring and deliberately not typed as coordinates: inventing
  six lat/lons to make my own test pass is precisely the behaviour `ops/` exists to contradict.
  **R6 THE COMMENT TEST DOES NOT BREAK "NEVER ANCHOR ON A COMMENT".** `_comment_bbox` and
  `_comment_counties` are JSON FIELDS of a committed config file, read back by `json.loads` and preserved by
  `region.load` (which refuses unknown NON-underscore keys and passes `_`-prefixed ones through untouched).
  No build step strips them, which is the property that rule is about; CLAUDE.md's own list of legitimate
  anchors names config files. The test anchors on the FIELD and on the bbox numbers, and the numeric half
  (`Anaheim is inside the box`) fails independently of any wording.
  **R7 FINDING 2 IS NOT SMALL - IT GOES TO STILL OPEN.** `counts_from.source = "california-osm.pbf"` is the
  manifest entry's NAME (`inputs/manifest.yaml` line 8) whose `url` is `.../california-latest.osm.pbf`, so
  the recorded source already matches what the tree calls that file; the reviewer's stronger suggestion -
  `CountsFrom.problems()` requiring the source to be one the manifest knows - makes `region.py` import
  `manifest.py`, changes a validator every region load runs through, and needs its own red test over both
  regions and a fixture region that names a file the manifest does not have. That is a task, not a line.
  **R8 MUTATION POPULATION.** `dem.py` is not a new module and has no population under `ops/mutate/`; that
  directory is outside this task's `touches:`. Noted in STILL OPEN.
- 2026-09-19T03:06:00Z RED, by name, before any implementation
  (`cd services/etl && python -m pytest tests/test_dem_tiles.py -q --no-header -rf`), 7 failed, 10 passed:
  ```
  FAILED tests/test_dem_tiles.py::test_a_westwood_point_resolves_to_its_tile_when_la_is_active
  FAILED tests/test_dem_tiles.py::test_the_sfbay_golden_set_is_exactly_what_the_derivation_serves
  FAILED tests/test_dem_tiles.py::test_naming_no_region_no_longer_means_sfbay
  FAILED tests/test_dem_tiles.py::test_absence_is_still_absence_outside_the_active_region
  FAILED tests/test_dem_tiles.py::test_grouping_and_sampling_carry_the_active_region_through
  FAILED tests/test_dem_tiles.py::test_the_manifest_pins_every_tile_la_needs
  FAILED tests/test_dem_tiles.py::test_the_bbox_comment_does_not_claim_to_exclude_cities_the_box_contains
  ```
  The two that matter, verbatim - the defect itself, and the comment contradicting the numbers:
  ```
  E       AssertionError: assert None == 'n35w119'
  E        +  where None = <function tile_for at 0x00000287525711B0>(34.07, -118.45)
  E        +    where <function tile_for at 0x00000287525711B0> = dem.tile_for
  tests\test_dem_tiles.py:144: AssertionError
  E       AttributeError: module 'etl.dem' has no attribute 'tiles_for_region'. Did you mean: 'tiles_for_bbox'?
  tests\test_dem_tiles.py:131: AttributeError
  E       AssertionError: the comment claims to exclude Orange County; Anaheim and Santa Ana are inside the box
  E       assert 'Orange County' not in ': Orange Co... this month.'
  E         'Orange County' is contained here:
  E           : Orange County, the Inland Empire and San Diego. They are a different market, not a bigger bbox, and each degree costs build time and graph size for roads nobody here will drive this month.
  tests\test_dem_tiles.py:201: AssertionError
  ```
  After `dem.py` and before the manifest and region.json edits, the same command left exactly the two that
  depend on data rather than code still red - `test_the_manifest_pins_every_tile_la_needs` and
  `test_the_bbox_comment_does_not_claim_to_exclude_cities_the_box_contains` - so each half was seen red for
  its own reason.
- 2026-09-19T03:07:00Z THE FOUR DIGESTS ARE THE ORCHESTRATOR'S, NOT A RE-FETCH. All four tiles were already
  complete in the main checkout's shared gitignored `services/etl/inputs/` when this task reached them, and
  `.artifacts/fetch/la-dem-20260919T025932Z.log` printed `sha256=` for each with `EXIT=0`. The digests and
  `bytes:` in `inputs/manifest.yaml` are COPIED FROM THAT LOG, verified against the files' sizes on disk
  (`ls -la`: 351919765 / 77566808 / 422435036 / 454839551 bytes, matching the log line for line).
  `python -m etl.fetch --record-digest` was NOT run for any of the four - nothing was re-downloaded, and no
  digest in this commit was typed from anywhere but that log. `retrieved: 2026-09-19` is the UTC day of the
  download. Nothing outside the gitignored inputs directory holds the .tif files.
