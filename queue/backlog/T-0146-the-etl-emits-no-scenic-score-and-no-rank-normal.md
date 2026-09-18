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
depends_on: []
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
