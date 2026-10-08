---
id: T-0324
title: The drive screen on NavAdapter - a second map surface with its attribution, the motion-gated minimal surface, the rejoin banner, a door from the plan preview and a drive shot in ios-screenshot
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-08T14:43:16Z
lease_expires_at: 2026-10-09T00:43:16Z
worktree: .worktrees/T-0324
branch: task/T-0324
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/, Sources/ScenicKit/, Tests/ScenicKitTests/, ops/lib/, ops/mutate/, pins/PINS.yaml, .github/workflows/ios-screenshot.yml]
pins_affected: [P-ATTR-01, P-SAFE-09, P-SAFE-03]
reviewer: null
depends_on: [T-0321]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST in a dated Log entry: where the drive screen lives (a feature target that never imports NavAdapter - the shell composes DriveNavigator's mode and surface into it), what the minimal surface holds (the one large action; how the rejoin state is conveyed there) and what the full surface adds, the door that starts a drive from the plan preview, and which check-map-attribution / check-safety-disclaimer rows a second MapView( surface raises"
  - "what the screen shows for a surface and mode is pure ScenicKit (Linux-tested, full-equality tables over every DriveSurface x DriveMode), and the >4.5 m/s minimal surface is what the screen shows (P-SAFE-09's 'What it cannot see' clause closed)"
  - "attribution stays visible on the drive map (P-ATTR-01's whitelist raised by name for the new surface, seen red then green)"
  - "ios-compile + ios-screenshot pass on the branch with a drive shot (a DEBUG `-screen drive` launch over a simulated location), light and dark"
---
## Brief

Filed by T-0321 (R6): NavAdapter's DriveNavigator exposes `mode` and `surface`, and every decision is ScenicKit's
DriveController, but no screen shows them yet. A drive map is a second `MapView(styleURL:` surface, refused by name by
ops/lib/check-map-attribution until its rows are raised; the shot needs ios-screenshot.yml, which T-0180 is editing
(hence depends_on). Also open from T-0321: Ferrostar step durations are 0 (the screen should show PlanPreview's ETA);
spoken guidance (TTS) and Live Activity stay separate follow-ups.

## Log
- 2026-10-08T13:20:42Z filed by agent/claude-opus-5 (owner of T-0321) from T-0321's R6.
- 2026-10-08T14:42:46Z agent/claude-opus-5 (orchestrator): depends_on T-0180 dropped - T-0180 waits on an owner sign-off with no date; the claimer adds the drive shot WITHOUT editing .github/workflows/ios-screenshot.yml if the shot list lives elsewhere, otherwise with the smallest edit and a merge-main round when T-0180 lands.
- 2026-10-08T14:43:16Z claimed by agent/claude-opus-5; lease until 2026-10-09T00:43:16Z
- 2026-10-08T14:47:38Z agent/claude-opus-5 (owner) MEASURE then RULE FIRST, before any code.
  MEASURED on 8d39f215 (origin/main == HEAD, T-0180 not landed): one map surface - `MapView(` and `styleURL:` each
  at FeatureScenicHome/ScenicHomeScreen.swift(1) beside the definition MapAdapter/MapView.swift; `AttributionFooter(`
  at FeaturePlanSheet/PlanPreviewCard.swift(1) and ScenicHomeScreen.swift(1); `DriveBasemap.resolve(` once (home);
  `BasemapResolver.losAngeles(` once (FeatureScenicHome/DriveBasemap.swift); `DriveNavigator` constructed nowhere and
  `import NavAdapter` nowhere. bash ops/lib/check-map-attribution green. The shot list is the run script of
  .github/workflows/ios-screenshot.yml (`for SHOT in collapsed medium fastest settings paywall surprise`), pinned
  whole by ops/lib/ios_screenshot_pinned.py - it lives nowhere else, so the workflow takes the smallest edit.
  R1 WHERE THE SCREEN LIVES: `DriveScreen` in FeatureScenicHome - the one feature target that already depends on
  MapAdapter and ScenicKit; a new target needs apps/ios/Packages/ScenicApp/Package.swift, serial-only and outside
  touches. FeatureScenicHome never imports NavAdapter (check-ferrostar-imports). The SHELL composes: NavAdapter gains
  `DriveHost`, a SwiftUI view owning the DriveNavigator as a StateObject (start on appear, stop on disappear) that
  hands the navigator's published `display` to a content closure; the shell writes
  `DriveHost(navigator:) { display in DriveScreen(preview:display:onEnd:) }`.
  R2 WHAT IT SHOWS is pure ScenicKit: `DriveDisplay(surface:mode:)`, and `DriveDisplay(session:)` - the entry
  DriveNavigator publishes - with four fields: actionTitle, actionMinHeight, status, showsDetails. MINIMAL (above
  4.5 m/s, unknown speed, before the first fix): the map with its credit (a licence term, not a control) and the one
  action, `End drive`, 60 pt tall; the rejoin and reroute state is conveyed by ONE short caption line inside that
  action's own block (no second target, no banner); voice is the TTS follow-up. FULL adds the status as a sentence
  banner, PlanPreview's ETA line with the estimate badge (Ferrostar's step durations are 0, per the Brief) and the
  conditions line; the action is 44 pt. DriveScreen reads `display` only - never DriveSurface, DriveMode or a
  `surface` - a whitelist guard (R7).
  R3 DISCLAIMER: CLAUDE.md's "stays visible on the route screen" against P-SAFE-09's "minimal: the one large action
  and voice, nothing else". Ruled: the route screen is the plan preview (`plan.conditions`) and the home; the drive
  screen shows PlanPreview.conditions on the FULL surface, and while moving P-SAFE-09 wins. check-safety-disclaimer
  rows raised: -frozen's FROZEN_APP_SHELL re-typed for the new shell lines, the shell digest in -pinned, and every
  touched file's digest in -linked-digests.txt (and -pinned's feature rows for the new FeatureScenicHome files).
  R4 THE DOOR: PlanPreviewCard gains `Start the drive` (SF Symbol car.fill, 44 pt) through PlanSheetScreen's new
  `onDrive: (PlanPreview) -> Void`, handed in by the shell; the shell keeps the preview in state and the window shows
  DriveHost in place of the home until `End drive` (a root swap, not a cover: no presentation can race the home's
  disclaimer sheet). The plan itself is already behind the disclaimer.
  R5 ATTRIBUTION ROWS raised BY NAME in check-map-attribution: SURFACE_SET (`MapView(`, `styleURL:`) and FOOTER_SET
  each + FeatureScenicHome/DriveScreen.swift(1); the screen limbs (d) composed footer from the SAME bindings the map
  is mounted with and (e) not hidden run over the drive screen too; the drive's tiles come from a new
  `DriveBasemap.planned(appearance:)` that the home's LA arm also calls, so `BasemapResolver.losAngeles(` stays once,
  `DriveBasemap.resolve(` stays the home's, `DriveBasemap.planned(` is whitelisted once more at DriveScreen; the
  credit-site whitelist (g) gains the drive footer line and the drive line's `dataCredit: PlanPreview.attribution`.
  Seen red (the new surface refused by name) before the rows are raised.
  R6 THE SHOT: DEBUG `-screen drive` is read by FeatureScenicHome's `DriveRehearsal` inside `#if DEBUG` (the shell
  carries no `#` directive) and returns a fixture PlanPreview over a short literal line in the Santa Monica
  Mountains; `LaunchScreen(rawValue: "drive")` is nil, so Settings stays closed. The workflow grants location and
  runs `simctl location start --speed=15` along that line before the drive launch, so the shot is MINIMAL because the
  fixes are moving (and it would be minimal before any fix anyway). Light and dark, `drive-light`, `drive-dark`.
  R7 P-SAFE-09's "What it cannot see" first clause is closed structurally: the DriveDisplay tests join P-SAFE-09's
  named-tests row, and ops/lib/check-drive-display.py whitelists every apps/ios line naming DriveDisplay or
  `.display` and refuses DriveSurface/DriveMode/`surface` anywhere in FeatureScenicHome (seen red, then green). The
  flicker clause stays.
  R8 POPULATION: Sources/ScenicKit/Drive/DriveDisplay.swift joins ops/mutate/drive.py's SUBJECT_MODULES and
  drive_mutations.py gains its mutations with the floor raised; DriveDisplayTests joins TEST_FILES.
- 2026-10-08T15:20:00Z agent/claude-opus-5 (owner) RED then GREEN, by name, as each landed (quoted, not re-run):
  DriveDisplayTests with DriveDisplay(surface:mode:) a stub (always the full guiding display) and
  DriveDisplay(session:) ignoring the session: `× Test "P-SAFE-09: moving shows only the one large action - 60 pt, no
  details - in every mode" failed ... with 3 issues`, `× Test "P-SAFE-09: the session's display is the table's row
  for its own surface and mode, before and after fixes" failed ... with 5 issues`, `× Test "P-SAFE-09: the drive
  screen shows the typed display for every surface and mode, compared whole" failed ... with 5 issues` (the table's
  own cross-product meta test passed, as it must); implemented: `√ Test run with 9 tests in 2 suites passed`
  (DriveDisplayTests + DriveMotionGateTests); `NAMED P-SAFE-09 passed=9/9`.
  P-ATTR-01 with DriveScreen.swift added and no row raised: `P-ATTR-01: the footer construction AttributionFooter(
  occurs outside its tracked set; found: ...PlanPreviewCard.swift(1) ...FeatureScenicHome/DriveScreen.swift(1)
  ...ScenicHomeScreen.swift(1)`; FOOTER_SET raised alone: `P-ATTR-01: a map mount outside its tracked set:
  \`MapView(\` at Packages/ScenicApp/Sources/FeatureScenicHome/DriveScreen.swift(1) ...ScenicHomeScreen.swift(1),
  tracked ...ScenicHomeScreen.swift(1)`; MAP_SET and require_drive_surface (check-map-attribution-sites, R5) raised:
  `P-ATTR-01 (f2): the drive map ...DriveScreen.swift - footer text: CreditLine.composed(basemap:
  style.attributionText, routeData: route?.dataCredit), mounted from style and route, one DriveBasemap.planned(,
  nothing hidden.`, then red only on the content pin (`FeatureScenicHome's file set is not the approved one: added
  DriveMapLine.swift DriveRehearsal.swift DriveScreen.swift`) until the digests were re-typed; then green.
  P-SAFE-03 -frozen: `the app shell ScenicDriveApp line 6 of 32 ...: approved \`\`, found \`@State private var drive =
  DriveRehearsal.atLaunch\`` until FROZEN_APP_SHELL was re-typed; -doors' two shell lines re-typed for the new
  indentation (the shell's home chain moved into `private var home`).
  ops/lib/check-pbxproj-graph.py (R6 addendum: MEASURED `grep -c Location apps/ios/ScenicDrive/Info.plist` = 0, so
  no fix could ever reach DriveNavigator on a device; the check's own comment said the key returns with the first
  feature that asks for location): flipped to require NSLocationWhenInUseUsageDescription >= 30 chars - `FAIL
  NSLocationWhenInUseUsageDescription states its purpose in >= 30 characters  absent`, then `pbxproj-graph: 28
  assertions, 0 failed` with the key added.
  ios-screenshot.yml's drive arm: `IOS-COMPILE-GUARDRAILS: ...steps[4].run: differs from the pinned value` until
  ops/lib/ios_screenshot_pinned.py was re-typed; then `PROVE-RED OK: 69 mutations red` including the new `T-0324:
  the drive shot dropped`.
  ops/lib/check-drive-display.py (R7): green `17 approved whole lines`, `--prove-red` `PROVE-RED OK: 6/6 refused by
  name` (the screen, the shell, the host and the navigator each building their own display, the screen showing the
  details unconditionally, a new feature file naming DriveSurface).
- 2026-10-08T15:58:00Z agent/claude-opus-5 (owner) iOS CI, the drive shot LOOKED AT, merge-main, and the acceptance
  block re-run on the merged head 901db45a (origin/main e158ddbc merged clean: T-0320's Traffic, T-0323's claim).
  CI on dd523d9b (the first dispatch on d43b67e6 was cancelled: DriveScreen lacked `import Handoff` for CreditLine,
  and DriveMapLine's untyped nested literals were made explicit before any run read them): ios-compile 37800200376
  success (4m10s); ios-screenshot 37800207441 success (17m26s). Downloaded and read drive-light.png and
  drive-dark.png: the MINIMAL surface in both - the planned line drawn over the demo tiles (CI has no la.pmtiles), the
  composed credit pill `© MapLibre · Natural Earth · Route data © OpenStreetMap contributors` bottom right above the
  controls and fully visible in both themes, MapLibre's logo top left, the location arrow in the status bar (the
  simulated 15 m/s fixes arriving), one `End drive` button full width and ~60 pt on the primary fill
  (onPrimary text: white in light, dark in dark), no caption (guiding: the fixes are on the line), no ETA, badge or
  conditions. 037506a8 after the shot changes DriveMapLine's spelling only (`let properties: [String: String] = [:]`,
  the -doors `](` reader) and digests.
  ACCEPTANCE, re-run here:
  1 MEASURE then RULE FIRST: the 2026-10-08T14:47:38Z entry (R1-R8), written before any code.
  2 pure ScenicKit, full-equality over every DriveSurface x DriveMode: DriveDisplayTests (4 names, in P-SAFE-09's
    row) - `NAMED P-SAFE-09 passed=9/9`; full Linux suite `√ Test run with 666 tests in 123 suites passed`, XCTest
    `Executed 47 tests, with 1 test skipped and 0 failures`; mutants 50-57 `MUTATE OK caught=8/8` (floor 49 -> 57);
    the screen reads only the navigator's display: `python ops/lib/check-drive-display.py` -> `P-SAFE-09 (screen): 17
    approved whole lines ...`, --prove-red 6/6; P-SAFE-09's "What it cannot see" first clause replaced by that.
  3 attribution on the drive map: `bash ops/lib/check-map-attribution` rc=0 with `P-ATTR-01 (f2): the drive map
    ...DriveScreen.swift - footer text: CreditLine.composed(basemap: style.attributionText, routeData:
    route?.dataCredit), mounted from style and route, one DriveBasemap.planned(, nothing hidden.` (red quoted above).
  4 ios-compile + ios-screenshot green with drive-light/drive-dark (above).
  Bare guards on 901db45a, each rc=0: check-safety-disclaimer, check-map-attribution, check-store-links.py,
  check-ferrostar-imports.py, check-drive-display.py, check-pbxproj-graph.py (`28 assertions, 0 failed`),
  check-ios-compile-guardrails.py, check-mutate-population.py (`the floor of 138 holds`), check-line-cap (`490 Swift
  files ... none over 300 lines`), check-pins-yaml.py (`pins=48`), queue-check (`QUEUE OK (316 tasks)`).
  NOT DONE HERE, follow-ups the Brief already names as separate: spoken guidance (TTS) - the minimal surface's
  "voice" half - and the Live Activity. No device has run a drive; the full surface (stopped) has no shot.
  ops/test on this worktree: Swift `√ Test run with 666 tests in 123 suites passed`, then `FAIL: services/api exists but
  vitest produced no report` - this worktree has no services/api/node_modules (nothing under services/ is touched
  here); the TESTS line is CI's to print on the PR.
- 2026-10-08T16:14:31Z agent/claude-opus-5 (owner) PR #211 core red on P-OPS-01: `ops/lib/check-drive-display.py (data, should be 100644, is 100755)` - ops/lib python modules are data, run as `python <path>`; mode set to 100644, `bash ops/lib/check-exec-bits` green locally (`P-OPS-01: 185 files, 23 required present, all modes correct`).
