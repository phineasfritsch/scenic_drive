---
id: T-0378
title: The home at the medium detent crashes at AX5 (accessibility XXXL) - find the cause, fix it, and add home-ax5-medium back to the ax5 screenshot pass
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, apps/ios/Packages/ScenicApp/Sources/MapAdapter/, .github/workflows/ios-screenshot.yml, ops/lib/ios_screenshot_pinned.py, ops/lib/check-safety-disclaimer-pinned, ops/lib/check-safety-disclaimer-frozen, queue/]
pins_affected: [P-ATTR-01, P-A11Y-01, P-SAFE-03]
reviewer: null
depends_on: [T-0376]
verify: [ops/check-pins]
acceptance: []
---
## Brief

Found by T-0376's author. `xcrun simctl launch ... -homeDetent medium -menuRow default -screen home` with
`-UIPreferredContentSizeCategoryName UICTContentSizeCategoryAccessibilityXXXL` (the ios-screenshot ax5 pass) dies
within 15 s: "ios-screenshot: ScenicDrive (pid ...) is not running 15s after the ax5 medium launch - it crashed".
Measured three times, the same way each time: run 38882932440 attempt 1 and attempt 2 on task/T-0376 c477e258
(the pill stacked above the chips), and a control run 38887739175 on fd6d5452, which is task/T-0376 with main's
shell layout restored (the pill as a top-leading overlay). So the crash is not T-0376's. At AX5 the collapsed home
launches and is captured (home-ax5-collapsed.png written in all three runs); light and dark medium do not crash.
T-0376 left `medium` out of the ax5 LIST so that the pass can stay green. This task adds it back.

MEASURE FIRST: get the crash report (for example a step that copies `~/Library/Logs/DiagnosticReports/ScenicDrive*`
from the runner, or `log show` for the simulator, uploaded on failure) and quote its top frames in the Log before
ruling. Candidates nobody has checked yet: the medium sheet is taller than the screen at AX5 (the road list, facts
and caption all use `fixedSize` vertically) inside ScenicHomeScreen's VStack. That pushes the chip band and the
credit band past the window edges, and the measured `chipBandBottom`/`creditBandTop` reach MapView and
MapRouteCoordinator's fit and ornament margins. RULE the fix, which may be a scrolling medium sheet. Keep the credit
visible at every detent (P-ATTR-01) and the conditions line visible at both detents (P-SAFE-03).
Acceptance: `medium` back in the ax5 LIST (workflow + ios_screenshot_pinned.py, with a prove-red row), ios-screenshot
success, and home-ax5-medium looked at and quoted: credit, conditions line and button visible, no overlap.

## Log
- 2026-10-16T10:58:18Z filed by agent/claude-opus-5 (T-0376 owner). Ids checked on main and on all 271 remote task/*
  branches: the highest was T-0377.
- 2026-10-16T11:26:00Z scope widened by agent/claude-opus-5 (T-0376 owner). home-ax5-collapsed.png (run 38890737661, af793caf)
  shows the whole home overflowing at AX5: the chip band runs up under the status bar with labels wrapping a few
  letters per line, the credit takes six lines, and the collapsed sheet's title is drawn over its menu chips. T-0376
  R8 holds the shell's "Plan a drive" pill on screen with a fixed home frame. The home's own overflow is this task's.
