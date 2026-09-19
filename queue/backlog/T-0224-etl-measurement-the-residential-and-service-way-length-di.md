---
id: T-0224
title: etl - MEASUREMENT: the residential and service way-length distribution over the LA clip per highway class, and the longest residential/service run on T-0213's window routes at lambda 0 and 8 - numbers only; the no-rat-run threshold for T-0209/T-0221 is written after
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/tests/, services/routing/tests/]
pins_affected: []
reviewer: null
depends_on: [T-0213]
verify: [ops/test, ops/check-pins]
acceptance:
  - "over the MAIN checkout's services/etl/work/la/la-filtered.osm.pbf (560,208 filtered ways; T-0112's osmium-export shape): per highway class the way-length distribution (count, median, p90, max, the share over 800 m) quoted in the Log; residential and service first"
  - "over T-0213's window graph (services/routing/work/t0213/graph-la-window, image scenic-routing:t0213, its pytest harness): for the routed pair at lambda 0 and 8, the longest residential/service RUN (consecutive edges of one class, in m, way ids) quoted; no threshold asserted - the Log ends with the numbers T-0209's ruling will read"
  - "nothing under services/etl/etl/ or services/routing/ changes; a measurement script, if committed, lives under tests/ with the command that produced each number; queue-check bare"
---
## Brief

From the 11:13 panel (STRATEGY, fable-grounded): T-0209 clause 3 asserted 'no residential or service run over 800 m'
over a population nobody had looked at (the only 800 m in the tree was its own copy into T-0221); T-0112:72-73
measured the top-200 LA ways' median length at 0.60 km. Measure first, rule after - the plan's rat-run property
('no run >800 m of residential/living_street') is a Bay Area number until LA says otherwise.

## Log
- 2026-09-19T20:26:45Z filed by agent/claude-fable-5-1 (11:13 panel, fable-grounded on T-0112:72-73, T-0209 Log 15:26:14Z, CLAUDE.md 74615e0). Not started; Log-only, no lock; startable now.
