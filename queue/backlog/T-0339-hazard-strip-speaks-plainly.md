---
id: T-0339
title: The hazard strip speaks plainly - every hazard the preview, trip and loop cards show is human copy from one closed table ("Private road ahead - local access only"), never a raw API key like "road_access: destination"
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/ScenicKit/, Sources/ScenicAPIClient/, Tests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/, ops/mutate/, ops/lib/check-safety-disclaimer-linked-digests.txt, pins/PINS.yaml]
pins_affected: [P-SAFE-02]
reviewer: null
depends_on: [T-0336]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0336 shots (PR #221) and rv2-t0336 recordable 1: plan-preview shows the raw string `road_access: destination` as
user-facing text. MEASURE FIRST: every hazard kind the Worker can send (HazardFlag, warnings in plan/trip/loop bodies),
where each reaches the screen, and what the copy should say (calm, specific, actionable - owner intent "calm
adventure"; the safety meaning must not be softened). Then the acceptance: one closed copy table, every kind mapped,
an unknown kind shows a safe generic line (never the raw key) and is logged as unknown in tests; whole-copy equality;
P-SAFE-02's layers still see each hazard; shots looked at.

## Log
- 2026-10-09T08:22:49Z filed by agent/claude-opus-5 (orchestrator) from rv2-t0336 recordable 1; T-0338 is held by task/T-0337.
