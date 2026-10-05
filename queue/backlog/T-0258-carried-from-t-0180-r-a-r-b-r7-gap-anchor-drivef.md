---
id: T-0258
title: Carried from T-0180 (R-a, R-b, R7 gap): anchor DriveFacts' rendered straight-line number to StraightLineDistance.skylineRouteWholeKilometers and the paste's timing line (HandoffFailureCard.clipboardText) - identifier-level source checks or UI tests - and assert home.conditions at the MEDIUM detent at the largest accessibility size
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [apps/ios/ScenicDriveUITests/, ops/lib/, pins/PINS.yaml]
pins_affected: []
reviewer: null
depends_on: [T-0180]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

From T-0180's Log (ruling R9), the three items its first UI test bundle did not take:
- R-a (carried from rv1-pr110): nothing anchors the rendered straight-line number to the pinned computation - DriveFacts interpolates StraightLineDistance.skylineRouteWholeKilometers, and a literal typed in its place passes every gate. Cheap anchor: an identifier-level source check that DriveFacts names that symbol (never a comment); or a UI test reading `home.distance` at the medium detent against the Linux value.
- R-b (carried from rv1-pr110): the timing line riding along in the paste (HandoffFailureCard.clipboardText) is pinned nowhere - no test, check or pin names DriveFacts.timing / home.timing / clipboardText. A UI test needs the failure card on screen, which needs a fault-injection launch argument the app does not have.
- R7 gap: SafetyGateUITests asserts home.conditions at the largest accessibility size at the COLLAPSED detent only; at medium the sheet may outgrow the screen. Measure first (a run's screenshot at -homeDetent medium with -UIPreferredContentSizeCategoryName UICTContentSizeCategoryAccessibilityXXXL), then write the predicate.

## Log
- 2026-10-05T11:46:32Z by agent/claude-opus-5 (filer, from T-0180 R16): ALSO CARRIED - register ops/lib/check-drive-copy in pins/PINS.yaml (rv1-pr121 recordable r1). T-0180 did not, because on the Windows box the check never finished: no output in 40 min in the background, and `timeout 280 bash ops/lib/check-drive-copy` was killed at 280 s with 0.45 s user time (blocked, not computing). Find the block first; a pin that hangs check-pins --source-only is worse than none.
- 2026-10-05T13:49:55Z by agent/claude-opus-5 (filer): renumbered from T-9902 (filed through the ops/new-task T-0128 stray-ref bug); the id was T-9902 in T-0180's Log entries before this date.
