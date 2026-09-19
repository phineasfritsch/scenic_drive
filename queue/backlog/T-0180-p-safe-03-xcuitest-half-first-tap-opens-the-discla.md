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
---
## Brief

From the 18:13 panel (grounded): T-0153's STILL OPEN 3 says the XCUITest half is "owed by whoever lands the first
XCUITest bundle" and nothing was filed. It needs a Mac runner that can launch the simulator (Xcode Cloud
nightly, plan M1) - T-0009 - and the pin's `runs_on: mac` today is a promise the linux check cannot keep.

## Log
- 2026-09-19T00:57:37Z filed by agent/claude-fable-5-1 from the 18:13 panel's grounded synthesis. Blocked on T-0009.
