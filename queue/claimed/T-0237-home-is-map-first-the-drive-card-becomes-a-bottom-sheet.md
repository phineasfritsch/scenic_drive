---
id: T-0237
title: Home is map-first - the map fills the screen, the drive card becomes a bottom sheet with detents, the chips float over the map; attribution and the conditions line visible at every detent; re-shot
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-26T03:29:17Z
lease_expires_at: 2026-09-26T13:29:17Z
worktree: .worktrees/T-0237
branch: task/T-0237
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, apps/ios/Packages/ScenicApp/Sources/DesignSystem/, apps/ios/Packages/ScenicApp/Sources/MapAdapter/MapView.swift, apps/ios/Packages/ScenicApp/Sources/MapAdapter/MapRouteCoordinator.swift, apps/ios/ScenicDriveUITests/, .github/workflows/ios-screenshot.yml, ops/lib/ios_screenshot_pinned.py, ops/lib/check-map-attribution, ops/lib/check-drive-copy, ops/lib/check-safety-disclaimer, Sources/Handoff/, Tests/HandoffTests/]
pins_affected: [P-ATTR-01, P-SAFE-03]
reviewer: null
depends_on: [T-0236]
verify: [ops/test, ops/check-pins]
acceptance:
  - "RULED in the Log before code, from the T-0236 screenshots (.artifacts/screens/home-light-T0236*.png): today the header is four paragraphs (title, road list, crow-flies line, timing, the 'Preview build' caption) and the map starts at 456 pt of 874 - the drive the app exists to show gets the bottom half. The ruling names: the sheet's detents (a collapsed height that shows the title, the conditions line and 'Open in Apple Maps'; a medium that adds the road list and the timing sentence; whether large exists), which copy moves where, whether the 'Preview build' caption survives (and where), and the camera padding per detent so the whole route stays in frame above the sheet"
  - "attribution: the composed map credit (T-0236 round 2) is visible and unobscured at EVERY detent in both themes - check-map-attribution binds the new mount (whitelist, identifier-anchored) and its --prove-red gains a row that hides the credit behind the sheet; the safety line 'Conditions change. Verify locally.' stays visible at every detent (P-SAFE-03's route-screen half)"
  - "the sheet cannot be dismissed (interactiveDismissDisabled) and the map stays interactive above it (presentationBackgroundInteraction); the chips sit over the map below the status bar with a legible background in both themes; every tap target >= 44 pt"
  - "ios-compile green on the head; ios-screenshot green on the SAME head producing light + dark at the collapsed AND medium detents (a launch argument selects the detent - four PNGs), downloaded to the main checkout's .artifacts/screens/home-*-T0237-*.png and DESCRIBED in the Log: where the route sits, the credit, the conditions line, the button"
  - "the credit pill never breaks a party across lines (T-0236 round 2's pill wrapped '... Natural Earth · ©' / 'OpenStreetMap contributors'): a non-breaking space after each copyright sign in the composed credit, or a layout that keeps each party whole - seen in the re-shot screenshots"
---
## Brief

The owner asked for a presentable app. The engine's Saddle Peak line is on the map as of T-0236, but the screen reads
as a document with a map under it. Every maps app the owner already uses is map-first with a sheet (Apple Maps,
Google Maps); the plan's UI section says 'sheets for planning' and 'lower-right reserved for attribution'.
Positioning is 'calm adventure' and the tagline 'Take the long way. Unwind.' - the collapsed sheet is the first thing
anyone sees, so its words are unhurried and few. No thrill words.

## Log
- 2026-09-25T23:35:28Z filed by agent/claude-opus-5 (orchestrator) from the T-0236 round-1 screenshot. Promote to ready/ when PR #130 merges (touches overlap FeatureScenicHome and check-map-attribution).
- 2026-09-26T01:30:07Z added by agent/claude-opus-5 (orchestrator): the pill-wrap cosmetic from rv2-t0236's recordable (3), deferred here because this task re-shoots the screen.
- 2026-09-26T03:28:46Z PROMOTED to ready/ by agent/claude-opus-5 (orchestrator): PR #130 merged (T-0236, c1dc1e8) - the route line, CreditLine.composed and check-map-attribution limb (g) are on main.
- 2026-09-26T03:29:17Z claimed by agent/claude-opus-5; lease until 2026-09-26T13:29:17Z
- 2026-09-26T03:40:46Z RULED by agent/claude-opus-5 (owner), before any code, from home-{light,dark}-T0236-r2.png.
  MEASURED on the light shot (1206x2622 px, 3x, 402x874 pt): chips 53-86 pt, title two lines to ~130 pt, road list
  four lines, crow-flies two, timing three, the 'Preview build' caption four; the map starts at ~456 pt of 874 -
  the drive gets the bottom half, and its button, conditions line and credit are stacked on the map's lower third.
  R1 SHEET KIND: an OVERLAY sheet (`HomeSheet`, FeatureScenicHome), not a system `.sheet`. Why: (a) the credit pill
  and the sheet are the only two children of one `VStack(spacing: 0)`, pill first, so the pill sits on the map
  directly above the sheet's top edge at every detent AND mid-drag, by layout; a system sheet is presented in its
  own window over the presenting view, so a credit kept above it has to be offset by a height reported back across
  the presentation, which lags the drag and which no source check can bind; (b) P-SAFE-03: the disclaimer is a
  `.sheet` on ScenicHomeScreen, and a drive sheet presented forever turns it into a nested presentation from inside
  that sheet - moving lines check-safety-disclaimer pins; (c) the camera padding and MapLibre's logo/(i) margins
  need the sheet's height in the MAP's hierarchy - measured with onGeometryChange in the same ZStack. Acceptance
  line 3's parentheticals are the system-sheet API names; an overlay has no presentation: nothing dismisses it (no
  swipe-down, no dismiss action - a drag only moves between the two detents) and it is not modal (the map above
  it takes every touch). Those two properties hold by construction and the screenshots show the map above it.
  R2 DETENTS: `collapsed` = grabber (44 pt button), title, the conditions line, 'Open in Apple Maps' (~200-240 pt
  with the home-indicator inset); `medium` = collapsed + the road list, DriveFacts (the crow-flies line and the
  timing sentence, unchanged) and the caption. Heights are CONTENT-driven, not fixed points: at the largest
  Dynamic Type sizes the collapsed sheet grows instead of clipping the safety line. NO large detent: the map is the
  screen, and at large the credit - which lives on the map above the sheet - would have no map left to sit on.
  Switching: a vertical drag (> 40 pt) or a tap on the grabber (VoiceOver-labelled; dragging is never the only
  way). A launch argument `-homeDetent collapsed|medium` (UserDefaults' argument domain) picks the first detent.
  R3 COPY MOVES: chips -> float over the map below the status bar on a material band; title -> sheet, first, one
  line at default size, rewritten to name + where to where ("Saddle Peak · Topanga to Malibu", "Skyline loop · SF
  and back", "Westwood loop · coast and back"); a failure card (if any) -> collapsed, above the conditions line;
  conditions line -> collapsed, under the title, above the button, footnote fgMuted on the sheet's `bg` (the token
  pair; the chip it wore over the tiles is dropped because the sheet is its ground); button -> collapsed; road list,
  DriveFacts, caption -> medium. No DriveCopy switch is added (titles rewritten in place), so no check-drive-copy
  count moves and that check is unchanged; every line check-safety-disclaimer pins stays in ScenicHomeScreen.swift.
  R4 'PREVIEW BUILD' CAPTION survives, medium detent only, last, footnote; its preamble shrinks from "Preview build:
  three fixed drives, X selected." to "Preview build." - the chips already say three and which. The rest stays: it
  is the honest sentence about the ground under the line (demo tiles show no roads).
  R5 CAMERA PADDING PER DETENT: MapView gains `obscuredTop` (the chip band's bottom, global) and `obscuredBottom`
  (map height minus the credit band's top, global); the fit padding is each plus 24 pt, LESS MapLibre's own
  contentInset, because 6.31 adds it (MLNMapView.mm setVisibleCoordinates: `padding += contentInset`), so the whole
  route sits between the chips and the credit pill at each detent; a detent change refits, animated.
  R6 ORNAMENTS: the credit pill lower-right on the map, directly above the sheet; MapLibre's logo rides up with the
  sheet into the credit band's lower-left (logoViewMargins from obscuredBottom less the safe-area inset the
  ornaments are anchored to); the (i) top-left and the compass top-right, both below the chip band. Never under the
  sheet, never under the chips.
  R7 NBSP: CreditLine.composed makes every space INSIDE a party non-breaking (after each ©, and between words) and
  leaves the separator's spaces breakable, so the pill can wrap only between parties. composed's nil-route contract
  changes from "unchanged, character for character" to "the same words, each party's inner spaces non-breaking";
  the three existing tests compare the SPOKEN text (NBSP read as a space), and a new test by name binds the property,
  red first.
  R8 GUARDS: check-map-attribution limb (h), new file ops/lib/check-map-attribution-sheet (lib is at the cap): a
  whitelist - `HomeSheet(` constructed at ScenicHomeScreen.swift(1) and nowhere else; the mount is five approved
  WHOLE lines, consecutive after dropping only lines whose trimmed text starts with // (`VStack(spacing: 0) {`, the
  footer line, the HomeSheet line, `}`, the onGeometryChange line), then a line starting with `}`; `.sheet(` only
  at ScenicHomeScreen.swift(1), whole line `.sheet(isPresented: $isShowingDisclaimer) {`; `presentationDetents`
  nowhere; the mount after the one MapView( line (drawn above the map). --prove-red rows: the credit moved into the
  sheet, the stack made a ZStack, the sheet pulled up over the credit, the credit below the sheet, a negative
  spacing, the drive card as a system sheet with detents, a second HomeSheet overlaid.
  R9 TOUCHES WIDENED by ops/lib/ios_screenshot_pinned.py: ios-screenshot.yml is compared by EQUALITY with that
  module's expected() and its --prove-red anchors the launch line; extending the capture loop without it is a red
  guardrail. The Brief names the workflow and says extend it; the module is its other half.
  R10 SCREENSHOTS: the capture loop runs light/dark x collapsed/medium, `simctl launch ... -homeDetent <d>`, PNGs
  home-<look>-<detent>.png; downloaded as home-<look>-T0237-<detent>.png. No UI test is written: there is no UI
  test target (apps/ios/ScenicDriveUITests does not exist; T-0180 owns the first XCUITest), and the launch
  argument is the whole selection mechanism.
- 2026-09-26T04:13:10Z BUILT by agent/claude-opus-5 (owner). RED FIRST (R7), Linux, by name: `swift test
  --scratch-path .build-t0237 --filter CreditLine` with the new test and the old composed -> `× Test "the credit
  pill never breaks a party across lines: every space inside a party is non-breaking" recorded an issue ...
  Expectation failed: !((party → "© MapLibre").contains(" ") → true)` and `(Self.occurrences(of: "©", in: pill) →
  2) == (Self.occurrences(of: "©" + Self.noBreakSpace, in: pill) → 0)` (13 issues, the other 4 tests passing);
  after CreditLine.composed's `unbroken(_:)`: `√ Test run with 5 tests in 1 suite passed` (commit 9fed536).
  UI + guards (commit 3ab5a77): HomeSheet, HomeSheetDetent, DriveDetails, ScenicHomeScreen (220 lines),
  MapView/MapRouteCoordinator (covered edges), DriveCopy titles + preamble; `bash ops/lib/check-map-attribution` ->
  exit 0 with `P-ATTR-01 (h): HomeSheet declared at .../HomeSheet.swift(1), built at .../ScenicHomeScreen.swift(1),
  directly under the pill in the approved five-line mount after MapView(; the only presentation is
  `.sheet(isPresented: $isShowingDisclaimer) {`.`; check-safety-disclaimer exit 0 (isSafetyDisclaimerAcknowledged
  at GatedHandoffButton.swift(2) ScenicHomeScreen.swift(4), unchanged); check-drive-copy exit 0, unchanged (no
  count moved, R3); `python ops/lib/check-ios-compile-guardrails.py` -> `ios-screenshot.yml equals the pinned
  workflow`, and --prove-red -> `PROVE-RED OK: 66 mutations red, 6 legitimate spellings green over 2 workflows`.
  ios-compile.yml run 36216670577 on 3ab5a77: `{"conclusion":"success","headSha":"3ab5a770d63d...","status":
  "completed"}` - first dispatch. ios-screenshot.yml run 36217144027 dispatched on the SAME head 3ab5a77.
- 2026-09-26T04:25:48Z SHOT, ROUND 1, by agent/claude-opus-5 (owner): run 36217144027 on 3ab5a77 `{"conclusion":
  "success","headSha":"3ab5a770d63d...","status":"completed"}`, artifact ios-screenshots = home-{light,dark}-
  {collapsed,medium}.png (1206x2622 each), kept in the main checkout as .artifacts/screens/home-*-T0237-*.png.
  `bash ops/lib/check-map-attribution --prove-red` (background, logged) -> `prove-red: 32/32 mutations refused by
  name`, H1-H8 each `1 yes`. DESCRIBED (pt = px / 3): light collapsed - map full-bleed under the status bar; chips on
  a pale material band ~50-93 pt, Saddle Peak selected; (i) top-left at ~100 pt, just under the band; the route
  fills the width between ~210 and ~405 pt, clear of the chips and of the pill; the credit pill lower-right on the
  map, ~475-510 pt, two lines `© MapLibre · Natural Earth ·` / `© OpenStreetMap contributors` - it wraps AT THE
  SEPARATOR, no party broken (acceptance 5 seen); the sheet from ~516 pt (~200 pt tall with the home indicator):
  grabber, `Saddle Peak · Topanga to Malibu` on one line, `Conditions change. Verify locally.`, the orange `Open in
  Apple Maps` (~33 pt text band, 44+ pt target). Light medium - the same sheet from ~320 pt adds the road list (4
  lines), the crow-flies line, the timing sentence and the `Preview build. The line is the route ...` caption; the
  pill rides up to ~280-313 pt, still on the map above the sheet; the route refit to ~130-310 pt. Dark collapsed /
  medium - the same geometry; the sheet on navy `bg`, fg white, conditions line muted, button orange with navy
  text; the chip band dark over the (light) demo tiles; the pill on dark `surface`, legible. Credit and conditions
  line visible in all four.
  FAILED, fixed before round 2: (1) MapLibre's LOGO is on none of the four PNGs (a pixel scan of the credit band's
  left half, 1850-2060 px, finds no dark pixel) - it was placed bottom-left with margins from the bottom covered
  edge, while the (i), placed from the TOP edge, landed exactly under the chips. Correction to R6: every ornament
  hangs from the top covered edge - the logo top-left, the (i) top-right, the compass 44 pt under the (i).
  (2) At medium the route's lower-left end dips to ~312 pt, level with the pill (beside it, not under it, above
  the sheet): the fit had less padding than the uncovered map allows, because R5 subtracted `contentInset` on the
  assumption that MapLibre adds it back. Correction to R5: MapView sets `automaticallyAdjustsContentInset = false`
  and `contentInset = .zero` (the setter exists in 6.31, MLNMapView.mm:1441), and the fit padding is exactly each
  covered edge + 24 pt. No guard reads either; the round-2 screenshots are the check.
- 2026-09-26T06:46:29Z SHOT, ROUND 2, by agent/claude-opus-5 (owner): ios-compile.yml run 36217861418 on 31c4985
  `{"conclusion":"success"}` (second dispatch); ios-screenshot.yml run 36224025703 on the SAME head 31c4985
  `{"conclusion":"success","headSha":"31c4985ea80b...","status":"completed"}` (second dispatch), downloaded as
  .artifacts/screens/home-{light,dark}-T0237-{collapsed,medium}.png (round 1 kept in .artifacts/screens/T0237-r1/).
  DESCRIBED (pt = px / 3): all four - the map full-bleed under the status bar; the chips on a material band ~50-121
  pt (pale in light, dark olive in dark), Saddle Peak selected (orange), the others on `surface`; the MapLibre
  LOGO now visible top-left just under the band (~133-150 pt) and the (i) top-right level with it - the round-1
  logo failure is fixed; the credit pill lower-right on the map directly above the sheet, two lines
  `© MapLibre · Natural Earth ·` / `© OpenStreetMap contributors`, wrapped AT THE SEPARATOR (acceptance 5 seen
  again); the sheet: grabber, `Saddle Peak · Topanga to Malibu` on one line, `Conditions change. Verify locally.`
  in fgMuted, the orange `Open in Apple Maps` (~33 pt band + padding, 44+ pt target). Collapsed: pill ~623-660 pt,
  sheet from ~676 pt (~198 pt tall). Medium: pill ~365-410 pt, sheet from ~418 pt with the road list (4 lines), the
  crow-flies line, the timing sentence and `Preview build. The line is the route ...` (3 lines). Dark: sheet on navy
  `bg`, title white, conditions muted, button orange with navy text, pill on dark `surface` - all legible.
  FAILED, MEASURED (a PIL scan for the route colour (37,99,235), gitignored .artifacts/measure_t0237.py): the route
  box is x 21-380, y 301-539 pt collapsed and x 21-380, y 173-410 pt medium - the SAME zoom at both detents, and
  IDENTICAL to round 1's boxes, so round 1's Log reading "(~312 pt)" was an eyeball error and the contentInset
  change of 31c4985 moved nothing. At medium the route's lower-left end reaches 410 pt, below the pill's top (~365
  pt, beside it, not under it) and 8 pt above the sheet: R5's "the whole route between the chips and the credit
  pill" does not hold. ROOT CAUSE, from the numbers: both boxes' centres (420, 291.5) sit exactly where a fit with
  a bottom padding 96 pt (= 62 + 34, the two safe-area insets) too small puts them - `mapHeight`, read by
  `onGeometryChange` OUTSIDE `.ignoresSafeArea()`, is the safe-area height 778, not the drawn 874, so
  `obscuredBottom = mapHeight - creditBandTop` was 96 pt short; at medium the open band (145-437 pt) was taller
  than the route, so the width decided the zoom at both detents. FIX (this commit): no SwiftUI height is measured.
  `MapView(coveredAboveY:coveredBelowY:)` takes the chip band's bottom and the credit band's top in WINDOW
  coordinates, and `MapRouteCoordinator.coveredEdges(in:)` converts them with UIKit's `convert(_:from: nil)` into
  the MLNMapView's own frame (nil until it is in a window). A stub typecheck of the extracted coordinator code
  (swiftc, Windows) printed `Covered(top: 121.5, bottom: 509.0)` for (121.5, 365) and a logo margin y 67.5 (the
  same as round 2's, which landed). Expected at medium: the route zoomed out into 145-341 pt, wholly above the pill.
- 2026-09-26T07:34:55Z SHOT, ROUND 3, and the ACCEPTANCE BLOCK re-run, by agent/claude-opus-5 (owner), on 96ead41.
  ios-compile.yml run 36225144393 on 96ead41 `{"conclusion":"success","headSha":"96ead418fa83...","status":
  "completed"}` (third dispatch, the last); ios-screenshot.yml run 36225665243 on the SAME head 96ead41
  `{"conclusion":"success","headSha":"96ead418fa83...","status":"completed"}` (third dispatch, the last),
  downloaded as .artifacts/screens/home-{light,dark}-T0237-{collapsed,medium}.png (round 2 kept in
  .artifacts/screens/T0237-r2/). MEASURED (the route-colour scan, pt = px / 3): route box light collapsed x 21-380,
  y 253-491 (centre 372; the open band 145-600 predicts 373); light medium x 50-352, y 143-343 - ZOOMED OUT to fit
  the band 145-341, its lowest point 22 pt above the pill's top; dark collapsed y 269-491, dark medium y 156-343
  (the dark casing is not in the scan colour). The R5 fix holds at both detents.
  DESCRIBED, all four: the map full-bleed under the status bar; the chips on a material band ~50-121 pt (pale in
  light, dark olive in dark), Saddle Peak selected in orange, Westwood loop and SF Peninsula on `surface`; the
  MapLibre logo top-left just under the band (~133-151 pt), the (i) top-right level with it - both on the map,
  neither under the chips or the sheet. COLLAPSED: the route across the upper-middle map, clear of the band and
  the pill; the credit pill lower-right on the map ~624-668 pt, two lines `© MapLibre · Natural Earth ·` /
  `© OpenStreetMap contributors`, wrapped at the separator with no party broken (acceptance 5); the sheet from
  ~676 pt (~198 pt tall): grabber, `Saddle Peak · Topanga to Malibu` on one line, `Conditions change. Verify
  locally.` in fgMuted, the orange `Open in Apple Maps` full-width (~33 pt of text band inside a 44+ pt button).
  MEDIUM: the route smaller, 143-343 pt, above the coast; the pill ~365-410 pt, still on the map directly above the
  sheet; the sheet from ~418 pt with the same title, conditions line and button, then the road list (4 lines),
  `About 10 miles as the crow flies ...`, `A slow mountain afternoon, not a shortcut ...` and `Preview build. The
  line is the route ...` (3 lines, footnote). DARK: the same geometry; the sheet on navy `bg`, title white,
  conditions muted, button orange with navy text; the pill on dark `surface`, legible over the light demo tiles.
  The credit and the conditions line are visible and unobscured in all four.
  GATES, bare, on 96ead41 (origin/main 4368aeb is its ancestor; `git fetch origin` at 07:34Z: main has not moved):
  `swift test --scratch-path .build-t0237` -> `√ Test run with 339 tests in 47 suites passed` (exit 0);
  `bash ops/lib/check-map-attribution` exit 0 (limb (h) quoted above); `--prove-red` -> `prove-red: 32/32
  mutations refused by name`, H1-H8 each `1 yes` (exit 0); `bash ops/lib/check-drive-copy` exit 0 (not touched,
  so no --prove-red); `check-safety-disclaimer` exit 0; `check-line-cap` -> `P-SRC-02: 122 Swift files tracked
  (Sources=45, Tests=50, apps/ios=27), none over 300 lines`; `check-exec-bits` -> `P-OPS-01: 101 files, 23 required
  present, all modes correct`; `ops/queue-check` -> `QUEUE OK (237 tasks)`; `check-ios-compile-guardrails.py` ->
  both workflows `equals the pinned workflow`; `bash ops/check-pins --source-only` -> `PINS ok=15 skipped=16
  pending=1 expired=0 failed=0 tier=linux source-only`. This entry is the only change after 96ead41.
  ACCEPTANCE: 1 ruled (R1-R10, 03:40Z, before code; R5/R6 corrected in the round-1 and round-2 entries). 2 the
  credit and the conditions line are seen at both detents in both themes; limb (h) binds the mount, and its
  --prove-red refuses the credit hidden behind the sheet (H1-H8). 3 an overlay sheet (R1): nothing dismisses it,
  and the map above it is interactive; the chips are on a material band below the status bar in both themes;
  the chips, grabber and button are each >= 44 pt. 4 ios-compile and ios-screenshot green on the same head
  96ead41, four PNGs, described above. 5 the pill wraps only at the separator (NBSP, red first by name, 9fed536).
- 2026-09-26T08:23:59Z agent/claude-opus-5 (owner) RULING before code, round-1 FAIL on PR #133 (rv1-t0237 B1-B3),
  on 8ae11de == origin/task/T-0237. The three reproductions, re-run here on 8ae11de: B1 (`if sheetDetent ==
  .medium {` wrapped around the mount, lines 100/104) -> `bash ops/lib/check-map-attribution` exit 0; B2 line 179
  `conditions` deleted -> `check-safety-disclaimer` exit 0, and moved into sheetDetails inside a VStack -> exit 0;
  B3 is quoted from the table run in the next entry. All three fail OPEN; B2 is a P-SAFE-* pin failing open.
  R-rv1-1 TOUCHES WIDENED: B2 and B3 live in P-SAFE-03's gate (ops/lib/check-safety-disclaimer, its -lib and its
  -mutations table), outside this task's touches, which named check-map-attribution and check-drive-copy only.
  This PR moved the line P-SAFE-03 reads (pins_affected already lists P-SAFE-03) and broke row 10 by re-indenting
  it, so the repair belongs here, not in a follow-up: touches gains `ops/lib/check-safety-disclaimer` (a prefix:
  the check, -mutations, and one new sourced reader). No claimed task touches those paths (T-0184 names them and
  is in ready/, unclaimed). pins/PINS.yaml's P-SAFE-03 prose says `thirteen mutations`; it is outside touches and
  stays stale this round - recorded open, not fixed.
  R-rv1-2 B1: limb (h)'s whitelist grows OUTWARD to the enclosing whole lines - before the mount the outer stack's
  opening five (`VStack(spacing: 0) {`, `chips`, blank, `Spacer(minLength: 0)`, blank; the //-lines between are
  dropped as before), after it the exact closes `}`, `}`, `.background(DesignTokens.bg)` (outer VStack, ZStack,
  the ZStack's first modifier). A wrapper opened anywhere between the outer stack and the mount, or closed anywhere
  between the mount and `.background`, adds a whole line the list does not have and is refused; the old "next line
  starts with }" test is gone. Blank lines are compared whole (the reader still drops only //-lines). New row H9:
  the reviewer's conditional wrap, which must be refused by name.
  R-rv1-3 B2: check-safety-disclaimer is at 300 lines, so the new reader is a sourced file,
  ops/lib/check-safety-disclaimer-sheet (100755 like -lib), loaded through the same missing-file refusal. It
  decides three WHITELISTS over the screen, whole lines, only //-lines dropped: the line `conditions` occurs
  exactly once; the whole block from `private var sheetSummary: some View {` to the next declaration `private var
  sheetDetails: some View {` equals the approved lines (so the one `conditions` is inside sheetSummary, at its top
  level, with no modifier or wrapper); and `HomeSheet(detent: $sheetDetent, summary: { sheetSummary }, details: {
  sheetDetails })` occurs exactly once - CONFIRMED that limb (h) binds the same line (SHEET_MOUNT[2] in
  check-map-attribution-sheet), repeated here so P-SAFE-03 does not lean on another pin's gate. Whole block, not
  a brace-depth walk: depth over whole lines is moved by a brace in a trailing comment or a string, and reading
  those needs string state, which is the fail-open reader rv3-t0236 refused; the cost is that every edit to
  sheetSummary edits the list, deliberately. It runs after (iv) and before (v), so rows 1-13 keep their names.
  Rows 14-16: the line removed, moved to medium, wrapped in `if sheetDetent == .medium {`.
  R-rv1-4 B3: row 10 re-anchored on the new whole line (8 spaces + `conditions`), refused by name.
  NO SWIFT CHANGE: the screen is right at both detents (round-1 PNGs); the defects are in the gates. Still unseen
  by source: HomeSheet.swift drawing its summary at both detents, and the `conditions` view's own modifiers.
- 2026-09-26T08:58:51Z agent/claude-opus-5 (owner) rv1-t0237 B1-B3 CLOSED in 9a51604 (ruling 651b760), each RED -> GREEN,
  bare, exit codes captured without a pipe. B1: the reviewer's wrap (`if sheetDetent == .medium {` at 100, `}`
  after 104) -> 8ae11de exit 0, 9a51604 exit 1 `P-ATTR-01: the credit is not mounted directly above the sheet in
  .../ScenicHomeScreen.swift.` with `found:    if sheetDetent == .medium {` against `approved: ` blank. B2 removed
  (line 179 deleted) -> exit 0, then exit 1 `P-SAFE-03: the conditions line is not in the collapsed sheet in
  .../ScenicHomeScreen.swift:` / `the whole line `conditions` occurs 0 time(s), expected exactly 1`; B2 moved into
  sheetDetails in a VStack -> exit 0, then exit 1, same reason, `sheetSummary line 17 of 22: approved
  `conditions`, found ``. B3: `check-safety-disclaimer --prove-red` on 8ae11de `prove-red: 12/13 mutations refused
  by name` (row 10 `0 no`), on 9a51604 `prove-red: 16/16 mutations refused by name` (row 10 `1 yes`, rows 14-16
  each `1 yes`). The new reader's missing-file refusal seen red: file moved aside -> exit 1 `P-SAFE-03:
  ops/lib/check-safety-disclaimer-sheet is missing; the check cannot read Swift source without its readers.`
  `check-map-attribution --prove-red` on 9a51604: `prove-red: 34/34 mutations refused by name` (H9 and H10 each `1 yes`). Unmutated tree: both
  checks exit 0. `wc -l`: check-safety-disclaimer 300, -mutations 102, -sheet 93 (new, 100755),
  check-map-attribution-sheet 131, -mutations 157. rv1 recordable 6, `bash ops/check-pins --source-only` on
  9a51604: `PINS ok=15 skipped=16 pending=1 expired=0 failed=0 tier=linux source-only` (exit 0); check-line-cap
  `P-SRC-02: 122 Swift files tracked (Sources=45, Tests=50, apps/ios=27), none over 300 lines`; check-exec-bits
  `P-OPS-01: 102 files, 23 required present, all modes correct`; queue-check `QUEUE OK (237 tasks)`. No Swift
  touched, so no ios-compile or screenshot this round. check-drive-copy untouched: its --prove-red not re-run.
  OPEN: pins/PINS.yaml P-SAFE-03 prose still says `thirteen mutations` (outside touches). NEXT, the last step:
  `git fetch origin` + merge origin/main, the gates re-run bare on the merged head, then the push.
