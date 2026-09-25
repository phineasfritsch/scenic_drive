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
touches: [services/etl/etl/, services/etl/tests/, ops/etl-extract, ops/mutate/, ops/lib/check-mutate-population.py, ops/lib/mutate_population_table.py]
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
- 2026-09-19T21:29:46Z PASS 1 WAS NOT COMPLETE, AND THE REFERENCE IS WHAT FOUND IT. Quoted as it landed.
  The resume note this session inherited said all 125 quarter-tile documents were in `/fast/docs`, and
  `ls /fast/docs | wc -l` was 125 while `wc -l work/tilelist.txt` was 125. A COINCIDENCE: 27 of those
  documents are the whole tiles in `work/done.txt`, which are NOT in `tilelist.txt`, so 27 of the
  tilelist's own tiles had no document at all. Nothing in the tree said so. What said so was the first
  reference built over those 125 documents:
      `REFERENCE docs=125 ways=410111 unique=386884 curvature=386884 ... sinuosity=371759`
      `REFERENCE sha256 7d6f74caa173beb5b367727f6123cbaf3ce008ad46e479cccdedde8b6f7c32fe  bytes 22285328  1544s`
  410,111 documented ways against the clip's own 560,208 is 73% of the region, and "the reference from the
  whole clip is the non-negotiable part". `comm` over the document names against `tilelist.txt` + `done.txt`
  named the 27 exactly: t08q0-3 · t16b · t25b · t28q2-3 · t33 · t35q0-3 · t36q0-3 · t37q0-3 · t44q0-3 ·
  t45 · t54. A REFERENCE THAT IS SHORT OF ITS REGION CANNOT BE SEEN IN ANY OF ITS OWN NUMBERS - it is a
  smaller curve, not a broken one - which is why the count is quoted against the clip's own way count and
  not merely recorded.
  PASS 1C, `work/pass1c.sh` over `work/tilelist-missing.txt`, nine tiles at a time, same resume-by-file-
  presence rule, 27 tiles in 3 rounds of ~11 min. Its container was removed before its stdout was copied
  out (my error; `work/count_missing.py` recomputes the same numbers from the documents the stage wrote
  rather than retyping them from memory):
      `PASS1C 27 tiles, 164285 ways, 0 refused` - t08q0 3133 · t08q1 7111 · t08q2 4817 · t08q3 6382 ·
      t16b 10868 · t25b 10574 · t28q2 6059 · t28q3 5031 · t33 10278 · t35q0 3094 · t35q1 5910 ·
      t35q2 6271 · t35q3 6197 · t36q0 6044 · t36q1 4773 · t36q2 4695 · t36q3 4113 · t37q0 5545 ·
      t37q1 6046 · t37q2 4740 · t37q3 4813 · t44q0 5729 · t44q1 6323 · t44q2 2739 · t44q3 4880 ·
      t45 10290 · t54 7830. `PASS1C END 152 docs`.
  THE REFERENCE, over all 152 documents - the count line this task's second acceptance clause asks for:
      `REFERENCE docs=152 ways=574396 unique=540793 curvature=540793 elevation_gain=540793
       furniture=540793 relief=540793 sinuosity=519764`
      `REFERENCE sha256 68863987ca325a42913d2534f1fbcc2d8a2292467125e93606425197ae2aa059  bytes 31385367  458s`
  574,396 documented rows over 152 tiles against the clip's own 560,208 ways: the tile edges complete
  14,188 ways into two tiles each (2.5%), and 540,793 of the region's ways are IN the curve. The 19,415
  that are not are the zero classes R2 keeps out of it (`meta.json` counts motorway 17,394 + trunk 2,117
  = 19,511 before their links and before the ways `waydoc` calls not_a_road). `sinuosity` is 21,029 short
  of the other four: those are T-0161's closed ways, which decline THAT term and no other (R2).
  `work/pass2_reference.py` was rewritten to a `multiprocessing.Pool(9)` over `Pool.imap`, which yields in
  the order it was given, so SORTED TILE ORDER - and therefore first-tile-wins - is unchanged by the
  parallelism: 1,544 s serial over 125 documents became 458 s over 152.
- 2026-09-19T21:59:24Z THE WHOLE-LA RUN, every stage's count line quoted as it landed. Each is one
  foreground container call of the digest-pinned `scenic-etl:latest` through `work/run_stage.sh`, except
  pass 2, which is the chunk loop and ran as one detached driver (`work/pass2.sh`, log kept at
  `work/pass2.log`).
  PASS 2, `python -m etl.assemble --reference /fast/la-reference.json` per tile, ten at a time, 27-76 s a
  tile: `PASS2 SWEEP END 152 scored of 152 docs`. Totalled over the 152 `ASSEMBLE` lines:
      `PASS2 TOTALS ways=574396 zero_class=20286 gated=106117 sinuosity_declined=21414
       points_of_interest_absent=574396 null_score=0`
  (those are per-tile sums, so a seam way is counted in both its tiles; the merge below deduplicates.)
  MERGE + THE SEAM RE-MEASURE, `work/pass3_merge.py`, first-tile-in-sorted-order wins:
      `MERGE tiles=152 ways=560304 seam_ways=13946 seam_differ=0 refused=0 52s`
      `MERGE ASSEMBLE ways=560304 zero_class=19511 gated=103989 sinuosity_declined=21297
       points_of_interest_absent=560304 null_score=0`
  13,946 WAYS ARE DOCUMENTED IN TWO TILES AND 0 OF THEM DISAGREE. T-0204's measurement was 160 of 190 on
  one seam. `zero_class=19511` is exactly the region motorway set R1b cut (`Number of ways: 19511`), which
  is the independent check that `population_of` dropped the four zero classes and nothing else.
  TAGWRITER over the whole `la-filtered.osm.pbf` (577,026,283 B as XML), 3m51s:
      `WRITE ways=565874 scored=560304 refused=0 gated=103989 not_a_road=5570`
  565,874 - 5,570 = 560,304: every road way in the clip carries a score and none was refused.
  CHECK4 over an `osmium cat` READ-BACK of the PBF, 1m17s:
      `CHECK4 null_score=0 gated_scored=0 malformed=0 scored=560304 refused=0 not_a_road=5570`
  malformed=0 over the whole region - T-0204's windows carried 2 and 15.
  T-0207's CLASS CEILING, re-measured over that same read-back (`work/ceiling.py`), 6m30s:
      `CEILING residential_or_living_street_at_7_or_above=0 service_above_0=0  (key scenic_score)`
      service 312,645 ways max_score=0 · residential 99,715 max 6 · living_street 195 max 6 ·
      primary 43,815 max 9 · secondary 42,237 max 8 · tertiary 25,380 max 8 · unclassified 5,460 max 8 ·
      motorway 7,486 max 0 · motorway_link 9,908 max 0 · trunk 1,939 max 0 (7,486+9,908+1,939+178 trunk_link
      = the 19,511 zero-class ways: PENALISED AND IN THE CORPUS, never excluded).
  THE ARTIFACT: `services/etl/work/la/la-tagged.osm.pbf`, sha256
  `648fc3dbb80c8e845ff265ef7eda4a7b2f9434b89c0a1bdd671ce0b2dcff3d39`, 45,914,107 bytes, copied to the MAIN
  checkout and re-hashed there to the same digest. T-0209 imports this and scores nothing.
- 2026-09-19T21:59:24Z THE THREE WINDOWS, cut OUT OF THE SHIPPED ARTIFACT with `osmium extract` and read
  back with `osmium cat`, ranked by `etl.scenecheck.top` (`work/windows.sh`, `work/windows_top.py`). The
  ASSEMBLE count line of each window's own population is quoted BESIDE its top ten (11:13 panel), because
  a top ten that moved has to be attributable to the population: gated ways ARE ranked (`score.py:29-32`
  applies `GATE_SCORE` after the rank) and `population_of` excludes only `is_zero_class`.
      whole region  `MERGED ASSEMBLE ways=560304 zero_class=19511 gated=103989 null_score=0`
      canyon  -118.95,33.98,-118.55,34.15
        `WINDOW canyon  ASSEMBLE ways=11740 zero_class=386 gated=5589 sinuosity_declined=619 null_score=0`
        `WINDOW canyon  CHECK4 null_score=0 gated_scored=0 malformed=0 scored=11740 refused=0 not_a_road=662`
      grid-a  -118.55,33.98,-118.45,34.15
        `WINDOW grid-a  ASSEMBLE ways=11239 zero_class=476 gated=1927 sinuosity_declined=575 null_score=0`
        `WINDOW grid-a  CHECK4 null_score=0 gated_scored=0 malformed=0 scored=11239 refused=0 not_a_road=212`
      grid-b  -118.45,33.98,-118.35,34.15
        `WINDOW grid-b  ASSEMBLE ways=23474 zero_class=772 gated=3696 sinuosity_declined=1074 null_score=0`
        `WINDOW grid-b  CHECK4 null_score=0 gated_scored=0 malformed=0 scored=23474 refused=0 not_a_road=413`
  THE SEAM, MEASURED ON THE ARTIFACT ITSELF: `SEAM overlapping=190 differ=0` - the same 190 ways T-0204
  found in both halves of the grid window, and NOT ONE of them differs. The two ways the Brief named:
      `NAMED way 1533792498 Mulholland Drive      a=0.6952 b=0.6952`   (T-0204: 0.6988 vs 0.7022)
      `NAMED way 399301293  West Sunset Boulevard a=0.6203 b=0.6203`   (T-0204: 0.6308 vs 0.6372)
  THE TOP TENS, new beside old (old = `git show HEAD:` the fixtures this commit replaces):
      CANYON   new                                             old
       1 667514937 N Topanga Canyon Blvd  0.8012        74344132   Topanga Canyon Blvd     0.7722
       2 74344113  Topanga Canyon Blvd    0.7965        74344113   Topanga Canyon Blvd     0.7697
       3 74344132  Topanga Canyon Blvd    0.7891        667514937  N Topanga Canyon Blvd   0.7679
       4 38311860  Topanga Canyon Blvd    0.7704        358703394  Stunt Road              0.7563
       5 358703394 Stunt Road             0.7691        456361801  N Topanga Canyon Blvd   0.7464
       6 1165966476 N Topanga Canyon Blvd 0.7660        38311860   Topanga Canyon Blvd     0.7401
       7 204589613 N Topanga Canyon Blvd  0.7655        1079750100 Old Topanga Canyon Rd   0.7367
       8 1255479697 Old Topanga Canyon Rd 0.7648        46752395   Old Topanga Canyon Rd   0.7314
       9 456361801 N Topanga Canyon Blvd  0.7637        13346012   Piuma Road              0.7306
      10 13409451  S Topanga Canyon Blvd  0.7594        1237332026 Fernwood Pacific Drive  0.7284
      GRID     new                                             old
       1 518410361 Mulholland Drive       0.7325        518410361  Mulholland Drive        0.7361
       2 518410363 Mulholland Drive       0.7236        787842196  Mulholland Drive        0.7299
       3 787842196 Mulholland Drive       0.7218        44327906   Mulholland Drive        0.7261
       4 44327906  Mulholland Drive       0.7206        13419334   Crescent Drive (resid.) 0.7228
       5 13292286  Franklin Canyon Drive  0.7128        632613339  Sullivan Fire Rd (serv.) 0.7227
       6 399262414 Laurel Canyon Blvd     0.7034        518410363  Mulholland Drive        0.7226
       7 159524496 Mulholland Drive       0.7026        13290126   Sullivan Ridge FR (serv.) 0.7215
       8 405362186 Mulholland Drive       0.7020        13292286   Franklin Canyon Drive   0.7203
       9 518410359 Mulholland Drive       0.7009        13379402   Scenario Lane (resid.)  0.7201
      10 13377650  Mandeville Canyon Rd   0.6991        121304178  Oakmont Street (resid.) 0.7189
  TWO THINGS TO SAY PLAINLY. (a) The old grid top ten held a residential street and two service fire
  roads at 0.72; T-0207's ceiling caps residential at 0.6499 and service at 0.0, so those fixtures were
  older than the ceiling and this re-record is also the first time the grid window's top ten obeys it.
  (b) THE RIDGE ALLOWLIST IS NOW EMPTY. `RIDGE_ALLOWLIST` held ways 518410361 and 787842196 because they
  reached the canyon window's tenth (0.7284). Both are STILL the grid window's best roads - ranks 1 and 3,
  the crest is still inside the bbox - but the canyon window's tenth is now 0.7594 (way 13409451, South
  Topanga Canyon Boulevard) and the grid window's best is 0.7325, so NO grid way reaches the bound and the
  allowlist shrinks to nothing. It was re-derived from the measurement and not re-ranked to keep a way in
  it (R4). An empty whitelist can pass over nothing, so `test_the_two_mulholland_ridge_segments_are_still_
  the_grid_windows_best_and_are_now_below_the_bound` names both ways and asserts exactly that, and
  `test_the_read_finds_a_way_that_reaches_the_bound` requires the same read to find all ten when they are
  raised over the bound.
  THE FIXTURES, all four re-recorded in THIS ONE COMMIT (R4): `canyon_top25.json` (6,497 B),
  `grid_top25.json` (36,806 B, carrying `seam_ways` - all 190 with both halves' units - and
  `seam_differ: 0`), `grid_tie_top25.json` (6,607 B, DERIVED: the grid window's best way RAISED onto the
  bound, because under the region reference nothing has to be lowered to make a tie), and
  `window_readback_sample.osm.xml` (71,718 B, four real ways cut with `osmium getid -r` out of the canyon
  window's own read-back: `SAMPLE CHECK4 null_score=0 gated_scored=0 malformed=0 scored=4 ... rows=4`,
  ways 667514937 · 358703394 · 13409451 · 1237330475, one of them the bound way itself).
  `test_window_ranking.py` re-derived in the same commit: BOUND_WAY_ID 1237332026 -> 13409451, BOUND_NAME
  "Fernwood Pacific Drive" -> "South Topanga Canyon Boulevard", BOUND_UNIT 0.7284 -> 0.7594,
  RIDGE_ALLOWLIST {518410361, 787842196} -> {}, and `test_the_seam_merge_rule_is_recorded_and_the_rows_
  obey_it` -> `test_the_seam_ways_are_recorded_and_every_one_of_them_carries_ONE_score` (R8), which pins
  `len(seam_ways) == 190` so it cannot pass over an empty list. 222 lines. Suite: `1242 passed`.
- 2026-09-25T21:08:06Z (R9) THE MERGE OF origin/main RULED by agent/claude-opus-5 (owner), resuming after the
  2026-09-19 usage-limit stop. `git fetch origin && git merge --no-edit origin/main` (006c798, PRs #119-#128)
  onto b519a88: ONE conflict, `ops/lib/check-mutate-population.py` DRIVERS - main added `plan.py` and
  `straightline.py`, this branch `normalise.py`. RESOLVED AS THE UNION, 15 drivers. COVERED_FLOOR merged
  without a conflict to the union: main's 34 plus `normalise.py` and `region_reference.py`, 36. The union
  took the gate to 302 lines against the 300-line cap (main left it at exactly 300), so the three DATA
  tables - DRIVERS, PROBES, COVERED_FLOOR - MOVED, content unchanged, into a sibling
  `ops/lib/mutate_population_table.py` (100644, importable beside the gate exactly as
  `mutate_population_red.py` is). The gate imports them at module scope and a missing sibling is the gate's
  own refusal, not a traceback - SEEN RED: with the sibling moved aside, `P-PROC-06:
  ops/lib/mutate_population_table.py is not importable: No module named 'mutate_population_table'`, exit 2;
  restored, exit 0. TOUCHES AMENDED: `ops/lib/mutate_population_table.py` added, nothing else in ops/lib/.
  `services/etl/etl/assemble.py` merged WITHOUT a conflict and carries BOTH #122's
  `from .accessrule import ...` (the access rules re-exported) and this branch's `region_reference` import
  and `--reference` plumbing.
  `--prove-red` BEFORE THE MERGE COMMIT read `git arm: ... 1 2 NOT DISCRIMINATING` on all three real-git
  cases: the git arm CLONES THE COMMITTED HEAD (`git clone root`), which was still pre-merge b519a88 and
  lacks main's `plan.py`/`straightline.py` drivers the merged table names, so every clone was a
  fail-closed exit 2. Main's own checkout reads `all 13 cases behaved as stated`. It is re-run on the
  committed merge below and quoted there; an uncommitted merge is not the tree the gate is proved on.
- 2026-09-25T22:43:08Z THE ACCEPTANCE BLOCK, RE-RUN BARE ON THE MERGED HEAD 6c96af0, and the 8/10 hand-over.
  `git fetch origin` first: origin/main is still 006c798, the commit R9 merged, and
  `git merge-base --is-ancestor origin/main HEAD` exits 0, so no second merge was taken. Every line below is
  quoted from a run on this head, with every `__pycache__` under services/etl purged before each Python run.
  PYTEST, `cd services/etl && python -m pytest tests -rs -o addopts=`: `1331 passed in 198.18s (0:03:18)`,
  exit 0, and `-rs` printed NO skip line - zero skips. (1242 before the merge, at 21:59:24Z; the other 89 are
  main's.) THE SEAM TEST BY NAME, `tests/test_seam_one_score.py`: `4 passed`, among them
  `test_a_way_in_two_overlapping_windows_takes_one_score_against_the_region_reference PASSED` and
  `test_without_a_region_reference_the_same_ways_take_two_scores PASSED`.
  `python ops/mutate/normalise.py`: `MUTATIONS: 18 caught, 0 missed, 0 skipped, of 18` /
  `EQUIVALENT: 0 caught, 2 missed, 0 skipped, of 2` / `MUTATE OK  caught=18/18 equivalent_caught=0`, exit 0.
  `python ops/mutate/normalise.py --prove-vacuity` (its one flag, read from its argparse first):
  `VACUITY: 0 caught, 18 missed, 0 skipped, of 18` / `VACUITY PROVED`, exit 0.
  `python ops/mutate/scenic_tags.py`: `MUTATIONS: 48 caught, 0 missed, 0 skipped, of 48` /
  `EQUIVALENT: 0 caught, 3 missed, 0 skipped, of 3` / `MUTATE OK  caught=48/48 equivalent_caught=0`, exit 0.
  `python ops/mutate/extractadapter.py` (main's, #122, on this merged head): `MUTATIONS: 27 caught, 0 missed,
  0 skipped, of 27` / `EQUIVALENT: 0 caught, 3 missed, 0 skipped, of 3` / `MUTATE OK  caught=27/27
  equivalent_caught=0`, exit 0. `git status --short` empty after each driver restored its subjects.
  `python ops/lib/check-mutate-population.py`: `P-PROC-06: 91 modules, 37 covered by 15 populations,
  33 allowlisted, 1 added by this branch` / `P-PROC-06: every added module is covered or allowlisted; the
  floor of 36 holds`, exit 0. `--prove-red` ON THE COMMITTED MERGE, the re-run R9 promised: `P-PROC-06
  --prove-red: all 13 cases behaved as stated`, exit 0 - the three git-arm cases that read NOT DISCRIMINATING
  on the pre-merge b519a88 clone now read `1 1 ok`, `0 0 ok`, `1 1 ok`.
  THE ARTIFACT, re-hashed in the MAIN checkout: `sha256sum services/etl/work/la/la-tagged.osm.pbf` =
  `648fc3dbb80c8e845ff265ef7eda4a7b2f9434b89c0a1bdd671ce0b2dcff3d39`, `stat -c %s` = `45914107` - the digest
  and the byte count 21:59:24Z quoted, unchanged.
  `bash ops/lib/check-line-cap`: `P-SRC-02: 111 Swift files tracked (Sources=43, Tests=47, apps/ios=21), none
  over 300 lines`, exit 0 (Swift only; the Python this branch touches is measured by `wc -l` next).
  `bash ops/lib/check-exec-bits`: `P-OPS-01: 98 files, 23 required present, all modes correct`, exit 0.
  `bash ops/queue-check`: `QUEUE OK (229 tasks)`, exit 0.
  `wc -l`, every non-fixture file in `git diff --name-only origin/main...HEAD`:
      ops/lib/check-mutate-population.py 283 · ops/lib/mutate_population_table.py 37 ·
      ops/mutate/normalise.py 171 · ops/mutate/normalise_mutations.py 130 ·
      services/etl/etl/assemble.py 293 · services/etl/etl/normalise.py 256 ·
      services/etl/etl/region_reference.py 109 · services/etl/etl/waydoc.py 288 ·
      services/etl/tests/test_motorway_source.py 70 · test_region_reference.py 142 ·
      test_seam_one_score.py 102 · test_window_ranking.py 222.
  assemble.py is 293, not the 299 the 18:05 entry quoted: #122 moved the access rules out into
  `accessrule.py`, and the merge kept both that import and this branch's `--reference` plumbing.
  THE 8/10 HAND-OVER. Each window's top ten, read OFF THE SHIPPED ARTIFACT: the `osmium cat` read-backs of
  the three windows cut out of `la-tagged.osm.pbf` (21:59:24Z), ranked by `etl.scenecheck.top` and ordered
  (score desc, unit desc, way_id asc) by `work/handover_top.py`. It ran against the COMMITTED HEAD's `etl`
  package (`git archive 6c96af0 services/etl/etl`, bound first by `work/handover_run.py`) because the
  worktree's `etl/` was being mutated by `scenic_tags.py` at the time. Its first line re-derives the region:
  `MERGED ASSEMBLE ways=560304 zero_class=19511 gated=103989 sinuosity_declined=21297
  points_of_interest_absent=560304 null_score=0` - the 21:59:24Z line, byte for byte. REGION = this
  task's region-normalised unit and the 0-10 tag written into the PBF; OLD = the pre-T-0208 window-relative
  unit (canyon_top25.json; grid_top25.json, with its seam_disagreements for each half's own value), `-` where
  no old top-25 named the way.
      CANYON  -118.95,33.98,-118.55,34.15
       #  way         name                             highway       tag  region  old
       1  667514937   North Topanga Canyon Boulevard   primary        8   0.8012  0.7679
       2  74344113    Topanga Canyon Boulevard         primary        8   0.7965  0.7697
       3  74344132    Topanga Canyon Boulevard         primary        8   0.7891  0.7722
       4  38311860    Topanga Canyon Boulevard         primary        8   0.7704  0.7401
       5  358703394   Stunt Road                       tertiary       8   0.7691  0.7563
       6  1165966476  North Topanga Canyon Boulevard   primary        8   0.7660  0.7116
       7  204589613   North Topanga Canyon Boulevard   primary        8   0.7655  -
       8  1255479697  Old Topanga Canyon Road          secondary      8   0.7648  0.7275
       9  456361801   North Topanga Canyon Boulevard   primary        8   0.7637  0.7464
      10  13409451    South Topanga Canyon Boulevard   primary        8   0.7594  -
      `WINDOW canyon ASSEMBLE ways=11740 zero_class=386 gated=5589 sinuosity_declined=619
       points_of_interest_absent=11740 null_score=0`
      GRID-A  -118.55,33.98,-118.45,34.15
       #  way         name                             highway       tag  region  old
       1  44327906    Mulholland Drive                 secondary      7   0.7206  0.7261
       2  405362186   Mulholland Drive                 secondary      7   0.7020  0.7064
       3  13377650    Mandeville Canyon Road           tertiary       7   0.6991  0.7125
       4  1533792498  Mulholland Drive                 secondary      7   0.6952  0.6988
       5  435695311   Temescal Canyon Road             unclassified   7   0.6672  -
       6  399156621   West Sunset Boulevard            secondary      7   0.6661  -
       7  13377647    Mandeville Canyon Road           tertiary       7   0.6595  -
       8  13278980    Round Valley Drive               residential    6   0.6499  0.6746
       9  13278983    Round Valley Drive               residential    6   0.6499  -
      10  13285888    Rivers Road                      residential    6   0.6499  -
      `WINDOW grid-a ASSEMBLE ways=11239 zero_class=476 gated=1927 sinuosity_declined=575
       points_of_interest_absent=11239 null_score=0`
      GRID-B  -118.45,33.98,-118.35,34.15
       #  way         name                             highway       tag  region  old
       1  518410361   Mulholland Drive                 secondary      7   0.7325  0.7361
       2  518410363   Mulholland Drive                 secondary      7   0.7236  0.7226
       3  787842196   Mulholland Drive                 secondary      7   0.7218  0.7299
       4  13292286    Franklin Canyon Drive            unclassified   7   0.7128  0.7203
       5  399262414   Laurel Canyon Boulevard          secondary      7   0.7034  0.7081
       6  159524496   Mulholland Drive                 secondary      7   0.7026  0.7100
       7  518410359   Mulholland Drive                 secondary      7   0.7009  -
       8  1533792498  Mulholland Drive                 secondary      7   0.6952  0.7022
       9  38555783    Laurel Canyon Boulevard          secondary      7   0.6928  -
      10  518410362   Mulholland Drive                 secondary      7   0.6922  -
      `WINDOW grid-b ASSEMBLE ways=23474 zero_class=772 gated=3696 sinuosity_declined=1074
       points_of_interest_absent=23474 null_score=0`
  THREE THINGS THE OWNER SHOULD KNOW BEFORE ANSWERING "HOW MANY OF THESE TEN WOULD YOU DRIVE". (a) Way
  1533792498, Mulholland Drive, is in BOTH grid tables - grid-a #4 and grid-b #8 - at ONE value, 0.6952,
  where the old windows gave it 0.6988 and 0.7022: the seam fix, visible in the hand-over itself. (b) Grid-a
  #8-#10 are residential ways sitting AT T-0207's residential ceiling, 0.6499 (tag 6): they are TIED, and
  a tie is ordered by way_id, so WHICH residential street is 8th, 9th or 10th is not a scenic claim.
  MEASURED over the same read-back (`work/handover_ties.py`, same HEAD package):
      `TIES grid-a tenth_unit=0.6499 tied_at_tenth=31 above_tenth=7 classes={'residential': 31}`
      `TIES grid-a distinct_names=30 first=Round Valley Drive, Rivers Road, Bel Air Road, Beverly Glen
       Terrace, Rivas Canyon Road, Mango Way, Antelo View Drive, Mulholland Place`
      `TIES canyon tenth_unit=0.7594 tied_at_tenth=1 above_tenth=9` · `TIES grid-b tenth_unit=0.6922
       tied_at_tenth=1 above_tenth=9`
  so grid-a has SEVEN ranked roads above the ceiling and then 31 residential ways (30 streets) tied on it;
  the owner's answer for grid-a is really about #1-#7 plus "a Bel Air / Brentwood hillside residential".
  Canyon and grid-b have no tie at the tenth. (c) The ways, zero_class, gated, sinuosity_declined and
  null_score counts under each table equal the 21:59:24Z entry's (that entry did not print
  points_of_interest_absent), so these tables are the artifact T-0209 imports, not a re-run.
- 2026-09-25T23:33:36Z (R10) ROUND 2 RULED by agent/claude-opus-5 (owner), before any code, on rv1-t0208's
  FAIL (.artifacts/signoffs/rv1-t0208-verdict.md, read in full). B1 and B2 ACCEPTED as written. R1 is recorded
  below and not done here. R2-R5 are noted and change no code.
  (B1) ACCEPTED: the shipping symbol is `assemble.main`, not `assemble.assemble`. Pass 2 ran
  `python3 -m etl.assemble --input <tile>-doc.json --out ... --reference /fast/la-reference.json` on all 152
  tiles, and `python -m etl.assemble` runs `main()`. So R3's "the entry point python -m etl.assemble runs" named
  the wrong symbol, and so did test_seam_one_score.py's "WHAT THIS FILE BINDS TO" paragraph. That docstring is
  corrected in the same commit. It is a test file's prose, not the Log, so this is not a history edit.
  THE FIX: two tests in test_seam_one_score.py that call `assemble.main` itself.
  (i) The WITH-REFERENCE path. seam_window_a/b are copied into tmp_path. The reference is written by
  `region_reference.dump` over the same union `reference_over` builds, which is the file pass 2 read. Then
  `main(['--input', doc, '--out', out, '--reference', ref])` runs for each window. The test asserts that every
  shared way has ONE score, and names T-0204's two ways in the shared set.
  (ii) The WITHOUT-REFERENCE path, which is legitimate for one self-contained document. `main` without the
  flag must equal `assemble.assemble(doc)` for each window, and Mulholland still takes two scores. That binds
  both of the flag's paths through the shipping symbol.
  (B2) ACCEPTED, the same gap one layer down. Pass 1 ran `python3 -m etl.waydoc ... --motorways
  work/la-motorways.osm.xml`, and the test bound only `waydoc.build(motorway_source=...)`.
  THE FIX: two tests in test_motorway_source.py that call `waydoc.main` itself.
  (i) With `--motorways region_motorways.osm.xml`, way 101's distance must equal `build`'s region-set answer
  and lie past `score.MOTORWAY_PROXIMITY_M`.
  (ii) Without the flag, it must equal the clip's own answer, 0.0.
  The CLI has no seam for the DEM or the landcover sampler, and the distance does not depend on either. So
  `dem.tiles_for_region`, `dem.sample_smoothed` and `waydoc.default_landcover` are stubbed with pytest's
  monkeypatch at the module attributes `build` reads at call time. `--no-byways` is passed because the byway
  overlay is not the motorway set and reads a real inputs file.
  THE POPULATION: four named mutants go into ops/mutate/normalise_mutations.py, two per flag.
  (1) The reviewer's B1 mutant: `table = assemble(document)`.
  (2) Its mirror: a reference loaded when none was given.
  (3) The reviewer's B2 mutant: `motorway_source=None)`.
  (4) Its mirror: `pathlib.Path(args.motorways)` read unconditionally.
  MIN_MUTATIONS goes from 18 to 22. waydoc.py joins SUBJECTS, the files the driver restores and guards against
  HEAD, and test_motorway_source.py joins EMPTIED, so `--prove-vacuity` still covers all 22. waydoc.py is NOT
  added to SUBJECT_MODULES. It is allowlisted as wiring (ops/lib/mutate-population-allowlist.json), and
  P-PROC-06 refuses an allowlist entry for a module a population declares. Mutating a wiring line from a
  population that does not claim the module is what this file already does for assemble.py. The comments that
  say "two layers" and "the single line" are corrected to three layers and to the lines named.
  Each of the four is to be seen RED BY NAME, applied from the population entry itself, before the commit.
  (R1) RECORDED, NOT DONE HERE: the pipeline scripts that built la-tagged.osm.pbf live only in this worktree's
  gitignored services/etl/work/: pass1.sh, pass1c.sh, pass2_reference.py, pass2.sh, pass3_merge.py,
  run_stage.sh, windows.sh, windows_top.py and handover_*.py. The first-tile-wins merge of scored rows and the
  seam_differ count exist only in pass3_merge.py. `touches:` names ops/etl-extract, but this branch never
  touched it. So the artifact cannot be rebuilt from the tree. THE ORCHESTRATOR FILES A TASK to commit the
  region driver under ops/ or etl/, with a test through its entry point.
  (R2, R3) The reviewer's reconciliations are recorded here as the later notes they ask for. The dated
  21:29:46Z entry is left unedited.
  - R2: 560,304 unique ways per the MERGE line, and 96 scored ways fall outside meta.json's per-class sum.
  - R3: 268 zero-class ways must also have declined sinuosity for 519,764 to reconcile.
  Neither was re-measured in this round. (R4) belongs to T-0207. (R5) noted: the floor lives in
  normalise_mutations.py.
- 2026-09-25T23:36:38Z (R10) RED BY NAME, THEN GREEN, quoted from the run.
  HOW IT WAS RUN: `python services/etl/work/r2_red_green.py`, a gitignored helper. It imports MUTATIONS from
  ops/mutate/normalise_mutations.py and applies each of the four `python -m etl.` entries from the population
  entry itself, never from a retyped string. Before each run it purges every `__pycache__` and sleeps 1.1 s.
  It runs the four new CLI tests by node id, sleeps 1.1 s, restores and purges.
  - PRISTINE-BEFORE `exit=0`, `4 passed`.
  - B1: `MUTANT [assemble.py] python -m etl.assemble drops --reference, so every tile is ranked against itself
    again (rv1-t0208 B1)  exit=1`. Result:
    `FAILED tests/test_seam_one_score.py::test_the_cli_with_a_region_reference_gives_a_way_in_two_windows_one_score`,
    `1 failed, 3 passed`.
  - Its mirror: `MUTANT [assemble.py] python -m etl.assemble loads a reference that was never given, so one
    self-contained window cannot run  exit=1`. Result: `FAILED tests/test_seam_one_score.py::
    test_the_cli_without_a_reference_ranks_one_self_contained_window_against_itself`, `1 failed, 3 passed`.
  - B2: `MUTANT [waydoc.py] python -m etl.waydoc drops --motorways, so the clip's own motorways are measured to
    (rv1-t0208 B2)  exit=1`. Result: `FAILED tests/test_motorway_source.py::
    test_the_cli_measures_to_the_region_motorway_file_it_is_given`, `1 failed, 3 passed`.
  - Its mirror: `MUTANT [waydoc.py] python -m etl.waydoc reads a motorway file that was never given, so a
    self-contained clip cannot run  exit=1`. Result: `FAILED tests/test_motorway_source.py::
    test_the_cli_without_a_motorway_file_measures_to_the_clips_own_motorways`, `1 failed, 3 passed`.
  - PRISTINE-AFTER `exit=0`, `4 passed`.
  Each mutant turns exactly the test written for it red, and no other. After the helper, `git status --short`
  listed only the five files this round edits. assemble.py and waydoc.py were not among them, so both were
  restored. The two files, whole: `pytest tests/test_seam_one_score.py tests/test_motorway_source.py
  -o addopts=` = `11 passed`. The driver runs next, on the COMMITTED tree, because it refuses a dirty one.
- 2026-09-25T23:52:39Z (R10) THE ACCEPTANCE BLOCK, RE-RUN BARE ON THE MERGED HEAD 694ef87.
  THE MERGE. The code commit is 0fa13f7. Then `git fetch origin`: origin/main had moved to 86ac9d5, and
  `git merge-base --is-ancestor origin/main HEAD` exited 1. `git merge --no-edit origin/main` made 694ef87.
  It brought in two backlog task files, T-0237 and T-0238, and no conflict.
  Every Python run below purged every `__pycache__` under services/etl first.
  PYTEST, `cd services/etl && python -m pytest tests -rs -o addopts=`: `1335 passed in 223.77s (0:03:43)`,
  exit 0. That is 1331 plus this round's 4. `-rs` printed no SKIPPED line, so there were zero skips.
  THE NEW TESTS BY NAME, `-v`, `4 passed`, exit 0:
  - `test_the_cli_with_a_region_reference_gives_a_way_in_two_windows_one_score PASSED`
  - `test_the_cli_without_a_reference_ranks_one_self_contained_window_against_itself PASSED`
  - `test_the_cli_measures_to_the_region_motorway_file_it_is_given PASSED`
  - `test_the_cli_without_a_motorway_file_measures_to_the_clips_own_motorways PASSED`
  `python ops/mutate/normalise.py`, exit 0:
  - `BASELINE exit=0, 22 mutations, floor 22`
  - B1 caught: `python -m etl.assemble drops --reference, so every tile is ranked against itself again
    (rv1-t0208 B1)  <- tests/test_seam_one_score.py::test_the_cli_with_a_region_reference_gives_a_way_in_two_windows_one_score`
  - B2 caught: `python -m etl.waydoc drops --motorways, so the clip's own motorways are measured to (rv1-t0208
    B2)  <- tests/test_motorway_source.py::test_the_cli_measures_to_the_region_motorway_file_it_is_given`
  - The two mirrors were caught by the two without-flag tests.
  - `MUTATIONS: 22 caught, 0 missed, 0 skipped, of 22` / `EQUIVALENT: 0 caught, 2 missed, 0 skipped, of 2` /
    `MUTATE OK  caught=22/22 equivalent_caught=0`
  `python ops/mutate/normalise.py --prove-vacuity`: `VACUITY: 0 caught, 22 missed, 0 skipped, of 22` /
  `VACUITY PROVED`, exit 0. `git status --short` was empty after both driver runs.
  `python ops/lib/check-mutate-population.py`, exit 0:
  - `P-PROC-06: 91 modules, 37 covered by 15 populations, 33 allowlisted, 1 added by this branch`
  - `P-PROC-06: every added module is covered or allowlisted; the floor of 36 holds`
  These are the same totals as 22:43:08Z. waydoc.py is still allowlisted and still declared by no population.
  `bash ops/lib/check-line-cap`: `P-SRC-02: 111 Swift files tracked (Sources=43, Tests=47, apps/ios=21), none
  over 300 lines`, exit 0. `bash ops/lib/check-exec-bits`: `P-OPS-01: 98 files, 23 required present, all modes
  correct`, exit 0. `bash ops/queue-check`: `QUEUE OK (231 tasks)`, exit 0.
  `wc -l`, re-measured because this round touched these files: test_seam_one_score.py 143,
  test_motorway_source.py 103, ops/mutate/normalise_mutations.py 148, ops/mutate/normalise.py 173.
  Unchanged and quoted for the cap: assemble.py 293, waydoc.py 288.
  `git ls-files -s`: both ops/mutate files are 100644.
  THE ARTIFACT IS UNTOUCHED. `git diff --stat 34db62c HEAD -- services/etl/etl/` is empty: no module changed
  this round. The main checkout's `sha256sum services/etl/work/la/la-tagged.osm.pbf` =
  `648fc3dbb80c8e845ff265ef7eda4a7b2f9434b89c0a1bdd671ce0b2dcff3d39`, and `stat -c %s` = `45914107`. That is
  the digest and byte count 21:59:24Z quoted, so acceptance lines 2 and 3 stand as quoted there.
