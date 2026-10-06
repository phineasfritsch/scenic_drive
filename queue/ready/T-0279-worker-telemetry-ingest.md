---
id: T-0279
title: the Worker serves POST /telemetry - accepts exactly the T-0265 TelemetryEvent wire data points (14 events, coarse payloads), refuses anything else, writes them to Workers Analytics Engine; never a coordinate, never more than an H3-5 cell
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/api/, Tests/Fixtures/t0279/, Tests/TelemetryTests/]
pins_affected: [P-PRIV-05, P-COST-01]
reviewer: null
depends_on: [T-0265]
verify: [ops/test, ops/check-pins]
acceptance:
  - "a shared fixture under Tests/Fixtures/t0279/ holds the Swift encoder's exact JSON for every one of the 15 wire names (written by a Swift test from Sources/Telemetry, compared by bytes); the Worker's validator accepts every fixture row and the ingest writes the identical {indexes, blobs, doubles} to an injected Analytics Engine binding (full equality per row)"
  - "a WHITELIST validator (event name in the closed set, exact key set, blob count/length, each label from its closed enum, the cell matching the H3 res-5 bit layout, doubles finite and in ruled ranges at EVERY bound) refuses every other body with 400 and zero writes - table test through ROUTES['/telemetry']; at most a ruled number of events per request and per device per day (quota kind 'telemetry', reserved before the write); KILL pauses writes; the request-read whitelist extended by equality"
  - "no deploy, no Analytics Engine dataset created (wrangler.jsonc binding declared only); a TS mutation population with a literal floor"
---
## Brief

Plan Telemetry: 'closed enum of 14 events ... -> Workers Analytics Engine; ops/funnel prints plan->preview->drive->answer'.
T-0265 (PR #155) shipped the device encoder; nothing receives it. P-PRIV-05: H3-5 cells only, never a coordinate.

## Log
- 2026-10-06T10:46:25Z filed by agent/claude-opus-5 (orchestrator) from the milestone gap map (M5 telemetry).
