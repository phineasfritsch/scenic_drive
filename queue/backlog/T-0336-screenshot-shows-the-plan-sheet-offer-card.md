---
id: T-0336
title: ios-screenshot shows the plan sheet's nothing_pretty offer card, light and dark, so the copy and both buttons are seen on a simulator
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [.github/workflows/ios-screenshot.yml, apps/ios/Packages/ScenicApp/Sources/, ops/lib/]
pins_affected: []
reviewer: null
depends_on: [T-0334]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0334 R8 (MEASURED): ios-screenshot.yml's SHOTS are collapsed medium fastest settings paywall surprise drive - none
is the plan sheet, so T-0334's PlanOfferCard (the nothing_pretty line naming the minutes, "Try N extra minutes", "All
back roads: about E min, B extra minutes", "Choose another place") has compiled but never been seen. Add a `-screen`
launch value that opens the plan sheet in `.offered` with a fixed PlanOffer (no request, no planner), and a SHOTS entry
for it; re-pin ops/lib/ios_screenshot_pinned.py. MEASURE first: how `-screen` values are routed today and what the
pinned workflow check holds. Shots looked at, light and dark, at the medium and large detents.

## Log
- 2026-10-09T04:50:29Z filed by agent/claude-opus-5 (T-0334 owner) from T-0334 R8.
