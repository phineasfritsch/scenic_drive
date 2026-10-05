---
id: T-0255
title: PlaceStore decodes the segment geometry BLOB into e7 vertices
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/PlaceStore/, Tests/PlaceStoreTests/, ops/mutate/]
pins_affected: []
reviewer: null
depends_on: [T-0175]
verify: [ops/test, ops/check-pins]
acceptance:
  - "Segment exposes its decoded vertices (Int32 e7 lat/lon pairs) equal by exact equality to the ETL's encoder output for every fixture segment; a mutation population under ops/mutate/ with a literal floor"
---
## Brief

Follow-up recorded in T-0175's Log (PR #142, review PASS): geometry is returned as stored bytes today (T-0175 R5) so no PlaceStore file computes a number; decoding is the first numeric code there and ships its own population.

## Log
- 2026-10-05T11:49:04Z filed by agent/claude-opus-5 (orchestrator) from T-0175's stillOpen list.
- 2026-10-05T20:05:56Z PROMOTED to ready/ by agent/claude-opus-5 (orchestrator): T-0254 (PR #152) merged; PlaceStore free.
