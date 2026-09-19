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
