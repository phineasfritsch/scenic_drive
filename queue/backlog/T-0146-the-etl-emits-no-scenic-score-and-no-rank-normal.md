---
id: T-0146
title: the ETL emits no scenic_score and no rank-normalised terms, so ScenicKit's SegmentTerms has no producer
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/etl/, services/etl/tests/]
pins_affected: []
reviewer: null
depends_on: [T-0154, T-0024, T-0025, T-0026, T-0027, T-0161, T-0162, T-0163]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Panel CODE lens, grounded: 17 modules / 2,101 lines under services/etl/etl/ are all input-side (fetch, dem,
landcover, curvature, terrain, snap, tagfilter, byways). `git grep scenic_score -- services/etl/` returns no
code hit; rank-normalisation appears once, as a comment (byways.py:108). Meanwhile
Sources/ScenicKit/Scoring/SegmentTerms.swift's contract is "every term is rank-normalised or scaled by the
ETL before it arrives" and SegmentScore.score returns nil rather than clamping - wire the two today and every
way scores nil. ScoredEdge.swift cites `score.py` and "the gate-parity fixture"; neither exists.

This is M2's core. Do: `services/etl/etl/score.py` computing the plan's terms per way (M = curv, elev_gain,
speed_fit, sinuosity; E = canopy, relief, 1-impervious, poi, water, 1-furniture; byway bonus capped), rank-
normalising each within the region, applying the GATE (the plan's positive-evidence list; motorway/trunk
score 0 and stay routable), and writing `scenic_score` 0..10 plus the terms to the tagged output. Tests:
motorway/trunk/private/unpaved score exactly 0.0; every term in [0,1] after normalisation; ScenicKit's
SegmentScore over the same fixture agrees within 1e-6 (the gate-parity fixture T-0012 names, made real).
Unblocks T-0029 (rank-order) and P-PROD-01. Depends on T-0024..T-0027 leaving queue/review/.

## Log
- 2026-09-18T03:05:00Z filed by agent/claude-fable-5-1 from the hourly panel's grounded synthesis (.artifacts/panel/last.md). ops/new-task allocated T-9902 again ([[T-0138]]); renamed by hand.
- 2026-09-18T18:00:58Z amended by agent/claude-fable-5-1 from the 11:13 panel: depends_on now carries what the brief said in prose (T-0024..T-0027) plus T-0154, the pure scorer contract split out of this task. Measured at this commit: ls services/etl/etl/*.py | wc -l prints 19 and cat services/etl/etl/*.py | wc -l prints 3138 (the brief's 17 / 2,101 predates PR #68 and PR #69 and is left as written). Terms with no producer under services/etl/etl today: speedFit, sinuosity, pointsOfInterest, furniture, tunnelMeters, metersToNearestMotorway. This task's remainder after T-0154: the region rank-normaliser for the raw-unit terms, those six producers, and the scenic_score 0..10 column.
- 2026-09-18T19:52:17Z SPLIT by agent/claude-fable-5-1 (13:13 panel, grounded). Three disjoint tasks, each claimable now because
  they need only main's `score.py`, `snap.py` and `tagfilter.py`: T-0161 (geometry terms: sinuosity, tunnel
  metres, metres to the nearest motorway), T-0162 (tag-table terms: speed_fit, furniture), T-0163 (the way
  record and the region normaliser, with the ruling on which terms are ranked). `points_of_interest` (Commons
  photo density, 50 km-local rank, network) is T-0164, later. THIS task shrinks to ASSEMBLY: run the
  producers over an extract, normalise, score, write `scenic_score` 0..10 onto the tagged output, and the
  gate tests the plan's `ops/sane` check 4 needs (no NULL scores; motorway/trunk/private/unpaved exactly
  0.0). HAZARD recorded by the grounding pass: `origin/task/T-0029` carries its OWN `services/etl/etl/score.py`,
  unmerged - it collides with T-0154's, which is the reviewed one on main.
- 2026-09-18T20:57:28Z SCOPE CUT AT THE OSMIUM SEAM by agent/claude-fable-5-1 (14:13 panel, DIRECTION lens, grounded). This task is
  now the FIXTURE HALF only: pure-python assembly (the producers' outputs -> way records -> `normalise` ->
  `score.score`) plus the four gate assertions the plan's `ops/sane` check 4 needs - no NULL score; motorway,
  trunk, private and unpaved ways exactly 0.0; every term in [0,1]; ScenicKit parity to 1e-6 - over a COMMITTED
  JSON way-record fixture, run with native Python on the dev box, demonstrated red then green. Grounded facts
  behind the cut: `services/etl/pyproject.toml` declares no dependencies, `score.py` imports only `math` and
  local modules, the Dockerfile installs `osmium-tool` (a subprocess, never a Python import), every fixture is
  JSON, and the score tests already pass natively here. "Write `scenic_score` 0..10 onto the tagged output" is
  REMOVED from this task and is T-0168, which needs docker through WSL. What a hand-written fixture cannot
  surprise its author with - real tag coverage, NULLs from missing DEM samples, the plan's "8/10 top-scored
  ways are roads you'd drive" - moves to T-0168 with it, on purpose and stated.
