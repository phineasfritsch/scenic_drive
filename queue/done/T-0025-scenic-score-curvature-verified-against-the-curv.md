---
id: T-0025
title: Scenic score: curvature, verified against the Curvature project's published values
state: done
owner: agent/claude-opus-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T16:59:08Z
lease_expires_at: 2026-09-07T20:59:08Z
worktree: ../wt/T-0025
branch: task/T-0025
exclusive: []
touches: [services/etl/]
pins_affected: []
reviewer: agent/rv-t0025
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Reimplement the Curvature project's method exactly: circumcircle radius from every 3 consecutive
OSM nodes, take the MIN of the two triangles a segment belongs to, cap 10 km, run the deflection filter that
zeroes fake curvature when the heading change is below gap_distance/175, then weight length by 2.0/1.6/1.3/1.0/0
at radius <30/<60/<100/<175 m.

THE ORACLE: Curvature publishes computed outputs for Vermont. Our value for the same way ids must match within
2%. That is an external oracle an agent cannot fabricate - the same discipline that caught the bad solar oracle
in T-0011. If the published data is not machine-readable, say so in the log and propose the next best oracle
rather than quietly falling back to self-generated fixtures.

## Log
- 2026-09-07T16:59:08Z claimed by agent/claude-opus-5; lease until 2026-09-07T20:59:08Z

- 2026-09-07 claimed by agent/claude-opus-5; reviewer agent/reviewer-30. Stacked on task/T-0024, which owns
  services/etl/.

- **THE ORACLE EXISTS AND IS MACHINE-READABLE.** The brief asked for this answer explicitly, and to say so
  rather than fall back on self-generated fixtures if the answer was no.
  `https://kml.roadcurvature.com/north_america/us/vermont.c_300.kmz` is a KMZ whose every Placemark
  description holds a table of the collection's constituent ways, each row carrying the OSM way id inside an
  `openstreetmap.org/way/N` link next to that way's curvature value, surface, length and name:

      <a href="https://www.openstreetmap.org/way/625066263">625066263</a> ... asphalt ... 63

  4422 collections, 3318 of them containing exactly one way. Pinned by sha256 in the manifest ON PURPOSE,
  unlike the Geofabrik extracts: an oracle that silently follows upstream is not an oracle. If they regenerate
  it the fetch fails and a human re-pins it having looked at what changed.

- **Recording that digest was impossible before this task.** `inputs/manifest.yaml`'s header documents
  "Get it with `--record-digest NAME`, then commit it", but a new entry has no digest, so it was invalid,
  validation ran first, and the tool refused with the one complaint it exists to resolve. Fixed:
  `--record-digest` now re-validates the named entry with a stand-in digest. Only that entry, only a missing
  or `TODO` digest; every other problem still fatal. The first version of that fix matched the complaint
  TEXT, which excused `TODO` and not a genuinely absent digest because those produce different messages - the
  test for the second case caught it, and re-validating with a stand-in has no such seam. Seven tests: two
  are the regression guard, five guard against the excuse being too broad.

- **Every constant checked against their source, not against the brief.** geomath.py
  (`rad_earth_m = 6373000`, the `cos > 1` clamp), radiusmath.py (`circum_circle_radius`, and its two
  fallbacks to 10000), add_segment_length_and_radius.py (`MAX_RADIUS = 10000`, the write order that produces
  the min-of-two-circumcircles), add_segment_curvature.py (the four bands, strict `<`, weights 2/1.6/1.3/1),
  filter_segment_deflections.py (`min_variance = gap_distance / level_1_max_radius`, 175, look-aheads 3..7).
  All match what the brief said, which is worth knowing rather than assuming.

- **Quirks reproduced rather than tidied**, each named in `etl/curvature.py`:
    - MAX_RADIUS is applied ONLY in the last-segment branch, so interior radii legitimately exceed 10000
    - the min-of-two-circumcircles falls out of the write order; a `min(left, right)` gives different numbers
      at the first and last segments
    - `math.fabs` inside their sqrt turns a triangle-inequality violation - which floating point produces for
      nearly-collinear points - into a huge radius instead of a domain error
    - the deflection filter compares raw headings with `abs(a - b)`, never the wrap-aware `heading_diff` the
      same class defines and does not call on that path
    - `get_segment_heading` does atan2 on unprojected degrees, squashed by the cosine of the latitude

- **The result, and the honest path to it.** Reporting one number over everything would have been 77%.

      all single-way collections              n=3297   77.0% within 2%   median 0.09%
      ... restricted to identical geometry    n=2571   90.4%             median 0.07%
      ... and no squash exposure              n=2307   95.0%             median 0.066%  p90 0.84%

  Two causes, both measured:

  1. OSM MOVED. Each Placemark carries the geometry Curvature computed over. 726 of 3297 ways differ from
     today's Geofabrik Vermont extract, and those agree 29.6% of the time against 90.4% for unchanged
     geometry. The disagreement is the data, not the arithmetic.
  2. THE FIVE STEPS ARE NOT THE PUBLISHED PIPELINE. `processing_chains/adams_default.sh` runs six squash
     post-processors after them - near junction/traffic_calming ways, near parking:lane ways, within 30 m of
     a junction or oneway tag change, and within 30 m of any highway=stop, give_way, traffic_signals,
     crossing, mini_roundabout, traffic_calming or barrier node - then
     `split_collections_on_straight_segments --length 2414`. Ways within 30 m of such a node agree 28.0% of
     the time; ways with none agree 82.2%. Filed as T-0050: adopting them is a product decision, not a
     matching exercise.

  The residual 5% is consistent with tagged nodes on ADJACENT ways: `osmium getid -r` pulls only the nodes
  these ways reference, so a traffic signal 25 m away on a cross street is not in the subset and cannot be
  excluded. Stated rather than chased.

- **The fixture is 400 ways sampled deterministically (seed 20260907) from the 2307 eligible**, with the
  three selection conditions written into the file itself. A subset without written criteria is a cherry-pick.

- **Four meta-tests, because an oracle that cannot reject anything is decoration.** Changing a weight, moving
  a band threshold, and taking the larger circumcircle each drop agreement below the floor. The fourth
  records a NEGATIVE result: swapping their 6373000 m earth radius for WGS84's 6378137 moves agreement only
  95% -> 94%, because a 0.08% length change is invisible at a 2% tolerance. I wrote that test expecting it to
  fail the oracle, found it did not, and corrected the test rather than deleting it. So this oracle verifies
  the ALGORITHM; the constant is held by an exact-value unit test instead. Worth knowing what 2% cannot see.

- **Verification:** `cd services/etl && python -m pytest -q tests/` -> 142 passed;
  `bash ops/check-pins` -> `PINS ok=10 skipped=0 pending=3 expired=0 failed=0`; `bash ops/queue-check` ->
  `QUEUE OK`. GitHub Actions has not executed since ~15:11 UTC (billing block), so all of this is local.

- Handing to agent/reviewer-30. The reviewer should re-derive the agreement figure rather than trust it: the
  fetch is a few minutes, and the honest number depends entirely on the partition being defensible. Attack
  the partition first - if the three exclusion conditions can be argued into a cherry-pick, the 95% means
  nothing.
- 2026-09-18 review by agent/rv-t0025 (not the owner; agent/reviewer-30 was named on 2026-09-07 and never
  reviewed this). **PASS.** Reviewed at origin/main 11078d3 in a throwaway worktree, removed afterwards. The
  code landed in 43c93eb and has not been touched since, so what merged in PR #36 is what I read.

- **The oracle is real, and I re-fetched it rather than trusting the fixture.**
  `vermont.c_300.kmz` comes back at 2,557,952 bytes, sha256 `3bdf4d14...39046` - byte-identical to the pin in
  `inputs/manifest.yaml` and to `source_sha256` in the fixture. (It needs a browser User-Agent; a bare urllib
  request gets 403.) 4422 Placemarks, 3318 single-way, exactly as the Log says. All 400 fixture way ids are
  single-way Placemarks in it, **all 400 `oracle_curvature` values match the KMZ's published numbers exactly**,
  none of the 400 also sits in a multi-way collection, and the stored geometry matches the KML's own
  `<coordinates>` to a worst case of 5.6 cm across all 400 ways. The expected values are not computed from the
  code under test. That was the question that mattered and it is answered.

- **The number re-derives, and the partition survives the attack the owner asked for.** The shipped fixture
  gives 94.5% within 2%, median 0.064%, p90 1.04% - half a point BELOW the 95.0% claimed, which is not how a
  cherry-pick fails. Computing on the KML's own geometry, so "OSM moved" cannot flatter anyone: all 3318
  single-way collections 83.5%, the fixture's 400 89.5%, the 2918 outside it 82.7%. The 6.8-point gap is the
  three written conditions doing what they say. And 22 of the 400 SELECTED ways still fail the tolerance on
  their own geometry. A set chosen because it agreed would have none.

- **The vacuity guards fail for the reasons they name.** Against a 0.93 floor and a 0.945 control: weight
  2.0->1.0 gives 0.235, band 175->250 gives 0.355, the larger circumcircle gives 0.015, dropping the deflection
  filter gives 0.915. Each monkeypatch genuinely binds - the module globals are resolved at call time - and each
  is a real collapse in agreement, not a swallowed exception. The WGS84 test reproduces at 0.940 against its
  `> 0.90`: the declared negative result is honest.

- **Three mutations nobody had already guarded, each applied alone; no survivors.** `MAX_RADIUS` 10000->150
  killed by `test_a_straight_line_is_flat` and the oracle. The third band's weight 1.3->1.35 - a 3.8% nudge -
  killed by `test_each_band_and_its_boundary[60.0-2-1.3]`, its 99.999 sibling, and the oracle. Inverting the
  deflection filter's `<` killed by the oracle ALONE.

- **Four things to record, none of them blocking.** (1) The fixture's selection line says "400 from 400
  eligible"; the Log says "from the 2307 eligible". They contradict, a seed is pointless if the sample is the
  whole pool, and nothing tests the counts - `test_the_fixture_says_how_it_was_selected` only counts the list.
  I could not settle it here: condition 3 needs osmium over the Geofabrik extract and osmium is not on this box.
  (2) `test_a_single_segment_way_is_straight_by_definition` and `test_only_the_last_segment_is_capped` both
  assert against `cv.MAX_RADIUS` itself, and both stayed GREEN when I moved it to 150. That is the exact defect
  this repository exists to catch; it is survivable only because `test_a_straight_line_is_flat` and the oracle
  caught the same mutation. (3) `filter_deflections` and `segment_heading` have no direct unit test at all, and
  the guard keeping the filter load-bearing has 1.5 points of margin resting on 13 of 400 ways. (4) The
  `_filtered` flag is inert: it can never be True while `curvature_level` is non-zero, and removing it changes
  0 of 400 results - an equivalent mutant, so not a correctness finding, but the docstring oversells it.

- **What I could not run here.** `ops/check-pins` produced nothing in ten minutes and was stopped - not
  load-bearing, `pins_affected: []` and no pin mentions curvature. `ops/test` not re-run: whole-repo, multi-tier,
  and this task touches only `services/etl`, whose tier I ran in full. `ops/queue-check` -> `QUEUE OK (147
  tasks)`. `services/etl` pytest: 457 passed, **zero skipped** - the only conditional skips in that suite are
  the two git-availability guards in `test_manifest.py` and neither fired. The Log's "142 passed" is eleven days
  and sixty merges stale; the property holds. Re-deriving selection conditions 2 and 3 is impossible on this
  box: no osmium, no GDAL, no PBF in the tree.

- Product invariants are not implicated: `curvature.py` has no highway, surface, access or exclusion logic of
  any kind - motorway/trunk scoring and the safety gates live in `byways.py` and `tagfilter.py`, untouched here
  and still correct. Nothing in this task widens a gate or gates on absent evidence.

- Signed agent/rv-t0025. Changed nothing; the transition is the orchestrator's.
