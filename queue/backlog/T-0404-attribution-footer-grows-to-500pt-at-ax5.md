---
id: T-0404
title: The attribution footer grows to about 500pt and 6 lines at AX5, covering the map, the route and the drive controls - make it one caption line at default sizes and at most a 2-line strip at AX sizes, never a box over content
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/DesignSystem/, ops/lib/, .github/workflows/ios-screenshot.yml, pins/PINS.yaml, queue/]
pins_affected: [P-ATTR-01, P-A11Y-01]
reviewer: null
depends_on: []
verify: [ops/check-pins]
acceptance: []
---
## Brief

Found by two authors on 2026-10-17 in ios-screenshot runs:
- T-0396 (PR #294): at AX5 the plan preview's AttributionFooter takes about 500pt, which pushes Start and the
  disclaimer line below the fold.
- T-0397 (PR #295): on the drive screen at AX5 the credit pill grows to 6 lines, covers the upper map, the route
  line and MapLibre's (i) button, and hyphenates "OpenStreet-Map".

The reference library (`C:/Users/phineasf/Documents/GitHub/scenic_drive/.artifacts/mobbin/library/reference-library.md`,
"Biggest changes" 4 and the "Legal / attribution" section) says: one caption
'© OpenStreetMap contributors · Protomaps' pinned bottom-left on the sheet edge; one line at default size; a
2-line strip at AX sizes; never boxed over the route.

Scope: AttributionFooter (DesignSystem) only; call sites stay as they are.
1. Default sizes: one line, .caption2, no box or pill.
2. AX sizes: it wraps to at most 2 lines with no hyphenation inside a word. "OpenStreetMap" must never break
   mid-word. Its height is bounded so it can never cover more than the strip it sits in.
3. P-ATTR-01 still holds: visible on every map screen, every detent, both themes and AX5, and not
   accessibilityHidden. The full credit stays available to VoiceOver even if the visible text is shortened.
4. The visible string comes from the product invariant. If the code shows a different string today (for example
   naming MapLibre or Natural Earth), rule it in the Log against the tiles actually drawn: the demo fallback in CI
   and Protomaps on a device with la.pmtiles. Do not drop a credit that the drawn tiles require.

Demonstration: dispatch ios-compile and ios-screenshot; quote the run ids; look at home, plan-preview and drive at
AX5 and at default size in light and dark, and state the footer's line count and what it covers in each. Any new
or changed guard is shown red, then green.

## Log
- 2026-10-17 filed by agent/claude-opus-5 from the T-0396 and T-0397 authors' still-open notes.
