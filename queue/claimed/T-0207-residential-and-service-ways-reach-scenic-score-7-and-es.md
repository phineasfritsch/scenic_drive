---
id: T-0207
title: residential and service ways reach scenic_score 7 and escape the anti-rat-run clause - rule a class cap (score or profile) with the LA grid window's hillside streets and fire roads as the fixture
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T11:30:53Z
lease_expires_at: 2026-09-19T17:30:53Z
worktree: .worktrees/T-0207
branch: task/T-0207
exclusive: []
touches: [services/etl/etl/, services/etl/tests/, ops/mutate/]
pins_affected: []
reviewer: null
depends_on: [T-0204]
verify: [ops/test, ops/check-pins]
acceptance:
  - "RULED in the Log before code, with the plan's profile block quoted (road_class == RESIDENTIAL && scenic_score < 7 -> 0.5): T-0204's grid window puts Crescent Drive, Scenario Lane and Oakmont Street (highway=residential) and Sullivan Fire Road / Sullivan Ridge Fire Road (highway=service) at scenic_score 7 (unit 0.7189-0.7228), so the router's rat-run demotion never touches them; rule WHERE the cap lives (score.py class factor, the quantiser, or the routing profile's threshold) and what it is for residential, living_street, service and unclassified"
  - "RED BY NAME first on a fixture of those five real rows (from services/etl/tests/fixtures/grid_top25.json): no residential/living_street/service way quantises to >= 7 (or the profile clause demotes it regardless) - then green; the ops/mutate population for the touched module gains the cap's mutants with the floor raised"
  - "tagwriter writes ONE number twice: scenic_score is quantise() of the UNROUNDED score while scenic_score_unit is the score fixed at four decimals, so 17 of 46,436 real ways (1 grid-a, 14 grid-b, 2 canyon; e.g. way 13332407 ships 5 beside 0.5500) fail the hardened oracle's quantise(unit) == score clause - quantise the SAME rounded value the unit carries, RED BY NAME first on a fixture row at a .x5 fourth-decimal boundary, then green; the three real read-backs re-checked: malformed=0"
  - "cd services/etl && python -m pytest tests -rs -o addopts= count line and zero skips; the canyon window's top ten unchanged (quoted)"
---
## Brief

From T-0204's real run (PR #113): in the Westwood/Brentwood/Bel Air window the top ten holds three residential
hillside streets and two service fire roads at scenic_score 7, one unit-score hair under Topanga's tenth (0.7284).
The plan's anti-rat-run rule only demotes RESIDENTIAL ways scoring BELOW 7, and the owner's bar is zero rat-runs -
one cut-through past a school and the app is deleted. T-0168 recorded the service-way half as STILL OPEN 3. The
four bits do not separate Topanga from a Bel Air cul-de-sac; something class-aware must.

## Log
- 2026-09-19T09:51:35Z filed by agent/claude-fable-5-1 from T-0204's grid-window top ten. Not started. Safety-adjacent: before T-0031's second half routes over LA scores.
- 2026-09-19T11:17:30Z bullet added by agent/claude-fable-5-1 from T-0204's fixer and rv1-pr113 (PR #113, merged): the hardened oracle found malformed=17 on real data, cause read out of tagwriter.tags_for_row. Same module and same re-run as the class cap, so it lands here.
- 2026-09-19T11:17:30Z PROMOTED to ready/ by agent/claude-fable-5-1: #113 (T-0204) merged, its fixture is on main; the 03:13 panel's NEXT START (safety: zero rat-runs).
- 2026-09-19T11:30:53Z claimed by agent/claude-opus-5; lease until 2026-09-19T17:30:53Z
