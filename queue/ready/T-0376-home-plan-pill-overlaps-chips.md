---
id: T-0376
title: The home's "Plan a drive" pill no longer draws over the drive chips (Saddle Peak, Westwood loop) - seen in home-light-medium on every recent ios-screenshot run
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, apps/ios/ScenicDrive/ScenicDriveApp.swift, ops/lib/check-safety-disclaimer-pinned, ops/lib/check-safety-disclaimer-frozen, queue/]
pins_affected: [P-ATTR-01, P-A11Y-01]
reviewer: null
depends_on: []
verify: [ops/check-pins]
acceptance: []
---
## Brief

Reported by T-0355's author (home-light-medium, run 38022188023), T-0367's author and rv2-t0368 (run 38878685784):
in home-light-medium.png the "Plan a drive" pill sits on top of the "Saddle Peak" and "Westwood loop" drive chips.
T-0355 attributed it to the shell's top-left overlay; none of the PRs that reported it touched that strip.

MEASURE FIRST: which views draw the pill and the chip strip (the shell's overlay in ScenicDriveApp.swift vs
FeatureScenicHome), their alignment/safe-area insets, and every home shot (light, dark, AX5, each detent) where they
collide - quote the shots looked at. RULE the layout (stack them, inset the chips, or move the pill), keeping
attribution visible at every detent (P-ATTR-01) and >= 44 pt targets. Acceptance: the home shots in light, dark and
AX5 show the pill and every chip with no overlap, looked at and quoted; P-SAFE-03 digests and the frozen shell lines
re-approved.

## Log
- 2026-10-16T10:05:00Z filed by agent/claude-opus-5 (orchestrator) from rv2-t0368's recordable (ids checked on main
  and task/T-0318, task/T-0375: highest T-0375).
