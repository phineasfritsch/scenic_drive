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
- 2026-10-17 T-0398's surprise-ax5.png (run 39046317171, the first ax5 Surprise shot) adds scope item 4: with the
  card open at AX5 the HOME's layout squeezes - the drive chips clip vertically ("West-wood loop" and
  "SF Peninsu-la" cut top and bottom), the collapsed sheet's three route tiles overflow their borders ("Fastest",
  "+13 min", "+18 min" drawn across the tile tops, "good road" below them), the sheet's Open in Apple Maps is pushed
  off-screen, and the attribution box covers the map's (i) button. home-ax5-collapsed.png (run 39035404874, no card)
  shows none of it, so the home gives the card its ideal height and compresses its own rows; fix in the home
  (chips and tiles keep their vertical ideal size, or the card scrolls inside a bounded height).
