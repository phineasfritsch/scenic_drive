---
id: T-0384
title: The shell's "Plan a drive" pill has no Dynamic Type cap - at AX5 it draws at full accessibility size above the capped home
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [apps/ios/ScenicDrive/ScenicDriveApp.swift, apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, ops/lib/check-safety-disclaimer-pinned, ops/lib/check-safety-disclaimer-frozen, queue/]
pins_affected: [P-SAFE-03, P-ATTR-01]
reviewer: null
depends_on: [T-0378, T-0376]
verify: [ops/check-pins]
acceptance: []
---
## Brief

T-0378 (PR #274) fixed the AX5 medium crash by capping the home's chrome and sheet at DynamicTypeSize.xxxLarge
(the disclaimer keeps the user's own size). Its author recorded the gap left behind: the shell's "Plan a drive"
pill (ScenicDriveApp.swift, the safeAreaInset T-0376 added) is outside that cap and still draws at AX5 size.

MEASURE: the AX5 shots on main (home-ax5-collapsed, home-ax5-medium) - how tall the pill is and what it pushes.
RULE whether the pill shares the home's cap (one binding - the same cap value, not a second literal) or gets
its own accessibility layout; the pill must stay a >= 44 pt target and readable. Re-approve the shell's frozen
lines and pinned digest in the same commit. Acceptance: ios-screenshot success; home-ax5-collapsed and
home-ax5-medium looked at and quoted (pill, chips, credit, conditions line, button visible, no overlap); light/dark
home unchanged.

## Log
- 2026-10-17 filed by agent/claude-opus-5 from T-0378 stillOpen (the shell pill has no Dynamic Type cap).
