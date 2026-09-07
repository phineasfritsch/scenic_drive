---
id: T-0030
title: Emit corpus.sqlite: segments + R*Tree, places, curated, meta, schema_version
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/, Sources/PlaceStore/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

The artifact the app actually reads. Tables per the plan: `osm_features` (ODbL layer),
`segments` (own stable ids + geometry + R*Tree), `terms_osm` / `terms_raster` (kept physically separate for the
ODbL Collective-Database posture), `places`, `curated`, `meta(version, schema_version, region, built_at, counts)`.

Stable ids: `segment_id = fnv64(osm_way_id, round(offset_m/100))`, with `--previous corpus.sqlite` carrying ids
forward by 25 m geometric match when a way changed >10% (the saved-drives requirement).

RED: rebuild twice from the same extract -> identical checksum (P-DATA-01 idempotence). Rebuild after a
simulated way split -> >=98% of previous ids still resolve.

## Log
