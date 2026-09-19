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
- 2026-09-19T03:20:00Z ACCEPTANCE BLOCK RE-RUN AND RE-QUOTED AT THE FINAL COMMIT (`8a23671`, the only
  commit carrying source; this entry is the second and touches no measured file).
  **Bullet 1, LA TERRAIN - met.** `dem.tile_for` resolves through `dem.tiles_for_region(region_id)`, which is
  `dem.tiles_for_bbox` of the region's own bbox minus `UNSERVED`; the sfbay `TILES` constant is no longer in
  the decision. Quoted from the committed tree:
  ```
  tiles_for_region('la')   = ['n34w118', 'n34w119', 'n35w118', 'n35w119']
  tiles_for_region('sfbay')= ['n37w122', 'n37w123', 'n38w122', 'n38w123', 'n38w124', 'n39w122', 'n39w123', 'n39w124']
  TILES == sfbay derivation: True
  tile_for(34.07,-118.45) la active = n35w119
  tile_for(34.07,-118.45) no region = n35w119
  ```
  The four manifest entries, read back through `etl.manifest.parse` rather than off the diff:
  ```
  3dep-n34w118.tif  sha256  f3b96b70480986170627b6d888be39775353de475e5e6d07823fcfe51869177e  bytes=351919765  retrieved=2026-09-19  by=T-0142
  3dep-n34w119.tif  sha256  d550d73b3884ccf16d9ca30c286c2d205905a4e35292324a2b38726896bd1f00  bytes=77566808   retrieved=2026-09-19  by=T-0142
  3dep-n35w118.tif  sha256  7e660831c5b6a2a6b7ded4215886df8ad393f4303500086880350cd94badf986  bytes=422435036  retrieved=2026-09-19  by=T-0142
  3dep-n35w119.tif  sha256  28fb065b1f33a57bee117377c65558e004488b97d5c61ec4f13c763b9b837afb  bytes=454839551  retrieved=2026-09-19  by=T-0142
  manifest validate_all: []
  ```
  AND THE FOUR DIGESTS WERE VERIFIED AGAINST THE FILES, not merely transcribed - the repo's own verifier,
  run read-only from the main checkout against THIS branch's manifest
  (`python -m etl.fetch --verify-only --manifest <worktree>/services/etl/inputs/manifest.yaml --only 3dep-nXXwYYY.tif`,
  exit 0 four times; `git status` in the main checkout empty afterwards):
  ```
  3dep-n34w118.tif: verified (sha256)   verified 3dep-n34w118.tif bytes=351919765 retrieved=2026-09-19 sha256 ok
  3dep-n34w119.tif: verified (sha256)   verified 3dep-n34w119.tif bytes=77566808 retrieved=2026-09-19 sha256 ok
  3dep-n35w118.tif: verified (sha256)   verified 3dep-n35w118.tif bytes=422435036 retrieved=2026-09-19 sha256 ok
  3dep-n35w119.tif: verified (sha256)   verified 3dep-n35w119.tif bytes=454839551 retrieved=2026-09-19 sha256 ok
  ```
  The sfbay eight are untouched: `test_the_sfbay_eight_are_untouched` asserts each is still present,
  64-hex and `consumed_by: T-0026`, and the manifest diff is four added entries plus one comment block.
  **Bullet 2, region.json - met.** `_comment_bbox` now says the box TAKES IN northern Orange County, names
  Anaheim and Santa Ana with the coordinates the reviewer measured and the other six cities by name, and
  its EXCLUDES sentence no longer claims the county. `_comment_counties` names Orange as a clipped
  neighbour that is not a sliver. `_comment_dem` no longer says the tiles are unpinned. Red first, by name
  (`test_the_bbox_comment_does_not_claim_to_exclude_cities_the_box_contains`, quoted verbatim in the
  03:06 entry), green now.
  **Bullet 3, the counts - met by not moving.** The bbox did NOT move, so no re-record is owed. Proven
  rather than asserted: `git diff 6d6e2e7 HEAD -- services/etl/regions/la/region.json` filtered to lines
  that are not `_comment` is EMPTY - `bbox`, `counts` and `counts_from` are byte-identical to origin/main.
  The DEM tile list re-derived by `dem.tiles_for_bbox` is quoted above (the four).
  Gates at this commit, run bare:
  ```
  cd services/etl && python -m pytest tests -rs   ->  1042 passed in 132.43s (0:02:12)   SUITE_EXIT=0   (skipped=0)
  bash ops/lib/check-line-cap  ->  P-SRC-02: 71 Swift files tracked (Sources=26, Tests=37, apps/ios=8), none over 300 lines   LINECAP_EXIT=0
  bash ops/queue-check         ->  QUEUE OK (179 tasks)                                  QUEUECHECK_EXIT=0
  bash ops/check-pins --source-only -> PINS ok=12 skipped=13 pending=1 expired=0 failed=0 tier=linux source-only  PINS_EXIT=0
  wc -l: services/etl/etl/dem.py 258 | services/etl/tests/test_dem_tiles.py 206 | services/etl/inputs/manifest.yaml 241 | services/etl/regions/la/region.json 45
  ```
  `ops/test` and full `ops/check-pins` were NOT run here (other authors hold other worktrees on this box;
  the orchestrator's instruction). The ETL suite ran on the Windows checkout, not in the pinned image -
  `tests/test_manifest.py`'s two attribution guards skip inside the container and did not skip here.
- 2026-09-19T03:21:00Z STILL OPEN, in the order they matter.
  **1. FOR THE HUMAN - the commute question, unchanged and now the only thing holding the bbox.** Does the
  owner's drive cross -117.85 (east, past Angeles Crest's far end into San Bernardino) or 33.70 (south, past
  Palos Verdes)? Until that is answered the south-east corner stays where the counts were measured, and the
  file now SAYS it holds Anaheim, Santa Ana, Fullerton, Buena Park, Garden Grove, Westminster, Seal Beach
  and La Habra instead of claiming it excludes them. If the answer moves the box: re-run the extract for the
  counts (`counts_from` will refuse the old ones), and re-derive the tiles - cutting east of -118.0 or north
  of 34.0 would drop `n34w118`, and `tiles_for_region` will do that automatically while the manifest entry
  stays, which is harmless but worth noticing.
  **2. "LA has terrain" means the tile resolution and the pinned inputs, NOT a sampled elevation.** Nothing
  has read a GeoTIFF for LA: `gdallocationinfo` lives in the pinned ETL image, the .tif files are in the
  gitignored inputs directory of the main checkout only (see [[T-0177]]), and no pipeline calls
  `dem.sample*` yet. What this task can honestly claim is that the four tiles are pinned and verifiable and
  that every LA point now RESOLVES to one. The first real LA elevation number is T-0168's.
  **3. No production caller passes `tiles=` because there is no production caller (R1).** When T-0168 wires
  the clip it should pass `tiles=dem.tiles_for_region("la")` to mean "this region only"; if it forgets, the
  default is every region we serve, so LA still gets its terrain - that is R2's whole point, not an excuse
  to forget.
  **4. Finding 2 of PR #68's review is NOT closed** (R7): `counts_from.source` still reads
  `california-osm.pbf`, which is the manifest's own name for the file whose url is `california-latest.osm.pbf`.
  Making `CountsFrom.problems()` require a source the manifest knows is a validator change that every region
  load runs through and wants its own red test; it needs its own task.
  **5. `dem.py` has no mutation population under `ops/mutate/`** (R8), and `ops/mutate/` is outside this
  task's `touches:`. The module predates the rule; the functions added here are set arithmetic rather than
  scoring, but the boundary cases (`<` versus `<=` on a bbox edge, ceil versus floor in the tile name) are
  exactly what a population would catch and `tests/test_dem_tiles.py` currently catches by hand.
  **6. Untouched from the Brief's "also on the record"**: no `curated.yaml` for la, `ops/sane` code 4 still
  cannot run for la (no `work/la/meta.json` on this box), and `.artifacts/record-provenance.py` is still
  gitignored.
- 2026-09-19T03:55:04Z REVIEW **FAIL** (round 1) by agent/rv1-pr106 on PR #106 at `3f9a220`. Reviewed in a
  detached worktree at that sha and removed it; nothing written to `.worktrees/T-0142`, nothing pushed, the
  task file untouched.
  **Every quoted number re-run and TRUE.** `tests/test_dem_tiles.py -rs` -> 17 passed; whole suite
  `python -m pytest tests -rs` -> `1042 passed in 98.10s`, exit 0, `grep -c SKIPPED` = 0;
  `wc -l` -> 258 / 206 / 241 / 45, exactly as quoted; `bash ops/lib/check-line-cap` -> `P-SRC-02: 71 Swift
  files tracked ... none over 300 lines`, exit 0; `bash ops/queue-check` -> `QUEUE OK (179 tasks)`, exit 0;
  `tiles_for_region('la')` = the four, `tiles_for_region('sfbay') == TILES` True, `tile_for(34.07,-118.45)`
  = `n35w119` with la active and with no region. `git diff origin/main -- regions/la/region.json` changes
  three keys and all three are `_comment_` — R4 holds, the box did not move. Two typed values re-done from
  scratch: the four LA tiles re-derived BY HAND from the bbox corners' ceils (rows [34,35] x columns
  [118,119]) and equal to `tiles_for_region('la')`; and `sha256sum services/etl/inputs/3dep-n34w119.tif` =
  `d550d73b3884ccf16d9ca30c286c2d205905a4e35292324a2b38726896bd1f00` with 77566808 bytes, identical to the
  manifest entry. R1 verified at this head: outside dem.py and its tests the only hit is `landcover.py`'s own
  unrelated `tile_for`, and `terrain.py` imports `math` and `.curvature` only — the sampler has no production
  caller, so the seam was indeed decided rather than discovered, and the chosen one is right for T-0168.
  R1-R8 all agreed; no ruling disputed.
  **BLOCKING B1 - the LA active tile set is unpinned, so a check this PR adds can pass over nothing.**
  `test_the_manifest_pins_every_tile_la_needs` puts its whole body inside
  `for tile in sorted(dem.tiles_for_region("la")):`, so its scope is the value under test: shrink that set and
  it iterates fewer and passes; empty it and it iterates zero and passes. Acceptance bullet 1 names four
  literal tiles; the check that carries it names none. `test_la_needs_exactly_four_tiles` pins
  `tiles_for_bbox(*LA)` — the arithmetic BEFORE `- UNSERVED`, against a bbox typed in the test rather than read
  from region.json. sfbay's active set is pinned by equality (`tiles_for_region("sfbay") == TILES`); la's is
  not pinned at all. Reproduction, run twice and restored: change `UNSERVED` (dem.py:39) to
  `frozenset({"n37w124", "n35w118"})` -> `python -m pytest tests -q` exits 0 with ZERO failures, while
  `tiles_for_region('la')` = `['n34w118','n34w119','n35w119']` and
  `tile_for(34.35,-117.86, tiles=tiles_for_region('la'))` = `None` — Angeles Crest east of Red Box, the roads
  the bbox reaches -117.85 expressly to include, silently without elevation. This is the gap the pre-review
  mutant pass named ("the eastern column's presence is pinned only at the derivation level") and the 03:20 /
  03:21 entries do not answer it; CLAUDE.md's author rule asks for the verifier's findings closed before the
  review is bought. Fix is two lines in a file this PR owns:
  `assert dem.tiles_for_region("la") == {"n34w118","n34w119","n35w118","n35w119"}` and a `tile_for`-level
  assertion for an eastern point (`dem.tile_for(34.35,-117.86, tiles=dem.tiles_for_region("la")) == "n35w118"`,
  verified to hold at this head) — both demonstrated red with the one-line `UNSERVED` widening, then green.
  Two further mutants of mine were CAUGHT and are recorded as evidence the rest of the seam is pinned:
  `tile_for` re-consulting `TILES` fails three tests (`..._westwood_point...`, `..._naming_no_region...`,
  `..._grouping_and_sampling...`); `tiles_for_bbox`'s far edges `<` -> `<=` fails
  `test_a_bbox_touching_a_border_does_not_claim_the_next_square` and — worth knowing — changes NEITHER the la
  nor the sfbay derived set, because neither bbox has an integer far edge, so that synthetic border test
  carries the whole class alone.
  **R2 judged against the absence-vs-wrong-region question and UPHELD.** `tile_for(37.78,-122.42)` with no
  `tiles=` returns `n38w123` where `tiles=tiles_for_region('la')` returns `None`, but a 3DEP tile is a global
  grid square picked from the point's own lat/lon, so the union default can return a right value where a
  region-scoped call would return absence — never a wrong one. Against main it is strictly better. Recordable
  consequence only: the old implicit "not in my region" signal is gone, so T-0168 must pass
  `tiles=dem.tiles_for_region("la")` rather than rely on the default.
  **RECORDABLE**: `served_tiles`' cache is never invalidated — demonstrated stale across a regions/ change on
  a tmp root while `region_ids` already saw the new region — and nothing pins its behaviour; the new import
  `from collections.abc import Collection, Iterable` (dem.py:17) leaves `Iterable` unused and no lint config
  catches it; `tile_for`'s default branch takes no `root`, so it can only be exercised against the live
  regions/ tree; the manifest test checks 64-hex, not bytes (right call — the .tif files are gitignored — but
  a pointer to `python -m etl.fetch --verify-only` in the manifest comment would save the next reviewer a hop).
  Disclosed gaps in STILL OPEN were confirmed and are NOT counted against the PR: nothing has sampled an LA
  GeoTIFF, finding 2 deferred per R7, no `ops/mutate/` population per R8, the commute question still FOR THE
  HUMAN. CI at this sha: `core` pass 2m1s, `pins-source-only` pass 57s.
- 2026-09-19T04:30:00Z FIX for B1 (review round 1) by agent/claude-opus-5 acting for the owner, in
  `.worktrees/T-0142` on `task/T-0142`, PR #106. B1 accepted as stated, not argued; both recordables taken.
  **REPRODUCED FIRST, and it is exactly what the review says it is.** `UNSERVED` (dem.py:39) widened to
  `frozenset({"n37w124", "n35w118"})`, nothing else touched, `__pycache__` purged: the whole ETL suite
  `python -m pytest tests -rs` exits 0 with every test a dot and not one F, and
  `tests/test_dem_tiles.py -rs` -> `17 passed in 0.23s`, green. At that same moment
  `tiles_for_region('la')` = `['n34w118','n34w119','n35w119']` — three — and
  `tile_for(34.35,-117.86, tiles=tiles_for_region('la'))` = `None`: Angeles Crest east of Red Box, the
  reason the box reaches -117.85 at all, with no elevation and nothing red anywhere. Mutant restored by
  writing the original bytes back; `md5sum services/etl/etl/dem.py` = `8c6e7b50c1564d8495a8c6b7c6437c08`,
  the pre-mutation digest, and `git status --porcelain` empty before any fix was written.
  **WHAT CHANGED** — tests first, then two small code changes; only `services/etl/etl/dem.py` and
  `services/etl/tests/test_dem_tiles.py`.
  1. `LA_TILES = {"n34w118","n34w119","n35w118","n35w119"}`, typed in the test file, and
     `test_the_la_active_tile_set_is_exactly_the_four_typed_tiles` asserting
     `dem.tiles_for_region("la") == LA_TILES` — the equality sfbay already had and LA had nowhere.
  2. `test_every_la_tile_carries_a_point_the_region_exists_for`: one point per square, each asserted inside
     the recorded bbox and asserted to resolve to its own tile with la active —
     n35w118 (34.35,-117.86) Angeles Crest Highway (SR-2) east of Red Box, toward Dawson Saddle;
     n35w119 (34.1289,-118.4043) Mulholland Drive at Coldwater Canyon;
     n34w119 (33.7445,-118.3870) the Palos Verdes peninsula, which Palos Verdes Drive rings;
     n34w118 (33.8366,-117.9143) Anaheim — honestly a CITY point and not a road: nothing in this tree
     records a road coordinate in that square, and inventing one to dress the test up is the exact move
     `OC_CITIES_INSIDE_THE_BOX` already refuses. The other three coordinates are already recorded here
     (`test_the_la_bbox_covers_ucla_and_the_santa_monicas`, the OC cities); the first is the point the
     review names. The test also pins one witness per tile and no more, so a name cannot enter `LA_TILES`
     without a point standing on it.
  3. `test_the_manifest_pins_every_tile_la_needs` now iterates `sorted(LA_TILES)`, not
     `sorted(dem.tiles_for_region("la"))`: its scope is no longer the value under test. It stays green under
     the `UNSERVED` mutant, correctly — it pins four manifest entries; the active set is pinned by (1).
  4. R1 taken rather than dropped: `dem._cache_key(root)` is the resolved root plus
     `(region_id, region.json st_mtime_ns)` for every region, and `served_tiles` keys `_SERVED_CACHE` on it.
     Cost is one `stat` per region per call — bounded by the number of regions, not by the number of points,
     so `group_by_tile`'s per-point pattern is unaffected and the reason the cache exists survives.
     `test_served_tiles_notices_a_region_added_after_its_first_call` writes one region into a tmp root, asks,
     writes a second, asks again, and also asserts `region_ids` saw it — on the Dakota plains (n45w101,
     n45w100) deliberately, so a mutant on `UNSERVED` or on the la bbox cannot move this check's answer.
  5. R2 taken: `Iterable` dropped from the `collections.abc` import; `Collection` is the only one used.
  **RED BY NAME, THEN GREEN.** `__pycache__` purged before every run, 1.2 s before every restore, every
  mutant restored by writing the original bytes back and the digest checked:
  ```
  MUTANT A (the review's)  dem.py:39  UNSERVED: frozenset({"n37w124"}) -> frozenset({"n37w124","n35w118"})
    .........FFF...  ->  exactly two, by name:
    FAILED tests/test_dem_tiles.py::test_the_la_active_tile_set_is_exactly_the_four_typed_tiles
    FAILED tests/test_dem_tiles.py::test_every_la_tile_carries_a_point_the_region_exists_for
    E AssertionError: Angeles Crest Highway (SR-2) east of Red Box, toward Dawson Saddle (34.35,-117.86)
      has no elevation: n35w118 is not in LA's active set
      assert None == 'n35w118'  where None = dem.tile_for(34.35, -117.86,
      tiles=frozenset({'n34w118', 'n34w119', 'n35w119'}))
  MUTANT B (mine, a neighbour)  dem.py  tiles_for_region: `tiles_for_bbox(...) - UNSERVED`
                                                       -> `UNSERVED - tiles_for_bbox(...)`
    .........FFFFFFFF...  ->  eight, by name: test_a_westwood_point_resolves_to_its_tile_when_la_is_active,
    test_the_la_active_tile_set_is_exactly_the_four_typed_tiles,
    test_every_la_tile_carries_a_point_the_region_exists_for,
    test_served_tiles_notices_a_region_added_after_its_first_call,
    test_the_sfbay_golden_set_is_exactly_what_the_derivation_serves,
    test_naming_no_region_no_longer_means_sfbay, test_absence_is_still_absence_outside_the_active_region,
    test_grouping_and_sampling_carry_the_active_region_through
  AT HEAD, both restored:  20 passed in 0.38s  (17 before this round)
  md5sum services/etl/etl/dem.py = 08792c47510738334c458ce703b20d68 (the fixed file, stable across both
  restores; 8c6e7b50c1564d8495a8c6b7c6437c08 was the pre-fix file each mutant was restored to)
  ```
  **Ruling, recorded rather than run:** the other neighbour the instruction offered — `tiles_for_region`
  subtracting `UNSERVED` TWICE — is an EQUIVALENT mutant, because set difference is idempotent
  (`(S - U) - U == S - U`); it cannot be shown red by any test and is not claimed as one caught. The
  wrong-side subtraction above is the non-equivalent neighbour and is the one demonstrated.
  **ACCEPTANCE BLOCK, whole, re-run at the final commit content** (this entry included; the only file that
  changed after the suite ran is this task file, and `ops/queue-check` re-ran over it):
  ```
  cd services/etl && python -m pytest tests -rs  ->  1045 passed in 120.27s (0:02:00)  SUITE_EXIT=0  (skipped=0)
  bash ops/lib/check-line-cap  ->  P-SRC-02: 71 Swift files tracked (Sources=26, Tests=37, apps/ios=8), none over 300 lines   LINECAP_EXIT=0
  bash ops/queue-check         ->  QUEUE OK (179 tasks)                                  QUEUECHECK_EXIT=0
  bash ops/check-pins --source-only -> PINS ok=12 skipped=13 pending=1 expired=0 failed=0 tier=linux source-only  PINS_EXIT=0
  wc -l: services/etl/etl/dem.py 273 | services/etl/tests/test_dem_tiles.py 280 | services/etl/inputs/manifest.yaml 241 | services/etl/regions/la/region.json 45
  ```
  The same block run once before this entry was appended gave the same numbers - 1045, zero skips, four
  exit 0s, the same four `wc -l` counts - at 106.56s wall; the only difference between the two runs is
  elapsed time, and the quoted run is the later one, over the tree this commit contains.
  1042 -> 1045 is the three new checks and nothing else; 258 -> 273 and 206 -> 280 are this round's edits,
  both files still under the 300-line cap, so no second test file was needed. `ops/test` and full
  `ops/check-pins` were NOT run here, same as the previous entry and for the same reason (other authors hold
  other worktrees on this box; the orchestrator's instruction). The ETL suite ran on the Windows checkout,
  not in the pinned image.
  **Derivation, re-quoted at this head:**
  ```
  tiles_for_bbox(*LA) = ['n34w118','n34w119','n35w118','n35w119']      UNSERVED = ['n37w124']
  tiles_for_region('la') = the same four, == the typed LA_TILES literals: True
  tiles_for_region('sfbay') == dem.TILES: True          served_tiles() with no region = 12 tiles
  tile_for with la active: (34.35,-117.86) -> n35w118    (34.1289,-118.4043) -> n35w119
                           (33.7445,-118.3870) -> n34w119  (33.8366,-117.9143) -> n34w118
  ```
  **STILL OPEN after this round.**
  1. FOR THE HUMAN, unchanged and still the only thing holding the bbox: does the owner's drive cross
     -117.85 east or 33.70 south? If the answer moves the box, the counts are re-recorded from a new extract
     and the four tiles are re-derived; `LA_TILES` and `LA_POINT_PER_TILE` are then edited WITH the box, by
     hand, on purpose — that is the cost of typing them and it is the point of typing them.
  2. "LA has terrain" still means tile resolution and pinned inputs, NOT a sampled elevation: nothing has
     read an LA GeoTIFF, and the first real LA elevation number is T-0168's.
  3. T-0168 must pass `tiles=dem.tiles_for_region("la")` to mean "this region only" (the review's R2
     consequence); the union default will otherwise answer for every region we serve.
  4. NOT taken this round, deliberately: the reviewer's two remaining recordables — `tile_for`'s default
     branch takes no `root`, so it can still only be exercised against the live regions/ tree (a signature
     change with callers, not a log line), and the manifest comment has no pointer to
     `python -m etl.fetch --verify-only` (re-touching `inputs/manifest.yaml` would re-measure a file this
     block already quotes, for a comment). Both belong in T-0168's neighbourhood; neither is load-bearing.
  5. Unchanged from 03:21: finding 2 of PR #68 (R7, `counts_from.source` naming `california-osm.pbf`) is
     still open and wants its own task; `dem.py` still has no `ops/mutate/` population (R8) and `ops/mutate/`
     is outside this task's `touches:` — the two mutants above were run by hand and are recorded, not
     populated; no `curated.yaml` for la; `ops/sane` code 4 still cannot run for la on this box.
- 2026-09-19T04:42:05Z **Record corrections from the mutant pass on the round-2 fix (27db1d7), closed before the review is
  bought - agent/claude-fable-5-1 (orchestrator), for the owner. The pass re-applied rv1-pr106's B1 on a copy
  (two red by name, the manifest test green as predicted), added two of its own (tiles_for_region returning the
  sfbay set for 'la': six red by name; tile_for ignoring its tiles argument: two red by name), found 1045 passed /
  zero skips, every wc -l and both digests as quoted, and the tree clean at 27db1d7 == PR head; zero survivors.
  Three items are text.** (a) "the reviewer's log entry appended verbatim" is unverifiable from the tree alone;
  the orchestrator holds the entry as the review workflow returned it and compared the two byte for byte:
  56 lines, present verbatim in this file.
  (b) The fixer's own second mutant (the subtraction on the wrong side, eight red by name) was not re-run by the
  pass; it rests on the fixer's run. (c) The wall-clock figures (120.27 s / 106.56 s) were not reproduced; the
  counts were. Nothing else moved.
