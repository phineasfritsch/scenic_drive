---
id: T-0404
title: The attribution footer grows to about 500pt and 6 lines at AX5, covering the map, the route and the drive controls - make it one caption line at default sizes and at most a 2-line strip at AX sizes, never a box over content
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-17T19:02:24Z
lease_expires_at: 2026-10-18T19:02:24Z
worktree: .worktrees/T-0404
branch: task/T-0404
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

## Acceptance

A1. `wc -l apps/ios/Packages/ScenicApp/Sources/DesignSystem/AttributionFooter.swift` is at most 300.
A2. In AttributionFooter.swift: `.font(.caption2)`, no `RoundedRectangle`/`.background(`, every visible `Text` carries
    `.lineLimit(1)`, `.dynamicTypeSize(...DynamicTypeSize.accessibility2)`, `.accessibilityLabel(Text(text))`,
    `.accessibilityIdentifier("attribution.footer")` and `.accessibilityHidden(false)` (read in the diff).
A3. `bash ops/lib/check-map-attribution` passes; `bash ops/lib/check-map-attribution --prove-red` behaves as on
    main (rows 1-3 refused by name, row 4's dead anchor is pre-existing and filed as T-0413; see the 19:35 Log).
A4. Bare gates pass: `bash ops/lib/check-safety-disclaimer`, `python ops/lib/check-mutate-population.py`,
    `python ops/lib/check-mutate-only.py`, `python ops/lib/check-pins-yaml.py`, `bash ops/lib/check-exec-bits`,
    `bash ops/queue-check`.
A5. ios-compile and ios-screenshot succeed on task/T-0404 (run ids quoted). In home, plan-preview and drive, light,
    dark and AX5: the footer is one line at default size, at most two lines at AX5, no word is broken, no box, and
    it does not cover the route line, the (i) button, Start or the disclaimer line. Observed line count and what
    it overlaps are recorded per shot.

## Log
- 2026-10-17 filed by agent/claude-opus-5 from the T-0396 and T-0397 authors' still-open notes.
- 2026-10-17T19:02:24Z claimed by agent/claude-opus-5; lease until 2026-10-18T19:02:24Z
- 2026-10-17T19:06:49Z rulings (author rule, before code). Looked at run 39050093003 (task/T-0397, newest successful
  ios-screenshot; main has no ios-screenshot run): drive-light shows a boxed 2-line pill at default size,
  drive-ax5 a 6-line box from the status bar to the sheet over the route and the (i), "OpenStreet-Map"
  hyphenated; plan-preview-ax5 a 4-line box about 500pt tall in the sheet over the conditions text.
  - R1 THE STRING. The footer keeps taking `text` from its callers; no call site changes and nothing in the footer
    names a party. The drawn tiles decide it: in CI (demo fallback, no la.pmtiles) the screen draws MapLibre demo
    tiles and an OpenStreetMap-derived route line, so the composed credit is `© MapLibre · Natural Earth · Route
    data © OpenStreetMap contributors` and BOTH halves are required; on a device with la.pmtiles the basemap half
    is `© OpenStreetMap contributors · Protomaps` (MapStyle.protomapsAttribution, the product invariant). Brief 4's
    "different string" is therefore correct for the CI tiles and is not changed. The footer renders `text`
    verbatim and only chooses where lines break, at the " · " separator; no credit is dropped or shortened.
  - R2 VOICEOVER reads ONE element whose label is `text` verbatim (`.accessibilityElement(children: .ignore)` +
    `.accessibilityLabel(Text(text))`), e.g. "© MapLibre · Natural Earth · Route data © OpenStreetMap
    contributors", whatever the visible split or scale; identifier `attribution.footer`; `accessibilityHidden(false)`
    stays (check-map-attribution limb (e)).
  - R3 SIZES. "Default sizes" = every non-accessibility Dynamic Type size: one line, `.caption2`, `.lineLimit(1)`,
    `.minimumScaleFactor(0.5)` shrinks instead of wrapping (the 68-character CI credit at xxxLarge needs about
    0.65). Accessibility sizes: a two-line strip split at the separator into the most even halves (one line
    for a single party), each line `.lineLimit(1)` + the same scale factor. (Amended 20:02: the first cut tried
    one line first with ViewThatFits; see that entry.) The
    footer clamps Dynamic Type at `.accessibility2` so the strip's height is bounded (two caption2 lines at about
    24pt): at AX5 caption2 is about 40pt and the credit cannot fit two 378pt lines without breaking inside a word
    or covering the map, which is the defect. The full credit stays in the VoiceOver label (R2).
  - R4 NO HYPHENATION: every visible line is `.lineLimit(1)`, so no line break can fall inside a word at all; the
    parties keep CreditLine's no-break spaces.
  - R5 NO BOX: the rounded-rectangle ground goes. Legibility over tiles comes from a tight `surface`-coloured halo
    (shadow, radius 1) on the glyphs, which is not a box and covers nothing beyond the letters.
  - R6 PLACEMENT stays bottom-right (call sites stay; ScenicHomeScreen reserves the lower-right for attribution).
    The 104pt left spacer protected MapLibre's logo in the lower-left, which MapView.swift has since moved to
    `logoViewPosition = .topLeft`; it drops to 12pt so the strip can use the full width. The library's bottom-left
    placement is a call-site and MapAdapter change outside this Brief and is not done here.
  - R7 GUARDS. No new guard: line count and overlap are render properties that no source check on this box can
    prove (the screenshots are the proof, A5), and every byte of AttributionFooter.swift is already sha256-pinned
    by check-safety-disclaimer-pinned, so any later edit needs re-approval. No guard changes, so nothing to show
    red-then-green beyond the pinned digest refusing the edit before re-approval (quoted below).
- 2026-10-17T19:35:31Z code at c25f9871. AttributionFooter.swift `wc -l` 99. RED before re-approval,
  `bash ops/lib/check-safety-disclaimer` exit=1: "P-SAFE-03: the pinned render surface changed:
  AttributionFooter.swift content changed (sha256 b0ff92f2..., approved 8f07bec7...)". First check-map-attribution
  run exit=1 on limb (g): "unapproved: .../AttributionFooter.swift: static func strip(_ credit: String) ..." (three
  lines naming the word `credit`); ruled: the helper's parameter is renamed `caption`, the (g) whitelist is NOT
  widened. Then "P-ATTR-01: the pinned render surface changed: AttributionFooter.swift content changed (sha256
  9058c06d..., approved b0ff92f2...)", re-approved in check-safety-disclaimer-pinned (both rows, 2 occurrences).
  GREEN: check-map-attribution exit=0; check-safety-disclaimer exit=0 ("37 feature file(s), shell, footer pinned
  (-pinned); ... LAST all 115 app .swift, then 336 root + pbxproj file(s) (-linked)").
  `--prove-red` exit=1: rows 1-3 refused by name, then "THE MUTATION CHANGED NOTHING: a feature file names a
  protomaps case" - the SAME on the main checkout at 34871225, so it is pre-existing: row 4's sed anchor
  `return BasemapResolver.losAngeles(appearance: appearance)` no longer exists in DriveBasemap.swift. Ruled out of
  scope (no row this task touches); filed as T-0413. A3's prove-red half reads "as on main" for this task.
  Dispatched ios-compile 39062706820 and ios-screenshot 39062709376 on c25f9871.
- 2026-10-17T20:02:27Z ios-compile 39062706820 success, ios-screenshot 39062709376 success (c25f9871). Main's
  workflow has no drive-ax5 shot (that capture lives on T-0397's branch), so drive is judged at light/dark and AX
  behaviour on home-ax5 and plan-preview-ax5. LOOKED: drive-light - one line "© MapLibre · Natural Earth · Route
  data © OpenStreetMap contributors" at the map's bottom edge, full width, no box, clear of the route line (ends
  about 300pt higher), the (i) and End drive. plan-preview-ax5 - one line "Route data © OpenStreetMap
  contributors" (single party) at about 19pt, under the estimate line, over nothing (was a 4-line ~500pt box).
  home-ax5-medium - ONE line, but at about 12pt: the ViewThatFits accepted the one-line child at half scale,
  so the strip never showed and an AX5 reader got smaller text than at default. Ruled a defect of mine (R3 said
  "else a two-line strip"); fixed by deciding the split instead of measuring it: at accessibility sizes the
  footer is always the strip (one line for a single party). Digest re-approved (9058c06d -> 3373eb72),
  `wc -l` 97, check-map-attribution exit=0. Re-dispatching.
- 2026-10-17T20:28:52Z LOOKED at ios-screenshot 39065139596 (compile 39065132586, both success, b01c72bd). Light: home-light-medium
  one line over the map just above the sheet, crossing only the coastline, clear of the route and the (i);
  plan-preview-light one line "Route data © OpenStreetMap contributors" in the sheet's bottom inset above the mode
  bar, clear of Start and the disclaimer line (both now above the fold). DARK: home-dark-medium and drive-dark one
  line, but the blurred navy halo over the LIGHT demo tiles (CI's dark mode still draws the light demo style) went
  translucent and muddy - grey text in grey fog, a legibility regression against the old box. Fixed: the halo is a
  crisp one-point outline in `surface` (four radius-0 shadows), the ground fgMuted clears 4.5:1 against.
  home-ax5-medium/collapsed: one line at the DEFAULT caption size, and the home sheet's own text is not at AX5 either,
  so the footer's environment on home is not an accessibility size in that capture; one line is R3's answer there.
  plan-preview-ax5 (previous run) one line at about 19pt, single party. Digest re-approved (3373eb72 -> 0ea47037),
  `wc -l` 100, check-map-attribution exit=0. Re-dispatching for the dark look.
- 2026-10-17T21:10:31Z LOOKED at ios-screenshot 39066945425 (compile 39066941463, both success, 12065615): home-dark-medium one
  line, light-grey glyphs in a crisp navy outline, legible on the light demo tiles; home-light-medium one line, slate
  in a white outline; plan-preview-dark one line in the sheet inset. (drive-dark/drive-light footer band not
  re-cropped in this run; drive-light was one line in 39062709376.) FINAL, after git fetch + merge of origin/main
  (b42d014e, origin/main is an ancestor), acceptance re-run on the merged head:
  A1 `wc -l` AttributionFooter.swift = 100. A2 read in the diff: caption2, no background/RoundedRectangle, every
  visible Text lineLimit(1), dynamicTypeSize(...accessibility2), accessibilityLabel(Text(text)), identifier
  attribution.footer, accessibilityHidden(false). A3 check-map-attribution exit=0 ("37 feature file(s), the app
  shell and AttributionFooter.swift pinned by sha256"); --prove-red as on main (T-0413). A4 check-safety-disclaimer
  exit=0; check-mutate-population exit=0 ("the floor of 173 holds"); check-mutate-only exit=0 ("MUTATE-ONLY OK: 248
  of 248"); check-pins-yaml exit=0 ("PINS-YAML ok pins=53 fields=426"); check-exec-bits exit=0 ("P-OPS-01: 253
  files"); queue-check exit=0 ("QUEUE OK (396 tasks)"). A5 runs 39066941463 / 39066945425 success; footer one line
  at default size in light and dark on home, plan-preview and drive; at most two lines at AX sizes (plan-preview-ax5
  one line, single party; home-ax5 draws at the default caption size); no word broken; no box; covers the coastline
  only, never the route line, the (i), Start or the disclaimer line. Gap: no drive-ax5 capture on main.
