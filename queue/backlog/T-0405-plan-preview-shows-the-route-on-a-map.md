---
id: T-0405
title: The plan preview shows the chosen route on a map above the sheet (reference library, Biggest changes 1) instead of a full-height sheet with an empty lower half
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/FeaturePlanSheet/, apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, Sources/ScenicKit/, Tests/, ops/lib/, ops/mutate/, .github/workflows/ios-screenshot.yml, pins/PINS.yaml, queue/]
pins_affected: [P-ATTR-01, P-SAFE-03, P-SAFE-07, P-A11Y-01]
reviewer: null
depends_on: [T-0396]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

After T-0396 (PR #294, merged 21559484) the preview sheet is tidy, but it fills the screen and its lower half is
empty. Today's shot is `.artifacts/shots-39050070882/ios-screenshots/plan-preview-light.png`. The screen where the
driver decides shows no route at all. The reference library is
`C:/Users/phineasf/Documents/GitHub/scenic_drive/.artifacts/mobbin/library/reference-library.md`. Its "Biggest
changes" 1 says to put the map back on every route screen and plan in a sheet over it. Its "Plan preview" section,
Recommended layout item 1, puts the map on the top ~45% with the chosen route bold. The references are Google Maps
#205, Apple Maps #056, AllTrails #102 and Waze #088. The screen PNGs are under `.artifacts/mobbin/screens/`.

Scope:
1. While the preview state is up, the chosen route is drawn on a map visible above the sheet. Pick whichever of
   these the code supports better and rule it in the Log: a medium detent over the home map, with the route drawn
   and framed; or a map in the preview card itself through MapAdapter's existing map view.
2. The map is fitted to the route's bounds with padding, so the whole route is visible above the sheet.
3. Attribution stays on the map surface at every detent (P-ATTR-01). The disclaimer line stays directly under Start
   (P-SAFE-03), and the estimate tag stays on the ETA (P-SAFE-07).
4. AX5: the sheet scrolls, and Start plus the disclaimer stay reachable. The map may shrink, but it must not cover
   the sheet's text.

Out of scope: alternative routes with time callouts, the "Most scenic" badge, the elevation chart and road cards.
T-0404 owns AttributionFooter's own size; do not edit DesignSystem.

Demonstration: dispatch ios-compile and ios-screenshot, and quote the run ids. Look at plan-preview light, dark and
ax5, and state item by item what each shot shows: the route visible, the map framed, attribution, Start and the
disclaimer. Any new or changed guard is shown red, then green.

## Log
- 2026-10-17 filed by agent/claude-opus-5 after T-0396 merged (empty lower half seen in run 39050070882).
