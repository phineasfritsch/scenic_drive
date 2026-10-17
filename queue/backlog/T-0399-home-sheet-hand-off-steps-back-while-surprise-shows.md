---
id: T-0399
title: While the Surprise card shows, the home sheet's own Open in Apple Maps steps back - one filled primary on screen, and the Surprise card gets its own disclaimer line
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, apps/ios/Packages/ScenicApp/Sources/FeatureSurpriseMe/, Tests/, ops/lib/, queue/]
pins_affected: [P-SAFE-03]
reviewer: null
depends_on: [T-0397, T-0398]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0398 (Surprise card) found that the second filled "Open in Apple Maps" in the `-screen surprise` shots (run
39035404874, surprise-light.png / surprise-dark.png) is not the Surprise card's: it is the home sheet's
GatedHandoffButton (FeatureScenicHome) for the selected drive, drawn under the card. FeatureScenicHome was outside
T-0398's touches and inside T-0397's, so T-0398 left it. Library: `.artifacts/mobbin/library/reference-library.md`,
"Surprise card" -> Clutter panel rows 1 and 6, and Recommended layout items 1 and 9.

Scope:
1. While the Surprise card shows, the screen holds exactly one filled primary: the home sheet's hand-off becomes
   tonal, or the sheet steps back (the library's "Surprise replaces the sheet content"). The gated opener stays the
   only path to Apple Maps (P-SAFE-03).
2. The Surprise card carries "Conditions change. Verify locally." directly under its primary (library item 9),
   added through the safety-disclaimer copy's approved sites, not as a new literal.
3. Demonstrate with ios-screenshot surprise light, dark and ax5 shots.

## Log
- 2026-10-17 filed by agent/claude-opus-5 from T-0398 ruling R1/R6.
