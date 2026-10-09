---
id: T-0348
title: A rerouted drive keeps learning - the Worker's reroute answer carries details=time runs, RerouteReply carries them, and the drive's CorridorClock moves onto the new line instead of finishing (T-0343 R8 follow-up)
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/ScenicKit/, Sources/ScenicAPIClient/, Tests/, services/api/src/, services/api/test/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-SAFE-07, P-PRIV-05]
reviewer: null
depends_on: [T-0343, T-0349]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE first: what the Worker's /plan reroute answer (plan_token continuation) sends today, whether its router call asks details=time, and what RerouteReply and ScenicAPIClient's PlanRerouter decode; quote them"
  - "RULE how the clock continues after a reroute (a new CorridorClock over the reroute's line and runs from the first on-line fix; the edge in progress at the reroute teaches nothing) before code"
  - "Tests RED first by name through the shipped CorridorLearner.observe and DriveController.rerouteArrived; P-SAFE-07 binds them; the P-PRIV-05 whitelist re-approved for every new site"
---
## Brief

Filed by T-0343 (R8). Since T-0325 R3 a CorridorClock finishes when the session's line is no longer the planned
route's, because RerouteReply carries no time runs (Sources/ScenicKit/Drive/RerouteReply.swift, measured
2026-10-09) - so every edge after a reroute teaches nothing. T-0343 gave the drive one feed, ScenicKit's
CorridorLearner.observe(coordinate:speedMetersPerSecond:at:on:clock:) (the app calls it from T-0349); this task
carries the runs on the reroute answer and gives the drive a new clock over the new line.

## Log
- 2026-10-09T18:15:30Z filed by agent/claude-opus-5 (T-0343 owner) from T-0343 R8.
