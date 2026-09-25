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
