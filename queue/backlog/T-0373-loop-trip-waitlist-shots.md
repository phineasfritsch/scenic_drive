---
id: T-0373
title: ios-screenshot shoots the loop and trip regionUnsupported failure with "Count this area" and their waitlist card
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [.github/workflows/ios-screenshot.yml, apps/ios/Packages/ScenicApp/Sources/, ops/lib/, queue/]
pins_affected: []
reviewer: null
depends_on: [T-0365]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0365 gave LoopScreen and RoadTripScreen the waitlist offer on regionUnsupported (`loop.failure.waitlist`,
`trip.failure.waitlist`, then the shared WaitlistCard), but no shot shows them: the shot list lives in
.github/workflows/ios-screenshot.yml, outside T-0365's touches (T-0365 R6). Add PlanRehearsalFixtures cases
(e.g. `loopRegion`, `tripRegion`, `loopWaitlist`, `tripWaitlist`: the failed sheet, and the card with an answer -
PlanRehearsal would need a per-tab waitlist answer the sub-screens read) and list them in the workflow's LIST and
plan-sheet case arm (and ops/lib/ios_screenshot_pinned.py if it pins the list). Acceptance: ios-screenshot success
with the new PNGs looked at, light and dark; the button reads "Count this area" and the card names what it sends.
Every apps/ios Swift edit re-approves its P-SAFE-03 digest.

## Log
- 2026-10-16T04:45:00Z filed by agent/claude-opus-5 from T-0365 R6 (ids checked on origin/main and every
  origin/task/* branch: highest T-0371).
- 2026-10-16T05:16:23Z renumbered T-0372 -> T-0373 by agent/claude-opus-5: main filed and claimed its own T-0372 (sane exit 4) after this was filed; this copy was unclaimed.
