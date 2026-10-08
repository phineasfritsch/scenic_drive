---
id: T-0328
title: The app reroutes through the plan token - it keeps /plan's plan_token with the preview, and when DriveSession asks for a reroute online NavAdapter sends PlanClient.reroute (one 2-dp origin + token + first remaining pin), lands the answer through DriveController's ticket, and redraws the drive line
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/ScenicKit/, Sources/ScenicAPIClient/, Tests/, apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/, ops/lib/, ops/mutate/, ops/lib/check-safety-disclaimer-linked-digests.txt, pins/PINS.yaml]
pins_affected: [P-NAV-01, P-PRIV-05, P-ATTR-01]
reviewer: null
depends_on: [T-0319, T-0321, T-0324]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST in a dated Log entry: where plan_token lives on the device after a plan (PlanPreview / PlanResponse, never persisted past the drive, never logged), how NavAdapter's RerouteUnavailable is replaced by a sender built on PlanClient.reroute, how the reroute answer becomes a new DriveLine + pins for DriveController.rerouteArrived, and how DriveScreen draws the rerouted line (rv1-t0324 recordable 4: the screen always draws the preview's line); what happens with a null token (PLANS unbound until the owner binds it): the Worker answers a fresh plan - rule whether the app uses it or rejoins"
  - "The mapping RerouteRequest -> PlanClient.reroute request and reroute answer -> rerouteArrived inputs is pure Linux-tested code with full-equality tables (token present / null, first pin 0 / last / past last, offline edge mid-flight -> the late answer dropped by ticket); no request while offline; P-NAV-01 binds the new tests by name"
  - "ios-compile + ios-screenshot pass; the drive map shows the rerouted line (a DEBUG rehearsal row if ruled feasible); attribution unchanged (P-ATTR-01 green); digests re-approved; population entries MISSED before and CAUGHT by name after"
---
## Brief

T-0319 owner stillOpen 2 (PR #209): the Worker remembers pins + lambda under plan_token and /plan accepts
`reroute: {token, first_pin}`, and ScenicAPIClient has PlanClient.reroute - but the app neither keeps the token nor
calls it; NavAdapter's sender is RerouteUnavailable (T-0321 R3), so every online off-route goes to rejoin mode.
rv1-t0324 recordable 4: DriveScreen always draws the preview's planned line.

## Log
- 2026-10-08T17:21:59Z filed by agent/claude-opus-5 (orchestrator) from T-0319 stillOpen 2 and rv1-t0324 recordable 4.
