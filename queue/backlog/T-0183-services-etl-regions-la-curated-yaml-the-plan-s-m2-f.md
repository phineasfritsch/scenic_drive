---
id: T-0183
title: services/etl/regions/la/curated.yaml - the plan's M2 five seeds, authored for LA and the owner's commute, with the pytest the plan names
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: [curated-la]
touches: [services/etl/regions/la/, services/etl/tests/, services/etl/etl/]
pins_affected: []
reviewer: null
depends_on: [T-0168]
verify: [ops/test, ops/check-pins]
acceptance:
  - "five seeds in services/etl/regions/la/curated.yaml with the plan's fields (id, name, hook <= 90 chars, lat/lon 5dp, join, category, hours_exempt, dwell_min, approach_hint, verified_on, curation_score 0.6-1.0, notes), every coordinate Nominatim-verified and quoted; the plan's pytest: every seed joins exactly one place or is hours-exempt; the approach road within 300 m has GATE=1 and score >= 0.5 (over the LA tagged PBF); verified_on <= 12 months - each RED by name on a deliberately broken seed, then green"
  - "cd services/etl && python -m pytest tests -rs -> count line and zero skips at the final commit"
---
## Brief

From the 19:13 panel (grounded): `services/etl/regions/la/` has no curated.yaml; the plan's M2 row asks for the
curated.yaml schema plus five seeds, and its Curation lifecycle row gives the fields and the pytest. The owner is
in Westwood; the seeds are places an LA driver with 25 spare minutes would actually go (the Surprise Me
candidates of M5), not Bay Area ones. `curated.yaml` is a serial-only file (CLAUDE.md): `exclusive: [curated-la]`.

## Log
- 2026-09-19T02:11:14Z filed by agent/claude-fable-5-1 from the 19:13 panel's grounded synthesis. Not started; behind T-0168 (the approach-road check needs the LA scores).
