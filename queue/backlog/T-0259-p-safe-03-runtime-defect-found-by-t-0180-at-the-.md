---
id: T-0259
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

MEASURED (T-0180 run 37292916916, AX XXXL, -homeDetent collapsed, iPhone 17 class 402x874 pt): home.conditions frame (16.0, 799.67, 369.67, 104.67) - its bottom at 904.3 is 30 pt below the window; the handoff below it is off screen, so the disclaimer (and its 44 pt accept) cannot be opened at that size. SafetyGateUITests.testConditionsAndAcceptTargetAtLargestAccessibilitySize holds this as a strict XCTExpectFailure naming T-0259; the fix removes it.

## Log
- 2026-10-05T13:49:55Z by agent/claude-opus-5 (filer): renumbered from T-9903 (filed through the ops/new-task T-0128 stray-ref bug); the id was T-9903 in T-0180's Log entries before this date.
