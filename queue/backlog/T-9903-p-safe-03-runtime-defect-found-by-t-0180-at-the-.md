---
id: T-9903
title: P-SAFE-03 runtime defect found by T-0180: at the largest accessibility size the collapsed home sheet outgrows the screen - home.conditions measured at y 799.7-904.3 in an 874 pt window (run 37292916916), so the persistent line and the handoff are below the bottom edge and the disclaimer's accept cannot be reached; fix the layout and drop the strict XCTExpectFailure in SafetyGateUITests
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, apps/ios/ScenicDriveUITests/, ops/lib/]
pins_affected: []
reviewer: null
depends_on: [T-0180]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

(what, why, and the exact demonstration that proves it — including the red run)

## Log
