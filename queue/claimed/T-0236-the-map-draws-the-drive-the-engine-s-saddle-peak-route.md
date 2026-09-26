---
id: T-0236
title: the map draws the drive - the engine's Saddle Peak route becomes the app's first drive, its real road geometry drawn as a line on the map with the camera fitted to it; the credit pill stops covering MapLibre's (i) button
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-25T20:54:56Z
lease_expires_at: 2026-09-26T02:54:56Z
worktree: .worktrees/T-0236
branch: task/T-0236
exclusive: []
touches: [Sources/Handoff/, Tests/HandoffTests/, apps/ios/Packages/ScenicApp/Sources/MapAdapter/, apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, apps/ios/Packages/ScenicApp/Sources/DesignSystem/, apps/ios/ScenicDrive/, ops/lib/, ops/mutate/]
pins_affected: [P-ATTR-01, P-SAFE-03]
reviewer: null
depends_on: [T-0182, T-0199]
verify: [ops/test, ops/check-pins]
acceptance:
  - "a third HandoffDrive, the engine's route from PR #124 (Topanga village -> Fernwood Pacific -> Tuna Canyon -> Saddle Peak -> Schueren -> Piuma -> Malibu Canyon; ops/plan over Tests/Fixtures/t0182/plan-pair at +25, lambda 7.75): its nine decision-point waypoints and destination EXACTLY as ops/plan printed them (the URL is quoted in T-0182's Log), its name, road list and sentences in the same shape the other two drives use (digit-free timing sentence, the card's own sentence, the straight-line figure through StraightLineDistance), becomes the DEFAULT and FIRST drive in the picker; the Westwood loop and the SF Peninsula stay as the second and third choices. Every existing Linux test that iterates HandoffDrive.allCases stays green with the new case, and the new drive's own literals are pinned RED first"
  - "the road GEOMETRY of that route - the recorded GraphHopper path (1,393 points), simplified with a stated tolerance in metres and the resulting point count quoted - ships as a bundled GeoJSON LineString under apps/ios/ScenicDrive/ (the buildable folder syncs it into the app, no Package.swift or pbxproj edit), produced by a committed deterministic script from the fixture so it can be re-derived; MapAdapter draws it as a line layer in the `route` token colour with a casing, above the basemap and below the labels, and fits the camera to its bounds with padding that clears the sheet and the button; a drive WITHOUT geometry (the loop, the Peninsula) draws no line and keeps today's camera - never straight lines between pins, which would cross the mountains"
  - "the map caption for the Saddle Peak drive says the line is the route the engine chose over Saddle Peak instead of PCH; the other drives keep theirs. The credit pill no longer overlaps MapLibre's own attribution (i) button (the first screenshots show it covered at bottom right): move one or the other and rule why the (i) stays reachable (it is MapLibre's attribution control - never hide it)"
  - "bash ops/lib/check-map-attribution + --prove-red, bash ops/lib/check-drive-copy + --prove-red (its typed case-site counts updated for the new case), bash ops/lib/check-safety-disclaimer (P-SAFE-03 counts unchanged), swift test --scratch-path .build/T0236 --filter HandoffTests count line, python ops/lib/check-mutate-population.py (any new numeric symbol populated or allowlisted with a reason), check-line-cap, check-exec-bits, queue-check bare; ios-compile green on the head; then ONE dispatch of ios-screenshot.yml on the branch and the two PNGs downloaded to the MAIN checkout's .artifacts/screens/ as home-light-T0236.png / home-dark-T0236.png, what they show described in the Log (the line on the map, the camera, the pill clear of the (i))"
---
## Brief

The first screenshots of the app ever taken (PR #127, run 36180944684, iPhone 17 / iOS 26.2) show a coherent home
screen and a map that shows nothing: no route, and a caption that says so ("The map doesn't show roads yet"). The
credit pill also sits on top of MapLibre's (i) button. The owner, shown the engine's first route as a web preview,
answered "looks promising" - that route is Topanga to Malibu over Saddle Peak and Piuma instead of PCH, and it is
the only drive we have REAL road geometry for (the recorded GraphHopper path in Tests/Fixtures/t0182/plan-pair/
lambda-7.75.json). Making it the first drive, drawn, is the single change that turns the walking skeleton into
something presentable. It is also plan:22's success criterion in the app itself: "a route this app made".

The loop's freeway middle leg (T-0211) is untouched here and still owed; the loop simply stops being the default.

## Log
- 2026-09-25T20:18:52Z filed by agent/claude-opus-5-5 (orchestrator, from the first CI screenshots of the app - PR #127's run 36180944684). Starts when PR #124 (T-0182, the route) and PR #125 (T-0199, Tests/HandoffTests) have merged.
- 2026-09-25T20:54:56Z claimed by agent/claude-opus-5; lease until 2026-09-26T02:54:56Z
- 2026-09-25T21:10:22Z RULINGS, before any Swift is written (agent/claude-opus-5). The geometry script was drafted
  first ONLY to measure the population the rulings and the test bounds range over; the measurements are quoted here.
  MEASURED over Tests/Fixtures/t0182/plan-pair/lambda-7.75.json paths[0]: 1,393 points, first (34.094352,
  -118.601287) = 5.47 m from ops/plan's source 34.09440,-118.60130, last (34.036524,-118.687061) = 6.22 m from the
  destination 34.03650,-118.68700; each of the nine waypoints is 0.2-0.7 m from a path vertex (indices 98, 168, 350,
  487, 577, 614, 745, 1205, 1228 - increasing, i.e. in driving order); the waypoint chain (nine pins + destination)
  is 17,362.496 m -> 17 km / 10 mi straight line; origin -> waypoint 1 is 1,212.4 m.
  (R1) THE DRIVE. `SaddlePeakRoute` (one type, one file) holds the nine waypoints and the destination EXACTLY as the
  URL quoted in T-0182's Log (lines 207-211 of queue/done/T-0182-*) prints them, plus `origin` = the source
  34.09440,-118.60130 held as a documented literal and NOT put into the URL. DROPPED from the handoff, ruled on two
  grounds: (a) ops/plan printed `WAYPOINTS 9 of max 9` - a tenth pin makes `AppleMapsDirections.url()` throw
  `tooManyWaypoints`, so "the origin becomes waypoint 1 within the cap" is not available without deleting one of the
  engine's decision points, which the acceptance forbids ("EXACTLY as ops/plan printed them"); (b) `source: nil` is
  the app's no-location rule, and the start is wherever the driver is. DISAGREEMENT WITH THE ORCHESTRATOR'S TEXT,
  ruled against it: waypoint 1 does NOT sit "down the same road". The fixture's osm_way_id at waypoint 1's vertex is
  way 691593545 (tertiary) - Fernwood Pacific Drive in the owner's preview - while the source is on way 13388359
  (Entrada Road, residential). The engine's path from the village to pin 1 is Entrada Road, North and South Topanga
  Canyon Boulevard, then Fernwood Pacific Drive; a driver starting in the village reaches pin 1 that way, and a driver
  starting anywhere else reaches it from CA-27 or PCH - either way the scenic middle starts at pin 1. `origin` stays in
  the type because the Linux test binds the LINE's first point to it. Case `saddlePeak`, declared first;
  `defaultDrive = .saddlePeak` with the new ruling appended as a new paragraph under the old one (the old text stays,
  marked superseded). Picker order Saddle Peak, Westwood loop, SF Peninsula. CHIP WORDS: "Saddle Peak" (new),
  "Westwood loop" (renamed from "Los Angeles": two drives are now in Los Angeles, and "Los Angeles" beside "Saddle
  Peak" would claim the other one is not), "SF Peninsula" (unchanged). Identifiers: `home.drive.saddlePeak` new,
  `home.drive.la` and `home.drive.skyline` unchanged (an identifier names what a row is, not its label).
  (R2) THE GEOMETRY. `ops/lib/make-route-geojson.py` (100644, ops/**/*.py rule), Douglas-Peucker at 5 m measured as
  point-to-SEGMENT distance in a local equirectangular plane, coordinates rounded to 5 decimals, `bbox` computed from
  the rounded coordinates. Tolerances measured: 2 m -> 803 points, 5 m -> 483, 10 m -> 318. RULED 5 m / 483 points:
  inside a lane-and-shoulder, keeps the Tuna Canyon / Saddle Peak / Piuma switchbacks, 15,312 bytes. Two runs:
  sha256 c945cbe8da3c3a96f77ea08b7eda93a931bc680af21bd966fbad2237553051db both times. Output
  apps/ios/ScenicDrive/Routes/saddle-peak.geojson (buildable folder; no Package.swift or pbxproj edit).
  `HandoffDrive.routeGeometryResource: String?` ("saddle-peak" / nil / nil) with `routeGeometrySubdirectory` =
  "Routes" and `routeGeometryExtension` = "geojson" as statics, so the app's Bundle.main lookup and the Linux test
  build the path from the SAME three shipping symbols. THE BINDING, stronger than the Brief's two ends: first
  position within 10 m of `SaddlePeakRoute.origin` (measured 5.47 m + <= 0.8 m rounding), last within 10 m of the
  destination (6.22 m + rounding), EVERY waypoint within 10 m of the drawn polyline (<= 0.7 m to a raw vertex + the
  5 m DP bound + rounding) AND in driving order along it, `bbox` == the positions' extent, 483 positions,
  `tolerance_m` 5 and `source_points` 1393. A pin moved off the line, a line re-derived from another path, or a
  resource name pointing at another file each fail by name.
  (R3) MAPLIBRE. `MapView` gains `route: MapRoute? = nil` - the ONE `MapView(` site and the one `init(styleURL` stay
  one each. `MapRoute` (new, MapAdapter): the GeoJSON bytes, its four bbox edges, two SwiftUI `Color`s (MapAdapter
  cannot import DesignSystem - its dependency list is MapLibre alone - so the feature target passes
  `DesignTokens.route` and `DesignTokens.surface` in, and MapAdapter resolves them against the map view's trait
  collection). `MapRouteCoordinator` (new, the MLNMapViewDelegate): one MLNShapeSource `scenic-route`, a casing
  MLNLineStyleLayer width 10 (6 + 2 x 2) in `surface` and the line width 6 in `route`, round join and cap, inserted
  BELOW the first MLNSymbolStyleLayer (above every fill and line of the basemap, under its labels), re-installed on
  every style load. CAMERA: fit to the bbox with edge padding top 48 / left 24 / bottom 200 / right 24 pt. Measured on
  PR #127's home-light.png (1206 x 2622 px, 3x): the map's top edge is ~396 pt, the conditions chip starts ~690 pt of
  874, so the bottom stack (chip, button, credit, home indicator) is ~184 pt - 200 clears it; 48 on top clears the
  moved (i) (8 pt margin + its ~24 pt button). CAMERA RULING: applied once per distinct TARGET VALUE (fit-these-bounds
  or centre-here-at-this-zoom), never per re-render - `updateUIView`'s old rule held for re-renders and still holds;
  what changes is that a new SELECTION moves the camera (today it never did: `updateUIView` ignored the centre, so
  switching drives left the map where it was). No route = `setCenter(destination, zoom 8.5)`, today's values.
  (R4) THE (i). `attributionButtonPosition = .topLeft`, `attributionButtonMargins` (8, 8): the top-left of the map is
  the one empty corner - header band above, compass top-right when rotated, MapLibre logo bottom-left, the credit
  pill bottom-right. `attributionButton.isHidden = false` stays; the (i) is moved, never hidden.
  (R5) COPY. Title "Saddle Peak · Topanga to Malibu over the mountains"; road list "Entrada Road and Topanga Canyon
  Boulevard out of the village, Fernwood Pacific Drive, Tuna Canyon Road, Saddle Peak Road, Schueren Road, Piuma
  Road, down Malibu Canyon Road to Civic Center Way." (the engine's order; names are the owner's preview's lookups of
  the fixture's way ids - the ids and classes are committed data, the names are not); home timing sentence "A slow
  mountain afternoon, not a shortcut - the coast road is the quick way. " + realTimePromise (digit-free; the card keeps
  the shared `failureTimingSentence`); caption "... The line is the route the engine chose over Saddle Peak instead
  of PCH" + ", over Los Angeles roads." (LA tiles) / "; the map under it shows no roads yet." (demo tiles) - it still
  follows the RESOLVED style. Two sentences that the third drive made FALSE are corrected, not left: the caption
  preamble "two fixed drives" -> "three fixed drives" (the rest of the other drives' captions unchanged), and the
  Skyline timing sentence "the longer of the two drives" -> "the longest of the three drives" (112 km vs 47 vs 17
  straight line - the ordering claim is still the only claim).
  (R6) P-PROC-06. `SaddlePeakRoute.swift`: allowlisted with a reason (literals only, no operator). `HandoffDrive`'s
  allowlist reason rewritten for three cases and the resource-name forward. `StraightLineDistance` (covered by
  ops/mutate/straightline_mutations.py) gains one switch arm; no mutation anchor names an arm (grep), and the
  EQUIVALENT entry's witness is extended with the third drive's arithmetic (17,362.496 m -> 10.788 mi -> 10;
  floor 17 km -> 10.563 mi -> 10: still equivalent over the three-case domain). check-drive-copy (iii): the case set
  becomes basemap(1) words(4) picker(1) for all THREE cases (the caption switch names every case once), moved in the
  same commit as the source. MapAdapter is Apple-only and outside P-PROC-06's roots; its bbox arithmetic is none - it
  READS the committed `bbox`.
- 2026-09-25T22:27:14Z RESUMED after a usage limit (agent/claude-opus-5). The previous session stopped with R1-R6
  written and the code UNCOMMITTED; nothing was discarded. Checkpoint commit 0eb5a0f ("T-0236: checkpoint - resumed
  after a usage limit") holds it exactly as found, 22 files. What was verified from here, in order:
  RED BY NAME. Tests and code were both on disk, so RED was demonstrated by putting the shipping symbols back to the
  wrong values (a gitignored driver under .build/, sources restored byte-for-byte after, `git status` empty) and
  running `swift test --scratch-path .build/T0236 --filter HandoffTests`:
  run A - defaultDrive = .santaMonicaMountains, `case saddlePeak` declared after the loop, pin 9's longitude
  -118.70790 -> -118.70890, destination longitude -118.68700 -> -118.68800 - "Test run with 104 tests in 15 suites
  failed ... with 11 issues": `the handoff URL is T-0182's URL without the source` (:48), `the nine pins, the
  destination and the origin are ops/plan's, exactly` (:38 :39 :41 :42), `the straight line through the pins is 17
  km, 10 miles` (:74, the chain), `Saddle Peak is the default and first of three drives` (:56 defaultDrive ->
  .santaMonicaMountains, :58 allCases.first -> .skyline), `each drive maps to its own route, and the default is the
  Saddle Peak drive` (SantaMonicaMountainsChainTests:182), `every pin the handoff carries lies on the drawn line, in
  driving order` (best -> 83.49 m > 10.0), `the drawn line starts at the drive's origin and ends at the destination
  the URL carries` (end -> 86.65 m > 10.0). The geometry binding is red on a pin moved off the line AND on a moved
  destination, each by name and by metres.
  run B - geometryResource "saddle-peak" -> "saddle-peak-v2" - "failed ... with 5 issues": `only the Saddle Peak
  drive names a route geometry resource` (:63), the three geometry tests (file doesn't exist, Code=260), and `every
  drive that names a line ships its file; the loop and the Peninsula name none` (:142).
  The case COUNT (== 3) cannot be driven red by a compiling mutation - removing the case removes the symbol the new
  tests name; against origin/main 006c798's sources the new test files do not compile (`HandoffDrive` has no member
  `saddlePeak`), which is the red that assertion had.
  GREEN: "Test run with 104 tests in 15 suites passed". make-route-geojson.py run twice: "1393 points -> 483 points
  at Douglas-Peucker tolerance 5 m", sha256 c945cbe8da3c3a96f77ea08b7eda93a931bc680af21bd966fbad2237553051db both
  times, `git status` empty after (the committed file IS the script's output). check-drive-copy exit 0 (".saddlePeak,
  .skyline and .santaMonicaMountains each at DriveBasemap.swift(1) DriveCopy.swift(4) DriveSelector.swift(1)");
  --prove-red "8/8 mutations refused by name" including the new row `the card reads the THIRD case hard-coded
  (T-0236)`. check-map-attribution exit 0 (every MapView( and styleURL: at ScenicHomeScreen.swift(1) outside the one
  definition); --prove-red "14/14 mutations refused by name". check-safety-disclaimer exit 0 (SkylineHandoff.open( once, GatedHandoffButton.swift line 87, guard at
  82 - counts unchanged). check-mutate-population exit 0 ("91 modules, 35 covered by 14 populations, 34 allowlisted,
  1 added by this branch ... the floor of 34 holds").
  IOS-COMPILE dispatch 1 of 3: run 36195286205 on 0eb5a0f2d083bec7ab19d34095c761601473338a - success. The resource
  line: `CpResource .../ScenicDrive.app/saddle-peak.geojson .../apps/ios/ScenicDrive/Routes/saddle-peak.geojson`,
  then `** BUILD SUCCEEDED **`. The buildable folder FLATTENS Routes/ into the bundle root, so
  `MapRoute.bundled`'s second lookup (`name.ext` at the root) is the one that finds it on this Xcode - the first
  (`subdirectory/name.ext`) is kept for a build that keeps the folder, as BasemapResolver does for the archive.
  IOS-SCREENSHOT dispatch 1 of 3: run 36196721558 on 0eb5a0f, in progress.
- 2026-09-25T22:37:10Z SCREENSHOTS (agent/claude-opus-5). ios-screenshot dispatch 1 of 3: run 36196721558 on
  0eb5a0f2d083bec7ab19d34095c761601473338a - success (iPhone simulator, 1206 x 2622 px at 3x). Artifact
  `ios-screenshots` downloaded into the MAIN checkout's gitignored .artifacts/screens/ and renamed home-light-T0236.png
  (sha256 d079e0931ce463d9b661e9a7b63d0af1d8e69fef640630fc6007a0c8e23d6f12) and home-dark-T0236.png (f485655c09860dd5
  95fa1005efc2bdb188e26cdd60a21ae0d23100f7351ddc1b); PR #127's home-light.png / home-dark.png stay beside them. Not
  committed. Read by eye and measured with PIL (a gitignored .build/ script; numbers in pt = px / 3):
  CHIP ROW: "Saddle Peak" filled in the accent (selected, first), then "Westwood loop", then "SF Peninsula" - the
  R1 order and words. TITLE "Saddle Peak · Topanga to Malibu over the mountains" over two lines; then the R5 road
  list, "About 10 miles as the crow flies, pin to pin. The roads are longer.", the timing sentence ("A slow mountain
  afternoon, not a shortcut - the coast road is the quick way. Apple Maps gives you the real time when it opens."),
  and the caption "Preview build: three fixed drives, Saddle Peak selected. The line is the route the engine chose
  over Saddle Peak instead of PCH; the map under it shows no roads yet." - the demo-tiles arm, which is TRUE here:
  CI has no LA archive, so the ground is the MapLibre demo's Natural Earth land and sea.
  THE LINE: drawn, in both. Light: 39,623 px of exactly (37, 99, 235) = #2563EB, the light `route` token, on a white
  (`surface`) casing. Dark: 39,625 px of exactly (59, 130, 246) = #3B82F6, the dark `route` token, on a dark casing -
  the colour follows the trait collection, it is not one blue for both. It runs as the fixture does: it starts at the
  top-RIGHT (Topanga village, the north-east corner of the bbox), drops south down the canyon, winds WEST along the
  Saddle Peak / Schueren / Piuma ridge in visible switchbacks, reaches the left edge at Malibu Canyon Road, descends
  SOUTH and ends turning EAST (Civic Center Way) just above the demo coastline - the Natural Earth coast is coarse at
  this zoom, so the sea edge is not the real beach; nothing was drawn between pins in a straight line.
  THE CAMERA frames the whole route: the map's top edge is at 456 pt (the header text ends above it), the map is 418
  pt tall; the line spans x 69-332 pt and y 507-640 pt - 69 / 70 pt clear of the left / right edges (centred), 50
  pt below the map's top (the 48 pt top inset plus the casing), 234 pt above the screen's bottom = the 200 pt bottom
  inset plus MapLibre's own 34 pt safe-area content inset. It is a HEIGHT-limited fit (133 pt of line in the 170 pt
  left between the insets would not grow wider than 263 of the 354 pt available). Nothing of the line is under the
  conditions chip (it starts ~694 pt, 54 pt below the line's lowest pixel), the button or the credit pill.
  THE (i): at the map's top-left, 10-31 pt from its left edge and 10-31 pt below its top (8 pt margins + the button's
  own inset), clear of the header, the line and every other control, in both screenshots. The credit pill ("© MapLibre
  · Natural Earth", the demo credit - TRUE, P-ATTR-01) sits alone at the bottom-right; the corner under it, where PR
  #127's screenshots had the (i) covered, now holds only sea and the pill (top colours (216, 242, 255) and the pill's
  white / dark fill - no (i) blue). The MapLibre logo stays at the bottom-left. The (i) was moved, never hidden.
  Pre-existing and not this task's: the dark screenshot's GROUND is still the light demo style (the demo tiles have
  one style; the LA archive has both) - the header, chips, pill and line are dark-mode.
- 2026-09-25T22:50:39Z ACCEPTANCE, re-run whole and bare at the final pre-review head (agent/claude-opus-5), after
  `git fetch origin && git merge --no-edit origin/main` ("Already up to date": origin/main 006c798 has not moved since
  the claim). HEAD a71fd570c26275ab8ee9307d413e41c452d45c5f.
  - `git merge-base --is-ancestor origin/main HEAD` exit 0.
  - `swift test --scratch-path .build/T0236` (whole suite) exit 0: "Test run with 334 tests in 46 suites passed"
    (HandoffTests alone: "104 tests in 15 suites passed").
  - `bash ops/lib/check-map-attribution` exit 0; `--prove-red` exit 0, "prove-red: 14/14 mutations refused by name".
  - `bash ops/lib/check-drive-copy` exit 0, "the drive cases .saddlePeak, .skyline and .santaMonicaMountains each at
    DriveBasemap.swift(1) DriveCopy.swift(4) DriveSelector.swift(1) and nowhere else"; `--prove-red` exit 0,
    "prove-red: 8/8 mutations refused by name".
  - `bash ops/lib/check-safety-disclaimer` exit 0, "SkylineHandoff.open( called once" (GatedHandoffButton.swift line
    87, guard at 82) - P-SAFE-03's counts unchanged.
  - `python ops/lib/check-mutate-population.py` exit 0, "91 modules, 35 covered by 14 populations, 34 allowlisted, 1
    added by this branch" / "every added module is covered or allowlisted; the floor of 34 holds".
  - `python ops/lib/make-route-geojson.py` twice: "1393 points -> 483 points at Douglas-Peucker tolerance 5 m", sha256
    c945cbe8da3c3a96f77ea08b7eda93a931bc680af21bd966fbad2237553051db both runs, tree unchanged after.
  - `bash ops/lib/check-line-cap` exit 0, "117 Swift files tracked (Sources=44, Tests=49, apps/ios=24), none over 300
    lines"; `bash ops/lib/check-exec-bits` exit 0, "96 files, 23 required present, all modes correct";
    `bash ops/queue-check` exit 0, "QUEUE OK (229 tasks)".
  - `wc -l`, every file the branch touches: HandoffDrive.swift 207, SaddlePeakRoute.swift 61,
    StraightLineDistance.swift 102, HandoffSourceTests.swift 270, SaddlePeakGeometryTests.swift 146,
    SaddlePeakRouteTests.swift 85, SantaMonicaMountainsChainTests.swift 191, StraightLineDistanceTests.swift 237,
    DriveBasemap.swift 44, DriveCopy.swift 107, DriveRoute.swift 30, DriveSelector.swift 70, ScenicHomeScreen.swift
    288, MapRoute.swift 67, MapRouteCoordinator.swift 129, MapView.swift 84, saddle-peak.geojson 493,
    check-drive-copy 295, make-route-geojson.py 161, mutate-population-allowlist.json 39, straightline_mutations.py
    198, this file 182 before this entry.
  - macOS runs: ios-compile 36195286205 and ios-screenshot 36196721558, both success on 0eb5a0f. Every commit since
    touches no file the app compiles except two doc-comment lines in HandoffDrive.swift (6c69ad7); ios-compile is
    dispatched once more on the pushed head and its run id is quoted in the PR body, since a Log entry naming it would
    itself move the head.
  - `git status --short` empty.
  STILL OPEN, recorded not hidden: the loop's freeway middle leg (T-0211) is untouched; the dark screenshot's ground
  is the one-style demo map on CI; the line has not been seen over the LA archive (no archive on CI) - on a phone
  with the archive the caption's LA arm says "over Los Angeles roads".
- 2026-09-25T23:37:21Z ROUND 1 FAIL RULED, before any code (agent/claude-opus-5). rv1-t0236 B1 (BLOCKING): the Saddle
  Peak line is GraphHopper over OpenStreetMap (the fixture's details carry osm_way_id), and the only credit on the
  surface was the basemap's, so on every device without la.pmtiles - every CI run - the pill said "© MapLibre ·
  Natural Earth" over OpenStreetMap-derived geometry. ACCEPTED in full. Round 1's screenshot entry called that pill
  "TRUE, P-ATTR-01"; it was true of the tiles and false of the surface - P-ATTR-01 covers the basemap credit only, and
  I read its green as the surface's.
  (F1) THE CREDIT TRAVELS WITH THE GEOMETRY, as MapStyle's travels with its URL. `SaddlePeakRoute.geometryCredit` =
  "© OpenStreetMap contributors"; `HandoffDrive.routeGeometryCredit: String?` forwards it beside
  `routeGeometryResource` (nil for the loop and the Peninsula, which draw nothing). `MapRoute.dataCredit: String`
  (MapAdapter) is NON-optional and a required init argument, so no MapRoute exists without its credit, and
  `DriveRoute.resolve` draws no line for a drive that names a resource and no credit. Declared in Sources/Handoff and
  passed in, not declared under apps/ios: P-ATTR-01 (b)'s second population refuses any `static let` under apps/ios
  whose value names OpenStreetMap other than the one approved declaration - the same shape as the token colours.
  (F2) ONE COMPOSED VALUE, ONE FUNCTION. `CreditLine.composed(basemap:routeData:)` (new, Sources/Handoff, Foundation
  only): nil route data returns the basemap credit unchanged; otherwise the route credit's " · " segments are
  appended after the basemap's, each skipped when the basemap already carries it (compared ignoring a leading © and
  whitespace), and a fully duplicated route credit returns the basemap credit unchanged. Demo tiles + Saddle Peak ->
  "© MapLibre · Natural Earth · © OpenStreetMap contributors"; LA tiles + Saddle Peak -> "© OpenStreetMap contributors
  · Protomaps", OpenStreetMap once. The screen's ONE `AttributionFooter(` is handed
  `CreditLine.composed(basemap: style.attributionText, routeData: route?.dataCredit)` - the `style` the map is mounted
  with and the `route` MapView( is handed. No wrapper in FeatureScenicHome: the function the screen calls is the
  function the Linux test calls. AttributionFooter has no lineLimit (it wraps, never truncates), so the longer demo
  line wraps rather than losing a term.
  (F3) THE (i) SHEET. MLNShapeSource's options (clustering, zoom range, simplification tolerance, wrap/clip, line
  metrics) carry no attribution key; `attributionHTMLString` / `attributionInfos` belong to MLNTileSource, and a
  GeoJSON shape source is not a tile source. The line's credit cannot reach MapLibre's (i) sheet, so the footer is the
  credit of record on every map surface. Stated from MapLibre's public API - this box has no Apple SDK to read the
  header, and the screenshot's pill is what decides the surface.
  (F4) THE GATE. check-map-attribution limb (d) becomes a WHITELIST of ONE form: the footer's text argument,
  whitespace-squashed, is exactly `text: CreditLine.composed(basemap: <b>.attributionText, routeData: <r>?.dataCredit)`,
  with <b> mounted as `styleURL: <b>.url` (unchanged) and the one MapView( construction's argument list carrying
  `route: <r>` with the SAME <r>; any other form is refused by name. New --prove-red rows: the footer back to
  `style.attributionText`; the composed call handed `routeData: nil`; MapView( handed `route: nil` while the footer
  credits `route`. Rows whose sed anchored on `AttributionFooter(text: style.attributionText)` are re-anchored on the
  new argument. The composer's BODY is Swift under Sources/Handoff, outside the check's app tree: a composer that
  drops the route inside `CreditLine.composed` is shown red by swift test (CreditLineTests), not by the source check.
  pins/PINS.yaml is NOT in this task's touches, so P-ATTR-01's statement ("The basemap credit on the home screen ...")
  is left for the orchestrator to widen to the drawn route's data credit; its assertion (`bash
  ops/lib/check-map-attribution`) already runs the new limb.
  (F5) THE TEST. Tests/HandoffTests/CreditLineTests.swift binds to the shipping symbols - `CreditLine.composed` and
  `HandoffDrive.routeGeometryCredit` over `HandoffDrive.allCases` - and READS the two style credits from MapStyle.swift's
  approved declarations by identifier (`static let demoAttribution = `, `static let protomapsAttribution = `), so it
  cannot hold a stale copy. It asserts: Saddle Peak on the demo credit contains OpenStreetMap; on the LA credit it
  names OpenStreetMap exactly once and equals the LA credit; a drive with no route equals each style credit unchanged;
  a drive has a credit iff it names a geometry resource, and every credit names OpenStreetMap contributors.
  (F6) R5, copy-only, taken in the same commit. The road list began "Entrada Road and Topanga Canyon Boulevard out of
  the village" - true of the DRAWN line (its first point is on Entrada Road, way 13388359) and false of the HANDOFF
  (`source: nil`: Apple Maps starts wherever the driver is and routes to pin 1 on Fernwood Pacific Drive). The card
  shows the same sentence when the handoff fails, so it has to be true of the handoff: "From wherever you are to
  Fernwood Pacific Drive, then Tuna Canyon Road, Saddle Peak Road, Schueren Road, Piuma Road, down Malibu Canyon Road
  to Civic Center Way." Digit-free; check-drive-copy reads case sites, not this text.
- 2026-09-26T00:01:49Z ROUND 2 BUILT, red then green (agent/claude-opus-5). F1-F6 as ruled. Files: Sources/Handoff/
  CreditLine.swift (new), SaddlePeakRoute.swift (`geometryCredit`), HandoffDrive.swift (`routeGeometryCredit`),
  MapAdapter/MapRoute.swift (`dataCredit`, required), FeatureScenicHome/DriveRoute.swift, ScenicHomeScreen.swift (the
  footer), DriveCopy.swift (R5), ops/lib/check-map-attribution, -lib, -mutations, ops/lib/mutate-population-allowlist.json
  (CreditLine allowlisted with a reason: string composition, no number, no threshold), Tests/HandoffTests/
  CreditLineTests.swift (new), HandoffSourceTests.swift (its type allow-list).
  RED. (1) HandoffSourceTests' allow-list went red by name on the new source before anything was added to it: `every
  capitalised identifier in the shipping source is on the allow-list` on "CreditLine" and on "Set" ("108 tests in 16
  suites failed ... with 2 issues"); both added, the argument beside them. (2) Three mutants of the SHIPPING symbols,
  each run with `swift test --scratch-path .build/T0236 --filter CreditLine` and restored byte-for-byte (a gitignored
  .build/ driver): the composer returning `basemap` (drops the route credit) - exit 1, "4 tests in 1 suite failed ...
  with 3 issues", red `over the demo tiles the Saddle Peak pill names OpenStreetMap after the basemap's own credit`;
  the composer inserting the route's party raw instead of by identity (repeats a party the basemap names) - exit 1, 2
  issues, red `over the LA Protomaps tiles the Saddle Peak pill names OpenStreetMap exactly once`; `routeGeometryCredit`
  for .saddlePeak -> nil - exit 1, 4 issues, red `a drive has a data credit exactly when it draws a line, and that
  credit names OpenStreetMap` and the demo-tiles test. (3) check-map-attribution --prove-red, the three new rows: `the
  footer back to the style's credit alone` (round 1's own footer), `the composed credit handed no route credit` and
  `the map not handed the route the footer credits` - each exit 1, each naming its reason ("is not the composed
  credit" twice, "the map is not handed the route the credit names").
  GREEN. `swift test --scratch-path .build/T0236 --filter HandoffTests`: "Test run with 108 tests in 16 suites passed".
  check-map-attribution exit 0 ("built with: text: CreditLine.composed(basemap: style.attributionText, routeData:
  route?.dataCredit) - and the map with styleURL: style.url and route: route, the same bindings"); --prove-red "17/17
  mutations refused by name". check-drive-copy exit 0; --prove-red "8/8 mutations refused by name".
  check-mutate-population "every added module is covered or allowlisted; the floor of 34 holds". check-exec-bits "96
  files, 23 required present, all modes correct". Line cap and wc -l re-measured at the final pre-review head.
- 2026-09-26T00:23:55Z ROUND 2 macOS RUNS, first pair (agent/claude-opus-5). Pushed b3bd63889cea90aa874ba5397672ef0be1a231f8.
  ios-compile dispatch 1 of 2: run 36203482867 on b3bd638 - success. ios-screenshot dispatch 1 of 2: run 36204050341
  on b3bd638 - success; downloaded into the MAIN checkout's gitignored .artifacts/screens/ as home-light-T0236-r2a.png
  (sha256 034937447279d633fd2e763aa4322cb006a1d3485e7e1e05dee30f5a4f77b18e) / home-dark-T0236-r2a.png (10f535030ddf8edb
  33631402641082dd977da2037e743c671cf8817d0c906f77), 1206 x 2622 px each. Not committed. READ: the pill says, exactly,
  "© MapLibre · Natural Earth · © OpenStreetMap contributors" in both - B1's credit is on the surface. The line, its
  casing, the camera fit and the (i) at the map's top-left are as round 1 described; the road list reads "From
  wherever you are to Fernwood Pacific Drive, then Tuna Canyon Road, ..." (R5). NEW DEFECT, found here and not left:
  the longer credit made the pill FULL WIDTH on one line, and its left end sits on MapLibre's logo (bottom-left, the
  logo's outline visible through the 0.85 surface at 9-94 pt from the left edge) - the same class of defect round 1
  fixed for the (i). RULED: the lower-left corner is the renderer's; `AttributionFooter`'s leading spacer gets a
  104 pt minimum (the logo's measured right edge 94 pt + 10), so the pill wraps onto a second line instead of
  covering the logo - it has no lineLimit, so nothing is truncated. DesignSystem is in touches; no check anchors on
  the spacer. Second dispatch of each workflow on the fixed head follows; that pair is named -r2.
- 2026-09-26T00:44:51Z ROUND 2 SCREENSHOTS AND ACCEPTANCE, final pre-review head (agent/claude-opus-5). ios-compile
  dispatch 2 of 2: run 36204762256 on 6fc18e05f402b759c01973e97948a7581e8c7537 - success. ios-screenshot dispatch 2 of
  2: run 36205326414 on the SAME head - success; home-light-T0236-r2.png (sha256 c91d2c71d8444241ae053cf2be644d92454a38
  f9ecaa17eabd4b63c1e3f5829d) / home-dark-T0236-r2.png (77be9ed1695add26d005670df3f40ecfac554704c1e9e822e5dce0cdbd664ea3)
  in the MAIN checkout's .artifacts/screens/, 1206 x 2622 px, not committed. READ with PIL and by eye: the pill says,
  exactly, "© MapLibre · Natural Earth · © OpenStreetMap contributors", wrapped onto two trailing-aligned lines
  ("© MapLibre · Natural Earth · ©" / "OpenStreetMap contributors") at the bottom-right, its left edge ~181 pt from the
  map's left, clear of the MapLibre logo (fully visible, bottom-left, right edge ~94 pt) - both themes. THE LINE is
  unchanged from round 1: 39,623 px of exactly #2563EB (light) and 39,625 px of #3B82F6 (dark), the same counts, the
  same Topanga -> Saddle Peak -> Piuma -> Malibu Canyon shape and camera fit. THE (i) is at the map's top-left, as in
  round 1. Road list "From wherever you are to Fernwood Pacific Drive, then ..." (R5).
  ACCEPTANCE, bare, after `git fetch origin && git merge --no-edit origin/main` (main had moved to 5d1e260, queue files
  only; merge cabf8ce): `git merge-base --is-ancestor origin/main HEAD` exit 0; `swift test --scratch-path .build/T0236`
  "Test run with 338 tests in 47 suites passed"; `--filter HandoffTests` "108 tests in 16 suites passed";
  check-map-attribution exit 0, --prove-red "17/17 mutations refused by name"; check-drive-copy exit 0, --prove-red
  "8/8 mutations refused by name"; check-safety-disclaimer exit 0; check-line-cap "119 Swift files tracked
  (Sources=45, Tests=50, apps/ios=24), none over 300 lines"; check-exec-bits "96 files, 23 required present, all modes
  correct"; check-mutate-population "every added module is covered or allowlisted; the floor of 34 holds"; queue-check
  "QUEUE OK (234 tasks)". wc -l: CreditLine.swift 60, HandoffDrive.swift 218, SaddlePeakRoute.swift 66,
  CreditLineTests.swift 73, HandoffSourceTests.swift 274, MapRoute.swift 73, DriveRoute.swift 32, ScenicHomeScreen.swift
  288, DriveCopy.swift 107, AttributionFooter.swift 73, check-map-attribution 274, check-map-attribution-lib 300 (303
  when first measured here - trimmed by three comment lines before this entry), check-map-attribution-mutations 127.
  STILL OPEN: P-ATTR-01's statement in pins/PINS.yaml (outside touches:) still says "the basemap credit" - the
  orchestrator widens it to the drawn route's data credit; the wrap breaks between "©" and "OpenStreetMap" (cosmetic,
  the text is whole); T-0211, the dark demo ground and the line over the LA archive as round 1 recorded them.
