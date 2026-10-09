---
id: T-0346
title: The plan sheet's bottom bar never hides a card's own actions - on the road-trip card "Change the trip" sits under the "Plan a drive / Just drive a loop" bar; every card's last control stays reachable above the bar at every Dynamic Type size
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-09T15:45:25Z
lease_expires_at: 2026-10-10T01:45:25Z
worktree: .worktrees/T-0346
branch: task/T-0346
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/, .github/workflows/ios-screenshot.yml, ops/lib/, ops/lib/check-safety-disclaimer-linked-digests.txt]
pins_affected: [P-ATTR-01, P-A11Y-01]
reviewer: null
depends_on: [T-0341]
verify: [ops/check-pins]
acceptance: []
---
## Brief

T-0341 owner stillOpen 2 (PR #227): in the plan-trip shot the bottom toolbar ("Plan a drive / Just drive a loop")
covers the trip card's "Change the trip" button; the added closures row pushed content down. T-0336's shots also
showed the plan sheet's two bottom-toolbar buttons change meaning per tab (an open design question for the owner).
MEASURE FIRST: every card in the plan sheet (preview, nothingPretty, offered, loop, trip, saved), the toolbar's
height at default and AX5 Dynamic Type, and whether each card's last control is above it (screenshots at both sizes);
RULE the fix (safe-area inset / content margin, not removing the bar), then the acceptance: shots at default and AX5
looked at, no control under the bar, attribution unchanged (P-ATTR-01). Do not redesign the toolbar - that is the
owner's design pass.

## Log
- 2026-10-09T15:24:28Z filed by agent/claude-opus-5 (orchestrator) from T-0341 stillOpen 2; T-0345 is held by task/T-0344.
- 2026-10-09T15:45:25Z claimed by agent/claude-opus-5; lease until 2026-10-10T01:45:25Z
