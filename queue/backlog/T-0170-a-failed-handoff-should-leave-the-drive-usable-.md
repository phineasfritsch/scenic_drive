---
id: T-0170
title: a failed handoff should leave the drive usable - a copyable list of the roads, not only Try again
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, apps/ios/Packages/ScenicApp/Sources/DesignSystem/]
pins_affected: []
reviewer: null
depends_on: [T-0152]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

DRIVER TWO, 2026-09-18 14:13 panel (grounded): when the Apple Maps handoff fails the home screen offers one
move - "Couldn't open Apple Maps. Try again." - and the code comment beside it admits there is no
copy-the-route affordance. If it fails twice the friend on the TestFlight link has nothing: no road names to
type, no address, no way to get the drive out of the app. Not M1.5-blocking.

**Do, after T-0152 lands:** on failure show the drive in words (the same road list T-0152 puts under the
title) with a Copy action, and keep Try again. DesignSystem tokens only, Dynamic Type, accessibility
identifiers, 44 pt targets; the compiler proof is a green `ios-compile` dispatch on the branch.

## Log
- 2026-09-18T20:57:28Z filed by agent/claude-fable-5-1 from the 14:13 panel's grounded synthesis. Not started.
