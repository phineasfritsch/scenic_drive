---
id: T-0168
title: ETL tagged-PBF rewrite - osmium writes scenic_score 0..10 and its terms onto ways, in the container, over a real extract
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: [scenic-index]
touches: [services/etl/etl/, services/etl/tests/, ops/etl-extract, services/etl/Dockerfile]
pins_affected: []
reviewer: null
depends_on: [T-0146, T-0169]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

The WSL half of what T-0146 used to be (cut by the 2026-09-18 14:13 panel, grounded). T-0146 proves the
assembly and the check-4 gates over a committed fixture with native Python; THIS task runs it over a real
extract inside the pinned ETL image (docker on this box works only through WSL) and has `osmium` write
`scenic_score=0..10` plus the terms back onto the ways of the tagged PBF that T-0031 imports into GraphHopper.

It deliberately carries what a hand-written fixture cannot surprise its author with: real tag coverage
(per-class surface coverage goes into `meta`, plan M2 row), NULLs from ways with no DEM or land-cover sample,
and the plan's human exit clause - "8/10 top-scored ways are roads you'd drive" - printed as a ranked list
with names and coordinates for the human to read. `ops/sane` check 4's clauses run for real here: no NULL
scores; no motorway/trunk/private/unpaved way with a score above 0.

Rule in the Log before code: the 0..1 -> 0..10 quantisation (round, floor, or keep one decimal - the
GraphHopper encoded value's bit width decides); what happens to a way a producer REFUSED (a named flag, never
a silent 0); idempotence (P-DATA-01: running twice over the same extract is byte-identical); which extract
(the refetched California file from T-0169, clipped to the sfbay bbox).

## Log
- 2026-09-18T20:57:28Z filed by agent/claude-fable-5-1 from the 14:13 panel's grounded synthesis. Not started.
