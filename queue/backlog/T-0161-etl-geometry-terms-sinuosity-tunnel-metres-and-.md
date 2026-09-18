---
id: T-0161
title: ETL geometry terms - sinuosity, tunnel metres and metres to the nearest motorway, from way geometry alone
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/etl/sinuosity.py, services/etl/etl/proximity.py, services/etl/tests/test_sinuosity.py, services/etl/tests/test_proximity.py, services/etl/tests/fixtures/]
pins_affected: []
reviewer: null
depends_on: [T-0154]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

One of three disjoint pieces T-0146 was split into by the 2026-09-18 13:13 panel (CODE lens, grounded). The
seam already exists and is code: `services/etl/etl/score.py` takes keyword-only `sinuosity`, `tunnel_meters`
(default 0.0) and `meters_to_nearest_motorway` (default `math.inf`) (score.py:119-122). Nothing under
`services/etl/etl/` produces any of the three. All three need only tags and coordinates - no raster, no
container - so they are built and tested on the Windows box (`cd services/etl && python -m pytest tests -rs`).

**Build, editing NOTHING that exists** (read `snap.py`: `length_m` at :106, `distance_to_line_m` at :58):
1. `sinuosity.py` - RAW sinuosity of a way: path length over the straight-line distance between its
   endpoints, as an unbounded value >= 1.0 (the region normaliser, T-0163, maps it to 0..1; do not normalise
   here). A closed way or coincident endpoints is its own named case, never a division by zero and never a
   silently huge number: decide the rule, say it in the docstring, pin it with a test.
2. `proximity.py` - `tunnel_meters(way)`: metres of the way tagged as tunnel (`tunnel=yes|building_passage|
   ...` - enumerate the OSM values you accept as a named constant and pin the set against literals; `tunnel=no`
   is NOT a tunnel). `meters_to_nearest_motorway(way, motorways)`: the minimum distance from the way's
   geometry to any motorway/motorway_link/trunk/trunk_link geometry, `math.inf` when none is within a stated
   search radius. The plan's thresholds (tunnel > 300 m x0.15; within 150 m of a motorway x0.7, plan:85) live in
   score.py ALREADY - do not restate them here; this task produces metres, not multipliers.
3. Fixtures: small committed geometries with hand-checkable answers (a straight line, a right-angle dog-leg
   whose sinuosity is sqrt(2) to the digit, a way parallel to a motorway at a typed-out offset, a way that
   crosses one). Expected values typed out from arithmetic you show in a comment, NEVER computed by the
   function under test.

**Owner's rulings, so the Log starts from them:** distances are metres on the same spherical model snap.py
uses (import it; do not add a second earth radius); the zero classes themselves still get values (the scorer
zeroes them, this module does not gate); a way with fewer than two coordinates REFUSES by name.

**The author rule (it took PR #89 through review in one round):** rule every place the plan, score.py and
snap.py disagree in your Log BEFORE writing code; re-run and quote the whole acceptance block at your FINAL
commit; close your own verifier's findings before the review is bought. Every new test demonstrated RED by
name (three mutations of each new module nobody else will write), then green. No number in prose that a
command did not print.

## Log
- 2026-09-18T20:20:00Z filed by agent/claude-fable-5-1 from the 13:13 panel's grounded synthesis. Not started.
