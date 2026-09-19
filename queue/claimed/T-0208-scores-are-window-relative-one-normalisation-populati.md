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
touches: [services/etl/etl/, services/etl/tests/, ops/etl-extract, ops/mutate/]
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
