---
id: T-0208
title: scores are window-relative - one normalisation population per REGION: the LA clip scored in chunks against a single reference so a way's score does not depend on which window it was clipped into
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T15:26:13Z
lease_expires_at: 2026-09-20T01:26:13Z
worktree: .worktrees/T-0208
branch: task/T-0208
exclusive: [scenic-index]
touches: [services/etl/etl/, services/etl/tests/, ops/etl-extract, ops/mutate/, ops/lib/check-mutate-population.py]
pins_affected: []
reviewer: null
depends_on: [T-0204, T-0207]
verify: [ops/test, ops/check-pins]
acceptance:
  - "RED BY NAME first: a test over a fixture way present in two overlapping windows asserting ONE score (T-0204 measured 160 of 190 seam ways with different scores across grid-a/grid-b: Mulholland Drive way 1533792498 0.6988 vs 0.7022; West Sunset Boulevard way 399301293 0.6308 vs 0.6372), red today, then green once the rank-normalisation reference (normalise_region's 'reference' population) is the whole region's, computed once and passed to every chunk"
  - "the LA clip (561,000 ways) scored in chunks that each finish in one foreground container call, the reference population recorded (count, sha256 of the reference table) and the seam re-measured: 0 of N seam ways differ; the three windows' top tens re-quoted"
  - "the WHOLE-LA TAGGED PBF written by this task from the region-normalised scores (tagwriter, T-0207's class ceiling in force) and RETAINED under the MAIN checkout's services/etl/work/la/ with its sha256, way count, scored count and CHECK4 line (python -m etl.scenecheck: null_score=0 gated_scored=0 malformed=0) quoted in the Log AS THE STAGE LANDS - T-0209 imports THIS artifact and scores nothing"
  - "cd services/etl && python -m pytest tests -rs -o addopts= count line and zero skips; the touched module's ops/mutate population updated"
---
## Brief

From T-0204's real run (PR #113): osmium completes crossing ways, so the 190 ways on the -118.45 seam were scored
in both halves - and 160 of them got different scores, because rank-normalisation runs over whatever window the
way landed in. A score that depends on the clip is not an index; the router would see steps at every chunk seam.
normalise_region already takes a 'reference' population (T-0163) - the run never passes the region's.

## Log
- 2026-09-19T09:51:35Z filed by agent/claude-fable-5-1 from T-0204's seam measurement. Not started. Before any whole-LA tagged PBF is handed to GraphHopper.
- 2026-09-19T11:43:44Z RULED by agent/claude-fable-5-1 (04:13 panel; grounded 8 of 14 - only the grounded items applied): depends_on += T-0207 (both tasks re-record grid_top25.json and re-quote the top tens; only panel prose ordered them). THE WINDOW FIXTURES: services/etl/tests/fixtures/canyon_top25.json, grid_top25.json and grid_tie_top25.json are re-recorded BY THIS TASK in one commit, with the bound (its way id and unit) and RIDGE_ALLOWLIST in services/etl/tests/test_window_ranking.py re-derived in that same commit and the pre- and post- bound values and the seam-disagreement count (must be 0) quoted in the Log. CLAUDE.md's snapshot-reference clause is about UI snapshot images and does NOT bind these data fixtures; the author rule binds them - the re-record is measured, quoted and reviewed. Clause 3's 'population updated' means CREATED for services/etl/etl/normalise.py, which sits in P-PROC-06's DEBT list with no population.
- 2026-09-19T15:26:13Z claimed by agent/claude-opus-5; lease until 2026-09-20T01:26:13Z
- 2026-09-19T15:26:14Z AMENDED at claim by agent/claude-fable-5-1 (orchestrator; 06:13 panel STRATEGY, grounded on the T-0208/T-0209 texts): (1) a fourth acceptance line - this task also WRITES AND RETAINS the whole-LA tagged PBF (T-0209 clause 1 presumed the artifact existed and nothing owned writing it; scoring 561k ways twice in two container sessions is the alternative). (2) LOCK ORDER RULED for scenic-index: T-0208 (this) -> T-0209 -> T-0216; T-0216 may not claim the lock ahead of the routed LA drive. (3) Inputs: the MAIN checkout's services/etl/work/la/ (la.osm.pbf, la-filtered.osm.pbf, meta.json with the 560,208 per-class counts) and the three windows' docs; T-0207's re-tagged windows preserved read-only at services/etl/work/t0207/. (4) The fixture re-record ruled on 04:13 stands: canyon_top25.json, grid_top25.json, grid_tie_top25.json re-recorded in ONE commit with the bound and RIDGE_ALLOWLIST re-derived and the pre/post values quoted.
- 2026-09-19T16:42:47Z RULED by agent/claude-opus-5 (owner), before any code. Every disagreement between the
  Brief, the code and the real data, settled here.
  (R1) THE TWO-PASS DESIGN. Pass 1 cuts `la-filtered.osm.pbf` into BBOX TILES with one
  `osmium extract -c <config>` pass (not way-id ranges: `osmium getid` cannot cut a tile without a way list,
  and the tile grid is the only cut whose inputs - DEM, WorldCover, byway corridors - are already local to the
  clip), runs `etl.waydoc` over each tile and writes that tile's RAW ranked-term values. Pass 2 normalises every
  tile AGAINST ONE REFERENCE, scores and tags. A way that crosses a tile edge is COMPLETED by osmium into both
  tiles and is therefore documented twice; the DEDUP KEY IS `way_id` and the rule is FIRST TILE IN SORTED TILE
  ORDER WINS, applied identically to the reference values and to the merged scored table, so the tagged PBF
  carries exactly one row per way. That rule is only allowed to be arbitrary if the two tiles agree; R1b is
  what makes them agree, and the run MEASURES the agreement rather than assuming it.
  THE REFERENCE IS, per ranked term, THE SORTED LIST OF THAT TERM'S RAW VALUES over the whole region's
  ranking population - `{"curvature": [...], "elevation_gain": [...], "relief": [...], "sinuosity": [...],
  "furniture": [...]}`. It is written to `services/etl/work/la/la-reference.json` with its count and sha256
  quoted in this Log, and read back by `etl.assemble --reference`.
  (R1b) A SECOND SEAM CAUSE, MEASURED BEFORE IT WAS RULED ON (`services/etl/work/seam_raw.py` over T-0204 two
  real docs, read-only): of the 190 ways present in BOTH grid-a-doc.json and grid-b-doc.json, only 92 rows are
  byte-identical. The ONE field that differs is `meters_to_nearest_motorway` - 98 of 190 - because
  `waydoc.build` measures it against the motorways PRESENT IN THE CLIP, and 15 of those 190 CROSS `score.py`
  150 m threshold between the two clips, so they carry the x0.7 multiplier in one window and not in the other.
  A region-wide ranking reference cannot fix that: it is the same defect one layer down - a per-way term
  computed against whatever landed in the window. RULED: `waydoc.build` takes an optional `motorway_source`
  (CLI `--motorways`), the region whole motorway set cut once with `osmium tags-filter`; the default stays the
  clip own ways, so every existing caller and test is unmoved. Without this the fourth count line below
  ("0 of N seam ways differ") is simply false, and a margin cannot buy it either: `osmium extract` completed
  ways 0.07 deg past T-0168 clip bbox, so no fixed margin bounds the overhang.
  (R2) WHAT IS IN THE REFERENCE POPULATION. Exactly what `normalise_region` ranks today, and not one row more:
  `normalise.population_of` drops the ZERO CLASSES (motorway, trunk and their links - they score 0 by class and
  15k of them would set the curve for the back roads), and `normalise.answering` drops, from the SINUOSITY term
  only, the ways that DECLINED to measure it. GATED ways ARE IN the population: the gate is applied in
  `assemble.scored_row` AFTER the score, so a gated way ranks normally and is then set to `GATE_SCORE`. Keeping
  those three rules is the whole point - the reference must be the same population the region-internal default
  ranks, only larger. Motorway/trunk stay penalised-not-excluded (CLAUDE.md): they are out of the CURVE, in the
  corpus, at 0.
  (R3) THE SEAM TEST binds to the shipping symbol `assemble.assemble` - the entry point `python -m etl.assemble`
  runs - over TWO OVERLAPPING WINDOWS BUILT FROM T-0204 REAL DOC ROWS, asserting ONE score for the way in both.
  It is RED today by name because `assemble.assemble` takes no reference at all (assemble.py:251,
  `normalised = normalise_region(records)`). The fixture ways are taken from the 92 rows that are BYTE-IDENTICAL
  in both of T-0204 docs, so the only thing the two windows disagree about is the ranking population - which is
  what this test is about. Mulholland Drive 1533792498 (0.6988 vs 0.7022) and West Sunset Boulevard 399301293
  (0.6308 vs 0.6372) are the named ways if they are in that 92; whichever are not, the Log says so.
  (R4) THE FIXTURE RE-RECORD, in one commit: `canyon_top25.json`, `grid_top25.json`, `grid_tie_top25.json` and
  `window_readback_sample.osm.xml` are ALL re-recorded from the region-normalised scores - the sample too,
  because `test_the_fixture_row_is_the_shape_the_shipping_oracle_produces` asserts the sample units equal the
  canyon fixture, and a stale sample would make that test a statement about a file. The three windows are cut
  OUT OF THE SHIPPED `la-tagged.osm.pbf` with `osmium extract` and read back with `osmium cat`, so the fixtures
  are `scenecheck.top` over the artifact this task ships and not over a private re-run. The bound and
  RIDGE_ALLOWLIST in `test_window_ranking.py` are re-derived in that same commit with pre/post values quoted.
  IF THE TWO MULHOLLAND RIDGE IDS DROP OUT OF THE GRID WINDOW TOP TEN under the region reference, the allowlist
  SHRINKS and the Log says so plainly - the whitelist is re-derived from the measurement, never re-ranked to
  keep a way in it. `test_the_seam_merge_rule_is_recorded_and_the_rows_obey_it` is re-derived too: under one
  reference the rule is no longer "take the max of two disagreeing clips", and a meta with an empty
  disagreement list would make that test pass over nothing.
  (R5) CHUNK SIZING AND THE DRIVER. The tile grid is sized from the FIRST tile measured waydoc time, quoted
  below before the loop is launched. The loop is ONE background driver (`services/etl/work/pass1.sh`, nohup,
  log under the worktree `services/etl/work/`), checked with `sleep 590 && tail`, at most once per ten minutes.
  A RESTART RESUMES BY FILE PRESENCE: a tile whose `-doc.json` is already non-empty is skipped, so the worktree
  that survives a session restart is the resume state. Tiles run N-at-a-time inside the driver (the box has 16
  cores and 30 GB); chunks are independent, so parallelism changes no number.
  (R6) THE LINE BUDGET. `assemble.py` is 293 of 300. The reference is BUILT in a new module,
  `services/etl/etl/region_reference.py` (raw values out of records, the merge by `way_id`, the sorted table,
  its sha256, load/dump); the bisect mid-rank lives in `normalise.py` (231 lines) beside `ranks_against`, which
  it must equal. `assemble.py` gets ONLY the parameter and the CLI flag. `ranks_against` is O(len(reference))
  per way: over a 560k-way reference that is ~3e11 comparisons and would never finish, so `normalise_region`
  sorts each reference term ONCE and ranks with `bisect`; the two are proved identical over a fixture, RED by
  name first. Both new/changed numeric modules ship in ONE population, `ops/mutate/normalise.py`, whose
  SUBJECT_MODULES names `normalise.py` and `region_reference.py`.
- 2026-09-19T17:26:00Z STAGE 1, EXTRACT, in the pinned `scenic-etl:latest` through WSL
  (`docker run --rm -v "$PWD:/w"` from the MAIN checkout, so the worktree and the shared `services/etl/inputs`
  are both visible; the worktree is `/w/.worktrees/T-0208/services/etl`). Quoted as it landed.
  THE REGION MOTORWAY SET (R1b), one `osmium tags-filter la-filtered.osm.pbf w/highway=motorway,motorway_link,
  trunk,trunk_link` - the four classes `proximity.MOTORWAY_CLASSES` names - then `osmium cat` to XML:
      `Number of ways: 19511` / `Number of nodes: 75897`, bbox (-119.0110416,33.695739,-117.8407146,34.4666531)
      work/la-motorways.osm.xml 22,086,577 B
  THE TILE GRID, `osmium extract -c` over `la-filtered.osm.pbf`: ten columns by six rows of the region bbox
  -119.0,33.7,-117.85,34.45, so 0.115 deg by 0.125 deg a tile. SIXTY EXTRACTS IN ONE CONFIG WAS OOM-KILLED
  (`Killed`, the kernel, after 70 s) - osmium holds every extract's buffers for the complete_ways strategy - so
  the cut is SIX CONFIGS, one per row, 2m26s for all six. 48 of the 60 tiles hold ways; the twelve empty ones
  are ocean and desert. Clip ways over the 60 tiles: 572,366 against the file's own 560,208, so the tile edges
  complete 12,158 ways into two tiles each - 2.1%, and the population the seam re-measure ranges over.
  THE FIRST CHUNK, MEASURED IN THE FOREGROUND BEFORE THE LOOP WAS SIZED (R5): tile t05,
      `WAYDOC ways=9831 refused=0 not_a_road=104 byways=865 byways_no_route_key=793`   real 3m25.227s
  = 205 s for 9,831 ways, 20.9 ms a way with the motorway-set parse and the `osmium cat` in it. EIGHT MINUTES
  IS THEREFORE ABOUT 23,000 WAYS, so every tile above 22,000 clip ways is cut in half by longitude: nine tiles
  (t09 31,303 · t15 27,167 · t16 24,478 · t17 27,405 · t18 26,581 · t19 24,773 · t25 23,320 · t26 29,566 ·
  t27 24,886) became eighteen halves, the largest 16,168 (t09b), 1m39s for both split configs. The loop is
  62 TILES, the largest 21,484 clip ways (t35) - a projected 7.5 minutes, under the ceiling.
  THE LOOP is one background driver, `work/pass1.sh`, `docker run -d` with its stdout in `work/pass1.log`,
  six tiles at a time (`xargs -P 6`) on the 16-core box. Resume is by file presence: `[ -s work/docs/<t>-doc.json ]`
  skips a tile, which is why the very first line of the log is `SKIP t05 (doc present)`.
- 2026-09-19T18:05:00Z RED BY NAME, THEN GREEN - each on the pristine tree, quoted from the run.
  1. `tests/test_motorway_source.py` (R1b), before `motorway_source` existed:
     `2 failed, 1 passed` - `TypeError: build() got an unexpected keyword argument 'motorway_source'` on
     `test_the_motorway_distance_is_measured_to_the_supplied_region_set_not_to_the_clips_own_ways` and
     `test_a_non_motorway_in_the_region_file_is_not_measured_to`. The third,
     `test_the_clip_answers_zero_because_the_clip_contains_the_motorway`, passed then and passes now: it pins
     the behaviour being replaced. GREEN after: `13 passed` with `tests/test_waydoc.py` beside it.
  2. `tests/test_region_reference.py`, before `etl/region_reference.py` existed:
     `ImportError: cannot import name 'region_reference' from 'etl'` - 1 error during collection. With the
     module present but no bisect ranker, the two that matter went RED BY NAME (the import is inside the test
     body exactly so that they can):
     `test_the_bisect_rank_equals_ranks_against_value_for_value` and
     `test_the_bisect_rank_is_not_vacuous_and_separates_the_probes` - `3 failed, 5 passed` (the third failure
     was my own test reading a dict's keys where it meant its values, corrected in the same commit).
     GREEN after `ranks_against_sorted`: `46 passed` with `tests/test_normalise.py` beside it.
  3. `tests/test_seam_one_score.py` (R3), before `assemble.assemble` took a reference:
     `2 failed, 2 passed` - `TypeError: assemble() takes 1 positional argument but 2 were given` on
     `test_a_way_in_two_overlapping_windows_takes_one_score_against_the_region_reference` and
     `test_the_two_named_ways_are_the_ones_the_measurement_named`. The two that PASSED are the ones that make
     the red mean something: `test_the_two_windows_really_do_overlap_on_the_named_seam_ways` and
     `test_without_a_region_reference_the_same_ways_take_two_scores`. GREEN after: `26 passed` with
     `test_assemble.py` and `test_assemble_wiring.py` beside it.
  THE SEAM FIXTURES ARE T-0204's OWN ROWS. Both ways the Brief names are among the 92 seam rows that are
  byte-identical in grid-a-doc.json and grid-b-doc.json - `named way 1533792498: IDENTICAL name=Mulholland
  Drive`, `named way 399301293: IDENTICAL name=West Sunset Boulevard` - so the two windows in the fixture
  disagree about NOTHING except their populations. The nine private ways of each window are chosen to make
  that difference bite: window a takes the grid-a-only ways with the HIGHEST curvature, window b the
  grid-b-only ways with the LOWEST. THE FIRST CUT TOOK THE NINE SMALLEST ROWS IN EACH CLIP AND BOTH WINDOWS
  THEN RANKED THE SHARED WAYS IDENTICALLY - a fixture that cannot show the defect cannot show the fix, and
  `test_without_a_region_reference...` is what caught it. On the fixture as shipped, without a reference:
      way 1533792498 Mulholland Drive       window a 0.6634  window b 0.6683
      way 399301293  West Sunset Boulevard  window a 0.5693  window b 0.5826
  the same shape and the same order of magnitude as T-0204's measured 0.6988/0.7022 and 0.6308/0.6372. With
  the merged reference both are ONE number.
  LINE COUNTS after the change: assemble.py 299, normalise.py 256, region_reference.py 109, waydoc.py 288.
- 2026-09-19T18:55:00Z TOUCHES AMENDED by agent/claude-opus-5 (owner): `ops/lib/check-mutate-population.py`
  added. The task text requires this population to be REGISTERED in that file's DRIVERS and COVERED_FLOOR,
  and the original `touches:` did not name it, so the pre-commit hook would have refused the registration
  the acceptance asks for. Nothing else in `ops/lib/` is touched. `services/etl/etl/waydoc.py` is NOT added
  to any SUBJECT_MODULES: it is in P-PROC-06's allowlist as wiring (T-0168's closing ruling), and the check
  refuses an allowlist entry for a module a population also covers. R1b's selection rule is guarded by
  `tests/test_motorway_source.py` instead, whose whitelist clause -
  `test_a_non_motorway_in_the_region_file_is_not_measured_to` - is the one that matters.
- 2026-09-19T20:51:04Z THE RANKING'S MUTATION POPULATION, red then green, quoted from the runs.
  `ops/mutate/normalise.py` + `ops/mutate/normalise_mutations.py`, `SUBJECT_MODULES =
  ("services/etl/etl/normalise.py", "services/etl/etl/region_reference.py")`, `MIN_MUTATIONS = 18`,
  registered in `ops/lib/check-mutate-population.py` DRIVERS and COVERED_FLOOR (both modules).
  FIRST RUN, on commit cbc52bb: `MUTATIONS: 17 caught, 1 missed, 0 skipped, of 18` - `MUTATE FAILED
  caught=17/18`. THE SURVIVOR, by name: `the digest is taken over the dict's insertion order rather than a
  canonical one (exit 0)`. It is NOT equivalent and was not filed as one: `table_of` builds its keys in
  `RANKED_TERMS` order and `load` builds them in the order the FILE lists them, so under `sort_keys=False`
  one population reached by the two paths would carry two names and the sha256 this Log quotes would
  identify the writer instead of the population. It survived because the only table the digest test ranged
  over held `curvature` and `relief`, which sort the same way under `RANKED_TERMS` as under `sorted()` - a
  predicate that could not see what it was written to see. `test_the_same_values_under_a_different_key_order_are_the_SAME_reference`
  ranges over `sinuosity`/`furniture`, the one adjacent pair whose `RANKED_TERMS` order is not their sorted
  order, and asserts both halves of that (commit 5dfbfb8). SECOND RUN: `MUTATIONS: 18 caught, 0 missed,
  0 skipped, of 18` / `EQUIVALENT: 0 caught, 2 missed, 0 skipped, of 2` / `MUTATE OK  caught=18/18
  equivalent_caught=0`; `--prove-vacuity`: `VACUITY: 0 caught, 18 missed, 0 skipped, of 18` / `VACUITY
  PROVED`. The two EQUIVALENT entries carry their witnesses in `normalise_mutations.py` (the bisect ranker
  has no accumulator, so iteration order cannot change its dict; `raw_values` and `load` both coerce before
  `table_of` can see a value).
  `ops/lib/check-exec-bits` refused `ops/mutate/normalise.py` at 100755 - under `ops/mutate/` a driver is
  DATA, run as `python ops/mutate/<name>.py`, and every other driver there is 100644. Fixed to 100644;
  `P-OPS-01: 81 files, 23 required present, all modes correct`.
- 2026-09-19T20:51:04Z (R7) A DISAGREEMENT BETWEEN A FIXTURE'S RECORD AND THE DATA, ruled before the
  re-record. `canyon_top25.json` meta says the canyon window is `--bbox -118.75,34.02,-118.55,34.15`;
  `services/etl/work/la/window-doc.json` meta says `-118.95,33.98,-118.55,34.15`. MEASURED, over the
  145,972 coordinates of that document's 11,740 ways: `lat 34.0027..34.1724  lon -118.9683..-118.5139`.
  A clip at -118.75 cannot hold a node at -118.9683, and 0.0183 deg west of -118.95 is exactly the
  `complete_ways` overhang R1b already measured. THE FIXTURE'S RECORDED BBOX IS WRONG and always was; the
  window is `-118.95,33.98,-118.55,34.15`, which is what the re-record cuts and what its meta will say.
  The 11,740-way count the task text names is the one thing both records agree on and it is the document's
  own way count.
  (R8) `test_the_seam_merge_rule_is_recorded_and_the_rows_obey_it` IS RE-DERIVED, not deleted. T-0204's
  rule - an overlapping way is taken at the MAX of its two clips - existed to arbitrate a disagreement
  that this task removes, and a meta whose `seam_disagreements` list is empty would leave that test passing
  over nothing (the vacuity R4 named). The re-recorded `grid_top25.json` carries `seam_ways`: EVERY way
  read back in both halves of the grid window, with BOTH halves' `scenic_score_unit`. The test asserts the
  list is non-empty, that every entry's two values are equal, and that a way of that list which is also in
  the 25 rows carries that same value - so the fact being pinned is the one this task bought, measured over
  a population the fixture names.
