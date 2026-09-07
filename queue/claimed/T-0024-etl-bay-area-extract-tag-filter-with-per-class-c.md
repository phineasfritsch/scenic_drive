---
id: T-0024
title: ETL: Bay Area extract + tag filter, with per-class counts and bounds
state: claimed
owner: agent/claude-opus-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T16:07:44Z
lease_expires_at: 2026-09-07T20:07:44Z
worktree: ../wt/T-0024
branch: task/T-0024
exclusive: [scenic-index]
touches: [services/etl/, ops/sane, ops/etl-extract]
pins_affected: []
reviewer: agent/reviewer-23
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Geofabrik `california-latest.osm.pbf` -> `osmium extract` to the 9-county Bay Area bbox ->
`osmium tags-filter` to drivable ways + the POI allowlist. Prints a COUNT PER FEATURE CLASS and writes them to
`meta`, so `ops/sane` can assert bounds later (viewpoints >= 400 etc, per the plan's data gate).

RED: a filter that drops motorways entirely -> the drivable-way count falls outside bounds and sane exits 4.

## Log
- 2026-09-07T16:07:44Z claimed by agent/claude-opus-5; lease until 2026-09-07T20:07:44Z
