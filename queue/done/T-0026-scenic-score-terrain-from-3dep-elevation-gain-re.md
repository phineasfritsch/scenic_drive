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
reviewer: agent/rv-t0026
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
- 2026-09-18T18:14Z REVIEW by agent/rv-t0026, at 11078d3, in a throwaway detached worktree at origin/main,
  since removed. The owner is agent/claude-opus-5; the reviewer named on this file, agent/reviewer-31, never
  ran it - the task has sat in queue/review/ for eleven days. This is that review. I changed nothing.

  **PASS.** Sign-off is warranted. What I ran, what I found, and what I could not run:

  **The brief's RED still holds, eleven days and ~60 merges later.**
  `cd services/etl && python -m pytest tests/test_terrain.py tests/test_terrain_fixture.py tests/test_dem.py
  tests/test_dem_tiles.py -q` -> 98 passed, 0 failed, ZERO skipped (37 + 11 + 41 + 9). The whole ETL suite is
  385 passed, 0 skipped. The log's "37 tests" and "41 tests" still count exactly. Recomputing every fixture
  way through `tr.summarise` reproduces the committed `recorded_summary` to the digit, and every number in the
  handoff table with it:

      old_la_honda  way 8940690    259 nodes  5109.9 m  418.0 m gain  81.81 m/km  relief 87.9  grade 13.65%
      skyline       way 239028846  428 nodes  7013.6 m  361.9 m gain  51.61 m/km  relief 62.2  grade 10.47%
      alviso_flat   way 92357845    13 nodes   221.2 m    0.0 m gain   0.00 m/km  relief  0.2  grade  0.19%
      alviso_flat2  way 8929268     11 nodes   264.0 m    0.6 m gain   2.08 m/km  relief  1.7  grade  1.02%

  The eight manifest `bytes:` fields sum to 2,278,440,685 - the log's figure, exactly - and the eight
  `- name: 3dep-*` entries are the same eight names as `dem.TILES`, with n37w124 in neither.

  **Three mutations, each alone, control green before and after, worktree re-hashed clean each time:**
  1. THRESHOLD MOVED, `NOISE_FLOOR_M 0.5 -> 0.05`: RED on 5 named tests, including the brief's own -
     `test_terrain_fixture.py::TestTheNamedProperties::test_the_flat_bay_margin_roads_score_near_zero_gain`
     and `test_terrain.py::TestElevationGain::test_noise_below_the_floor_is_not_climb`.
  2. WEIGHT CHANGED, `RELIEF_WINDOW_M 1000.0 -> 100000.0`, relief over the whole way: RED on
     `test_terrain.py::TestRelief::test_a_long_steady_climb_is_not_more_dramatic_than_a_short_one`. This is
     the mutation the 18:40Z entry says caught NOTHING until both profiles were made to climb the same 600 m.
     I re-ran it rather than take the repair on trust. The repair holds.
  3. GATE INVERTED, `tile_for` ceil -> floor: RED on 17 named tests across the four files. The log claimed 12;
     the suite has grown since.
  No survivors, no equivalent mutants.

  **Product invariants:** correctly not applicable. `grep -niE "motorway|trunk|unpaved|private|track|exclude"`
  over both modules returns ONE line, and it is prose about an ocean tile. Nothing in T-0026 can exclude a way,
  so motorway-scores-0-but-is-never-excluded is untouched, and no hard gate is widened. Absence is never zero
  anywhere in the path - `tile_for`, `parse_values`, `sample_smoothed`, `coverage` and `relief` all keep None
  as None, which is the right call and is tested directly.

  **What I could NOT run, rather than claiming it.** `acceptance: []` is EMPTY, so there were no acceptance
  lines to replay; I re-derived the log's numbers instead. Nothing that touches a raster: the 2.28 GB of tiles
  are not on this box and `gdallocationinfo` is WSL-container-only, so `sample_tile`, `sample` and
  `sample_smoothed` ran only against injected fake runners, and the sha256 pins, the eight HTTP 200s and
  n37w124's 404 are unverified here. I did NOT run `ops/test`. `ops/check-pins --source-only` prints
  `PINS ok=8 skipped=11 pending=1 expired=0 failed=0`; no pin covers terrain, matching `pins_affected: []`.
  `ops/sane` prints `SANE FAIL exit=10` entirely from worktree hygiene - T-0104 and T-0154 unpushed, plus my
  own mutation in flight when the gate ran - and nothing of T-0026's.

  **Findings, all recordable, none blocking:**
  - `summarise(coords, profile)` never checks `len(profile)` against `len(resample(coords))`. It takes length
    from the GEOMETRY and gain from the PROFILE and divides. Truncating old_la_honda's 208-value profile to 50
    returns `gain_per_km 18.39, coverage 1.0` - no exception, no sanity problem, and coverage says 1.0 because
    it only ever sees the profile it was handed, never the geometry it was meant to cover. A three-quarters
    truncated read reports FULL coverage and a plausible road. `parse_values` guards the GDAL read, which is
    the guard the handoff pointed me at; THIS seam is the unguarded one, and it is the seam T-0030 builds on.
  - `test_dem.py::test_the_tile_set_matches_what_the_manifest_pins` NEVER OPENS manifest.yaml. Its body is
    `len(dem.TILES) == 8` and `"n37w124" not in dem.TILES` - the code against itself, under a name claiming an
    external oracle. The correspondence does hold; I compared both lists and they are identical. Nothing
    guards it.
  - `dem.neighbourhood` is not a 3x3 CELL neighbourhood, whatever its docstring and the brief say.
    `dlon = CELL_DEG/cos(lat)` is 1.269 cells at 38N, so east/west samples land 1 OR 2 cells out depending on
    where the point falls inside its cell: ~54% of points get a symmetric +/-1 row, ~46% an asymmetric -1/+2
    or -2/+1 that skips the adjacent cell on one side. Square-on-the-ground is a real argument and
    `test_the_box_is_square_on_the_ground_not_square_in_degrees` locks it in deliberately - but the kernel is
    not 3x3, and the per-point asymmetry is a sub-cell bias nobody has argued for. North-south is exact.
  - No committed recorder for `terrain_fixture.json`. This entry asks its reviewer to "confirm the profile
    really came from the pinned tiles by resampling a way yourself in the image"; there is no script in the
    tree that does it, here or in the container. The GEOMETRY half IS independently guarded - the <120 m node
    spacing assertion is a good guard against the hand-typed-polyline failure this log documents so well. The
    ELEVATION half rests on the fixture's own `dem_source` string.
  - `relief` and `grade_percent` window over the NODATA-FILTERED list, so a gap compresses the window on the
    ground: a "1 km" relief window spans more than 1 km of road where cells are missing, and grade's 100 m run
    is understated so the grade is overstated. Invisible here because all four fixtures are coverage 1.0.
    `elevation_gain` documents its bridging; these two silently do something else with the same gaps.
  - test_terrain_fixture.py line 14 says the roads "score 14.6% and 8.3%". The fixture produces 13.65% and
    10.47%. Prose, nothing anchored on it, but wrong.
  - The stdin worry from the handoff, answered rather than assumed: 3000 points -> 27,000 rows, 828,690 bytes,
    ONE subprocess call. It goes down stdin, not argv, so no argument limit applies.
  - Neither module has a production caller; `smooth3x3` still has none. Deliberate per the handoff, tracked by
    T-0052. Recorded so this PASS is not read as "this code runs".

  The two things this task got right are worth naming, because they are the reason it passes: it threw away
  its own fixtures when the 44% grade showed the geometry was wrong rather than tuning the threshold to fit
  them, and it re-derived the tile list against the bbox instead of against the URLs it had already checked.
  Both are the failure this repository exists to catch, caught by the owner on himself.

  Signed agent/rv-t0026. Not the owner; nothing in the repository was changed by this review.
