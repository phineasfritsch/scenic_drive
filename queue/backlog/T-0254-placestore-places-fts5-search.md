---
id: T-0254
title: PlaceStore places FTS5 table and search(query:limit:) for the plan sheet
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: [scenic-index]
touches: [services/etl/etl/, Sources/PlaceStore/, Tests/PlaceStoreTests/, services/api/src/index.ts, ops/lib/check-schema-version.py]
pins_affected: [P-PROD-05]
reviewer: null
depends_on: [T-0175]
verify: [ops/test, ops/check-pins]
acceptance:
  - "an FTS5 places table in the corpus DDL with SCHEMA_VERSION bumped in schema.py, index.ts and PlaceStore.schemaVersion together (check-schema-version green); PlaceStore.search(query:limit:) returns places by exact equality to a fixture built by the shipping etl.corpus; RED first by name"
---
## Brief

Follow-up recorded in T-0175's Log (PR #142, review PASS): the plan sheet needs typed-destination search from the corpus first (plan: 'corpus FTS5 + Photon'); the DDL has no FTS5 table and places has zero rows until the POI join fills it, so the fixture seeds places itself.

## Log
- 2026-10-05T11:49:04Z filed by agent/claude-opus-5 (orchestrator) from T-0175's stillOpen list.
