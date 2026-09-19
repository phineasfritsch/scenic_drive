---
id: T-0008
title: ops/test-routing: GraphHopper container + Bay Area graph from R2, 20 goldens
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/test-routing, Tests/Fixtures/]
pins_affected: []
reviewer: null
depends_on: [T-0002, T-0209]
verify: [ops/test, ops/check-pins, ops/queue-check]
acceptance:
  - "bash ops/test-routing -> 20 goldens pass against a real GraphHopper in Docker"
  - "RED: a golden edited to expect a motorway-free middle when the fixture route uses 280 -> fails"
---
## Brief

Depends on the M2 graph build. Fixture graph-cache is fetched from R2 by manifest sha256, never committed.

## Log
- 2026-09-19T10:46:00Z RE-RULED by agent/claude-fable-5-1 (03:13 panel, grounded): the Bay Area graph is the CI golden set and comes SECOND; T-0031's Log rules 'the FIRST served graph is LA' (T-0209). depends_on += T-0209.
