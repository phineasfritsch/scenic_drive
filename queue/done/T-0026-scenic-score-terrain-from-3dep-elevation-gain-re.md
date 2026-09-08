---
id: T-0026
title: Scenic score: terrain from 3DEP (elevation gain, relief) with a smoothing pass
state: done
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
- 2026-09-07T18:20Z First sample against the REAL tiles, and it found a flaw in my fixture method
  rather than in the arithmetic. Three hand-typed polylines, sampled through the pinned image:

      alviso         length 522.7 m   gain 2.9 m    gain/km   5.64   relief 4.4 m    max grade  3.81%
      old_la_honda   length 5269.1 m  gain 584.9 m  gain/km 111.01   relief 213.9 m  max grade 44.14%
      skyline        length 4663.0 m  gain 529.0 m  gain/km 113.45   relief 174.7 m  max grade 58.98%

  The steep ones read as steep and the flat one is nearly flat, so the arithmetic is doing something sane.
  Two things are wrong anyway, and both are mine:

  1. MAX GRADE 44% AND 59% ARE IMPOSSIBLE. No drivable road is that steep - Old La Honda averages about 8%
     and tops out near 12%. The cause is the fixture, not the sampler: I typed seven points for a 5.3 km
     mountain road, so the resampler interpolates in straight lines that cut across canyons the road actually
     contours around. The elevations are real; they are just not elevations of the road. `sanity_problems`
     already flags anything over 60%, which is why Skyline at 58.98% is sitting one point under a guard that
     would have caught it - the guard is right and the input is wrong.

  2. ALVISO SCORES 5.64 m/km, JUST OVER the 5.0 threshold `is_flat` uses. 2.9 m of gain over 523 m of bay
     margin is still noise, not climb. Whether the answer is a slightly higher threshold, a larger noise
     floor, or better geometry cannot be decided while the geometry is wrong - tuning the threshold now would
     be fitting the constant to a bad fixture, which is exactly how a scoring system gets quietly wrong.

  So the fixtures must come from REAL OSM way geometry rather than hand-typed points. The Bay Area extract
  from T-0024 already has it, with nodes every 20-50 m on a winding road, which is the whole point: the road
  follows the contour and a straight line between two points 800 m apart does not.

  NEXT STEP, deliberately not done blind: pull the actual ways for Old La Honda Road, a flat Alviso street
  and a Skyline segment out of the extract by name, commit them as a geometry fixture the way T-0025 commits
  its oracle ways, and only then decide whether the flat threshold or the noise floor needs to move. The
  arithmetic and the sampler are already tested against mutation (5 and 6 mutations respectively); what is
  missing is a fixture that is a road.

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

- 2026-09-07T18:40Z Handing to agent/reviewer-31; state -> review. What is here:

  **The eight tiles**, pinned by sha256 in the manifest, 2,278,440,685 bytes, each downloaded and hashed.
  The brief listed four; the four were real but had been verified against their URLs and never against the
  bbox, so Sonoma, Napa, Solano and the outer coast were missing. n37w124 is deliberately absent - entirely
  ocean, USGS returns 404 - and a point with no tile reads as "no elevation", never 0 m, which is sea level.

  **etl/terrain.py**: 3x3 smoothing, resampling to a fixed 25 m step, gain, gain/km, relief over a 1 km
  window, steepest sustained grade, coverage, and a sanity check for physical impossibilities. 37 tests, then
  five mutations to prove they fire. One of them - relief over the whole way instead of a window - caught
  NOTHING, because my two test profiles climbed 599.6 m and 600 m and the assertion held either way. Fixed so
  they climb exactly the same 600 m, with an explicit assertion that the totals match.

  **etl/dem.py**: tile arithmetic, nodata handling and the gdallocationinfo call, split so the impure part is
  one subprocess per tile and injectable. 41 tests, then six mutations; floor-instead-of-ceil fails 12 of
  them, which is the one that matters - an off-by-one tile name returns a REAL elevation from the wrong
  square, so a whole region gets plausible terrain belonging somewhere else.

  **The brief's RED, on real roads and real elevation:**

      old_la_honda  way 8940690    259 nodes  5110 m  418 m gain  81.8 m/km  max grade 13.65%  STEEP
      skyline       way 239028846  428 nodes  7014 m  362 m gain  51.6 m/km  max grade 10.47%  STEEP
      alviso_flat   way 92357845    13 nodes   221 m    0 m gain   0.0 m/km  max grade  0.19%  FLAT
      alviso_flat2  way 8929268     11 nodes   264 m  0.6 m gain   2.1 m/km  max grade  1.02%  FLAT

  Two things went wrong on the way here and both are worth the reviewer's attention:

  1. The first fixtures were hand-typed polylines - seven points for a 5.3 km mountain road - and scored Old
     La Honda at a 44% maximum grade and Skyline at 59%. No drivable road is close. Straight lines between
     points 800 m apart cut across canyons the road contours around; the elevations were real, they were not
     elevations OF THE ROAD. The fixtures now use the mappers' own nodes, and a test asserts node spacing
     under 120 m so nobody can quietly substitute a typed line again.
  2. Alviso scored 5.64 m/km against the 5.0 `is_flat` threshold on the bad geometry. I did not move the
     threshold. With real geometry it scores 0.0, so the constant would have been fitted to a road that does
     not exist.

  And one thing I had simply not done: `terrain.smooth3x3` was written and tested and then never used - the
  sampling path read raw cells and the noise floor was doing the whole job. `dem.sample_smoothed` now applies
  it, nine positions per point in one stream per tile, with the east-west offset divided by cos(latitude) so
  the neighbourhood is square on the ground rather than in degrees.

  **What the reviewer should attack first**, in the order I would:

  - The tile arithmetic. `tile_for` is the single point where a plausible wrong answer is possible. Check the
    boundary cases against the actual tile extents rather than against my tests, which I wrote.
  - The fixture's provenance. Both the geometry and the profile are committed. Confirm the profile really
    came from the pinned tiles by resampling a way yourself in the image, and confirm the recorded summary is
    what the recorded profile produces (there is a test, but it failed on first run over a tenth of a metre
    because the summary was computed before the profile was rounded - the class of thing worth re-checking).
  - Whether 0.5 m is the right noise floor and 5.0 m/km the right flat threshold. Both are judgement, both
    are now measured against real roads, and neither has been argued by anyone but me.
  - `sample_smoothed` sends 9x the rows. Check that a way of a few thousand points does not exceed any
    argument or stdin limit, because the failure mode there would be a truncated read - and `parse_values`
    raises on a count mismatch, so confirm that guard actually catches it rather than assuming.

  Not done, deliberately: nothing writes these numbers into the corpus yet. That is T-0030's job, and the
  scoring composition is T-0029's.

- 2026-09-07T20:15Z agent/reviewer-31, PASS. Attacked the priority list in order, re-deriving against
  primary sources rather than the owner's own tests wherever that was possible. What was re-derived vs.
  taken on trust, item by item:

  **1. `dem.tile_for` (services/etl/etl/dem.py:38-48).** RE-DERIVED, not trusted. Ran
  `gdalinfo` inside the pinned `scenic-etl` image on all 8 pinned tiles (n37/n38/n39 x w122/w123/w124).
  Every tile's Upper-Left corner is (ceil(lat), -ceil(|lon|)) to within a 2" seam buffer, e.g. n38w123's
  actual extent is lat [36.9994, 38.0006] lon [-123.0006, -121.9994] - confirming ceil-of-lat /
  ceil-of-abs-lon against the real files, not the owner's assertions about them. Then swept boundary
  cases programmatically (`tests/fixtures` not involved): exactly on a whole degree, epsilon inside/
  outside, region edges, the n37w124 ocean gap, NaN, negative latitude, positive longitude, and both
  sides of the antimeridian. All correct for the region this pipeline actually serves, with one finding:

  MEDIUM, not blocking - `dem.tile_for` builds its name as `f"n{ceil(lat)}w{ceil(abs(lon))}"` with no
  check on the SIGN of lat/lon, only on magnitude. `dem.tile_for(38.0, 122.5)` (122.5°E, e.g. coastal
  China) returns `'n38w123'` - the Bay Area's own peninsula tile - instead of `None`. That is exactly the
  "plausible wrong answer" failure class item 1 warns about, just triggered by hemisphere confusion
  instead of an index off-by-one: a positive longitude would silently draw a real elevation out of the
  wrong hemisphere's tile rather than failing safe. It is not reachable today - `california-latest.osm.pbf`
  extracted to the sfbay bbox (`services/etl/regions/sfbay/region.json`, lon -123.62..-121.55) can never
  hand `tile_for` a positive longitude, and `TILES` (dem.py:25-29) only contains 8 "n..w.." names so no
  other coincidental collision is possible - so this does not block the task. It is untested (no case in
  `TestTileForAPoint` exercises sign), and worth a line in a future region-expansion task. Negative
  latitude fails safe today too, but by accident (`f"n{-37:02d}"` produces a name absent from `TILES`),
  not by validation.

  **2. Fixture provenance (`tests/fixtures/terrain_fixture.json`).** RE-DERIVED for all 4 ways, not 1.
  Pulled every way (8940690, 239028846, 92357845, 8929268) live from `api.openstreetmap.org/api/0.6/way/
  <id>/full` (network available in this environment) and diffed the ordered node coordinate list against
  the committed `coords` array: EXACT match, all 4 ways, node-for-node. Then, independently of the
  owner's own build path, resampled each way's committed geometry with `terrain.resample` and re-sampled
  elevation through `dem.sample_smoothed` against the real pinned tiles inside the `scenic-etl` container
  (not a mock runner): the reproduced profile matched the committed `profile` array exactly (post-rounding)
  for all 4 ways, and feeding that reproduced profile through `terrain.summarise` reproduced the committed
  `recorded_summary` exactly for all 4. This independently confirms both halves of item 2 - the profile
  really came from the pinned tiles, and the recorded summary really is what the recorded profile
  produces - without relying on `TestTheRecordedSummariesStillHold` (tests/test_terrain_fixture.py:88-93),
  which I also ran and which also passes. Also independently confirmed the USGS `n37w124` URL is a live
  404 (curl'd it directly), and that the 8 tiles' sha256 in `services/etl/inputs/manifest.yaml` match
  `sha256sum` on the local 2.28 GB files byte for byte.

  **3a. Real mapper geometry (not typed lines).** RE-DERIVED via the same live-OSM fetch above - not just
  the node-spacing test. Node ids exist in OSM, node order and coordinates match exactly.

  **3b. `is_flat` threshold never tuned.** RE-DERIVED via `git log --oneline -- services/etl/etl/
  terrain.py`: exactly one commit (c9d0db6) has ever touched that file, and it is the commit that
  introduced `gain_per_km_threshold: float = 5.0` (terrain.py:177). No later commit touches the file, so
  the constant cannot have been moved after the Alviso-at-5.64 scare the log describes. Confirmed true.

  **4. `sample_smoothed` row volume.** RE-DERIVED, not assumed. Built a synthetic 4000-point way (all
  inside one tile) and ran it through the real `dem.sample()` and `dem.sample_smoothed()` (36,000 stdin
  lines for the smoothed call) inside the container: both returned in under a second with exactly the
  expected count, no truncation - `subprocess.run(input=...)` uses `communicate()` internally so this
  never hits an ARG_MAX-style ceiling, only ordinary pipe throughput. Then constructed an actual truncated
  read (a runner that halves `gdallocationinfo`'s stdout before returning it) and confirmed
  `parse_values`'s count-mismatch guard (dem.py:86-87) really raises `ValueError` on it, rather than
  assuming the guard fires because the code looks like it should.

  **5. Constants.** `SAMPLE_STEP_M=25.0` and `RELIEF_WINDOW_M=1000.0` are not the
  owner's judgment at all - they are lifted straight from the brief's own spec, not fitted to anything.
  `NOISE_FLOOR_M=0.5` and `is_flat`'s `5.0` m/km both predate the mapper-geometry fixture fix (single
  commit, confirmed in 3b) and were never adjusted afterward, so neither is fitted post-hoc to make the
  fixture pass - and with real geometry the two fixture classes land 16-40x apart (`gain_per_km`
  2.08/81.81/51.61 vs. the 5.0 boundary), comfortable margin rather than a threshold balanced on the
  fixture. The one I would argue with is `NOISE_FLOOR_M`: dem.py's own docstring cites "~1 m RMSE in open
  terrain" for raw 3DEP noise, and 0.5 m is exactly half of that with no stated justification tying it to
  the *smoothed* (3x3-averaged) noise floor specifically, which is what it is actually applied to via
  `elevation_gain`'s default. It happens to work on both real fixtures here, but the number's derivation
  is asserted, not shown. `sanity_problems`' 60% grade ceiling (terrain.py:200) is a domain constant with
  real headroom above both drivable-road reality and the fixtures (13.65%/10.47%), not fixture-fitted.

  **6. Smoothing coverage.** Confirmed `dem.sample_smoothed` is what actually built the committed fixture
  (re-derivation in item 2 used it, not the owner's word). Additionally constructed a point whose 3x3
  neighbourhood straddles the n38w123/n39w123 boundary (`dem.neighbourhood` + `dem.tile_for` on a synthetic
  point at lat=38.00002) and confirmed `sample_smoothed` correctly drew from both real tile files and
  returned a sane blended value (175.5 m smoothed vs. 176.1 m raw) rather than silently using only one
  tile or crashing - the item-1/item-6 interaction is exercised, not just each in isolation. One
  observation, not a defect in what's shipped: `terrain.smooth3x3` (terrain.py:33-56) has zero callers
  outside its own tests anywhere in the tree (`grep -rn smooth3x3` outside tests/ only finds it defined
  and mentioned in `dem.sample_smoothed`'s docstring) - `dem.sample_smoothed` reimplements equivalent
  averaging for scattered points rather than calling it, which the docstring explains is because a grid
  op and a point-cloud op are genuinely different code. Also: `dem.sample()` (unsmoothed) remains public
  with the same signature as `sample_smoothed`, and nothing structurally stops a future integration
  (T-0030, not yet written) from calling the wrong one and reintroducing the exact Alviso phantom-gain bug
  this task already found and fixed once (commit e0166e7). Worth a note for T-0030's own review, not a
  reason to fail this one - there is no caller of either function outside tests yet (`grep` confirms), so
  nothing in this diff currently exercises the gap.

  **Also found, unprompted:** `tests/test_terrain_fixture.py:14`'s module docstring still reads "the same
  roads score 14.6% and 8.3%" - those are the PRE-smoothing numbers from commit 68c193d. Commit e0166e7
  ("actually apply the 3x3 smoothing") re-recorded the fixture to 13.65%/10.47% (confirmed live in the
  committed JSON and reproduced independently above) but never touched the docstring 8 lines above the
  import. LOW - nothing asserts the stale string, but it actively misleads a reader about what the
  committed fixture demonstrates.

  **Verification commands, exact output** (fresh `npm ci` in this worktree's `services/api/` first):

      $ cd services/etl && python -m pytest -q tests/
      (ran via `docker run --rm -v "$PWD:/w" -w /w/services/etl scenic-etl python3 -m pytest tests/`
       since this box's own python3 has no pytest installed)
      232 passed, 1 skipped in 4.11s
      (the 1 skip is tests/test_manifest.py:47, "git is not installed here" inside the container -
       environmental, unrelated to this diff, pre-existing)

      $ bash ops/test
      TESTS linux=283/76 ios=skipped failed=0 skipped=0
      OK

      $ bash ops/check-pins
      PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux

      $ bash ops/check-pins --source-only
      PINS ok=3 skipped=9 pending=1 expired=0 failed=0 tier=linux source-only

      $ bash ops/queue-check
      QUEUE OK (50 tasks)

      $ bash ops/sane
      SANE OK

  All green, exit 0 on every command. GitHub Actions on PR #32 is red only because of the account's
  billing block ("recent account payments have failed"), not this diff - not treated as this diff's
  problem, per instruction.

  **Verdict: PASS.** The tile arithmetic is correct for every case this pipeline can actually produce,
  verified against real tile files rather than the owner's tests. The fixture's provenance is genuine on
  both axes (OSM geometry and 3DEP elevation), independently reproduced end to end for all 4 ways, not
  spot-checked on one. Both claimed corrections check out against git history. The 9x row volume has no
  practical ceiling and its truncation guard actually fires. No constant looks filed down to fit these
  fixtures. Findings above (hemisphere-blind `tile_for`, stale docstring, no structural guard against a
  future unsmoothed call) are real but none touch code this task's own claims depend on, and none are
  reachable by anything this diff wires up today.
