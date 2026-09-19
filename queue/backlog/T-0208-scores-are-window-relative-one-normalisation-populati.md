---
id: T-0208
title: scores are window-relative - one normalisation population per REGION: the LA clip scored in chunks against a single reference so a way's score does not depend on which window it was clipped into
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: [scenic-index]
touches: [services/etl/etl/, services/etl/tests/, ops/etl-extract, ops/mutate/]
pins_affected: []
reviewer: null
depends_on: [T-0204, T-0207]
verify: [ops/test, ops/check-pins]
acceptance:
  - "RED BY NAME first: a test over a fixture way present in two overlapping windows asserting ONE score (T-0204 measured 160 of 190 seam ways with different scores across grid-a/grid-b: Mulholland Drive way 1533792498 0.6988 vs 0.7022; West Sunset Boulevard way 399301293 0.6308 vs 0.6372), red today, then green once the rank-normalisation reference (normalise_region's 'reference' population) is the whole region's, computed once and passed to every chunk"
  - "the LA clip (561,000 ways) scored in chunks that each finish in one foreground container call, the reference population recorded (count, sha256 of the reference table) and the seam re-measured: 0 of N seam ways differ; the three windows' top tens re-quoted"
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
