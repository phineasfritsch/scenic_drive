---
id: T-0030
title: Emit corpus.sqlite: segments + R*Tree, places, curated, meta, schema_version
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-18T21:54:27Z
lease_expires_at: 2026-09-19T05:54:27Z
worktree: .worktrees/T-0030
branch: task/T-0030
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
- 2026-09-07T23:19:29Z claimed by agent/unknown; lease until 2026-09-08T01:19:29Z
- 2026-09-18T21:54:27Z RE-LEASED by agent/claude-fable-5-1 for agent/claude-opus-5 (15:13 panel, STRATEGY F2, grounded): the lease
  expired 2026-09-08T01:19:29Z with a pushed WIP at a2f1e2b (662 lines: contentdigest.py, geom.py, schema.py,
  segid.py, segmenter.py - no tests, no PR) and the sweep keeps it because it names a branch (queue.py:552-590),
  so no dispatcher would ever surface this M2 exit clause (plan:283 "corpus <60 MB"). Lease until 2026-09-19T05:54:27Z.
  FIRST SLICE for the adopter: merge origin/main into task/T-0030 (506 commits behind), read the WIP against
  the plan's corpus lifecycle and today's `services/etl/etl/` (score.py, way_record.py on #93), and land the
  parts that do not need scores: the schema with `meta(schema_version, region, built_at, counts)`, stable
  `segment_id = fnv64(osm_way_id, round(offset_m/100))`, the segmenter over a committed synthetic extract, and
  the two REDs in the Brief (byte-identical rebuild; >= 98% of previous ids resolve after a simulated way
  split). `terms_osm`/`terms_raster` are declared and empty until T-0146 assembles the terms - say so.
