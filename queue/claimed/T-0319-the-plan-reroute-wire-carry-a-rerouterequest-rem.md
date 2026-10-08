---
id: T-0319
title: The /plan reroute wire - carry a RerouteRequest (remaining pins + same lambda) without sending more than one 2-dp coordinate (plan token + first remaining pin index); the Worker half of T-0317 R2
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-08T12:53:20Z
lease_expires_at: 2026-10-08T22:53:20Z
worktree: .worktrees/T-0319
branch: task/T-0319
exclusive: []
touches: [services/api/src/, services/api/test/, Sources/ScenicAPIClient/, Tests/ScenicAPIClientTests/]
pins_affected: [P-NAV-01, P-PRIV-05]
reviewer: null
depends_on: [T-0317]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Filed by agent/claude-opus-5 from T-0317 ruling R2. ScenicKit's DriveSession (T-0317) emits a device-side
RerouteRequest {origin, remainingWaypoints, firstRemainingWaypoint, destination, lambda}. /plan cannot carry it:
services/api/src/planRequest.ts BODY_KEYS are origin, destination, budget_minutes, departs_at, vehicle (measured
2026-10-08), and CLAUDE.md forbids more than one coordinate per user action or more than 2 dp, so sending the pins
as coordinates is not an option. MEASURE FIRST (what /plan returns today that could identify a plan - nothing is a
token yet), then rule an encoding - e.g. a plan token the Worker remembers (with the pins and lambda it chose) plus
`firstRemainingWaypoint` and the one 2-dp origin - whitelist it (P-PRIV-05), and make ScenicAPIClient send it.
Acceptance is written by the claimer after that measurement (CLAUDE.md: a predicate over an unmeasured population is
a measurement task first).

## Log
- 2026-10-08 filed by agent/claude-opus-5 (T-0317 R2) through ops/new-task; the allocator answered T-9902 (a stray
  ref outside origin/main holds T-9901), renumbered to T-0318, the next id after origin/main's T-0317.
- 2026-10-08T12:53:20Z claimed by agent/claude-opus-5; lease until 2026-10-08T22:53:20Z
