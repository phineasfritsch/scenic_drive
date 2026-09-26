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
touches: [apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, apps/ios/Packages/ScenicApp/Sources/DesignSystem/, apps/ios/Packages/ScenicApp/Sources/MapAdapter/MapView.swift, apps/ios/Packages/ScenicApp/Sources/MapAdapter/MapRouteCoordinator.swift, apps/ios/ScenicDriveUITests/, .github/workflows/ios-screenshot.yml, ops/lib/ios_screenshot_pinned.py, ops/lib/check-map-attribution, ops/lib/check-drive-copy, Sources/Handoff/, Tests/HandoffTests/]
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
