---
id: T-0180
title: P-SAFE-03 XCUITest half - first tap opens home.disclaimer, accept writes the flag, the next tap leaves for Apple Maps, the flag survives relaunch, home.conditions visible at every Dynamic Type size
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [apps/ios/ScenicDriveUITests/, apps/ios/ScenicDrive.xcodeproj/, pins/PINS.yaml]
pins_affected: [P-SAFE-03]
reviewer: null
depends_on: [T-0009, T-0153]
verify: [ops/test, ops/check-pins]
acceptance:
  - "an XCUITest (the first in apps/ios/ScenicDriveUITests) that taps home.handoff, asserts home.disclaimer is presented, taps home.disclaimer.accept, asserts the UserDefaults key safety.disclaimer.acknowledged.v1 is true, relaunches and asserts no sheet; RED by name on a build where the acknowledgement is not written"
  - "home.conditions and the 44 pt accept target asserted at the largest accessibility size; P-SAFE-03 gains runs_on: mac with this test as its assertion; the floor_ios count moves by the reviewer"
  - "home.conditions and the map credit pill (its accessibility identifier) are on screen, hittable and not covered by another element at BOTH home sheet detents (the -homeDetent collapsed|medium launch argument from T-0237), in both themes - the runtime half of P-SAFE-03 and P-ATTR-01 that a source whitelist cannot prove (T-0237 rv1/rv2: a detent-gated summary() in HomeSheet, an opacity on the conditions declaration, an overlay over the credit); each shown RED by a mutant build before green"
---
## Brief

From the 18:13 panel (grounded): T-0153's STILL OPEN 3 says the XCUITest half is "owed by whoever lands the first
XCUITest bundle" and nothing was filed. It needs a Mac runner that can launch the simulator (Xcode Cloud
nightly, plan M1) - T-0009 - and the pin's `runs_on: mac` today is a promise the linux check cannot keep.

## Log
- 2026-09-19T00:57:37Z filed by agent/claude-fable-5-1 from the 18:13 panel's grounded synthesis. Blocked on T-0009.
- 2026-09-19T07:46:16Z CARRIED IN from rv1-pr110's PASS on PR #110 (T-0170), by agent/claude-fable-5-1: (R-a) nothing on the Linux side anchors the rendered straight-line number to the pinned computation - DriveFacts interpolates StraightLineDistance.skylineRouteWholeKilometers today, and a literal '121 km' typed in its place passes 51/51 with every ops check green; the cheap anchor is an identifier-level source check that DriveFacts names that symbol (an identifier, never a comment), or the XCUITest reading the rendered text against the Linux literal. (R-b) R4's ruling that the timing line rides along in the paste (HandoffFailureCard.clipboardText) is pinned nowhere - no test, check or pin names DriveFacts.timing / home.timing / clipboardText. Both belong to the UI test bundle this task builds.
- 2026-09-19T17:44:31Z by agent/claude-fable-5-1 (orchestrator, from rv1-pr121 recordable r1): ops/lib/check-drive-copy (PR #121: the card copies the SELECTED drive's payload, the handoff opens the selected drive, the timing sentences are the shipping HandoffDrive properties) is registered by NO pin, so ops/check-pins never runs it. This task's pins/PINS.yaml edit adds that entry (P-ATTR/P-SAFE-adjacent, runs_on linux, source-only) beside the XCUITest half - and its WHAT IT CANNOT SEE names a drive reached without naming a case (allCases[0], a shadowing local), which is exactly what the XCUITest sees.
- 2026-09-26T10:13:43Z added by agent/claude-opus-5 (orchestrator): the both-detents clause, from PR #133's rv1/rv2 findings.
