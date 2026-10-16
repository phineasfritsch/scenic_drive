---
id: T-0371
title: surprise_not_this has no wire reason for the card's fourth button, Wrong time - it sends nothing today
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/Telemetry/, Tests/TelemetryTests/, services/api/, apps/ios/Packages/ScenicApp/Sources/PlanAdapter/, ops/lib/]
pins_affected: [P-PRIV-05]
reviewer: null
depends_on: [T-0361]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0361 (M6/R5): SurpriseFeedback.Reason has four cases and the card four buttons; Telemetry's SurpriseNotThisReason
has three (too_far, been_there, not_my_thing). PlanAdapter's LiveMoments sends nothing for `.wrongTime`. Rule whether
the closed list gains `wrong_time` (Telemetry enum + the Worker's accepted labels + encoding table rows) or the button
stays unreported, and record it.

## Log
- 2026-10-16T02:32:24Z filed by agent/claude-opus-5 (T-0361 owner) from T-0361 R5.
