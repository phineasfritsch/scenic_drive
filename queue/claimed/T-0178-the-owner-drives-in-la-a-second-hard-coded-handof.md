---
id: T-0178
title: the owner drives in LA - a second hard-coded handoff drive (Sunset / PCH / Topanga / Mulholland) selectable on the home screen, pins Nominatim-verified like Skyline's
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T07:47:40Z
lease_expires_at: 2026-09-19T13:47:40Z
worktree: .worktrees/T-0178
branch: task/T-0178
exclusive: []
touches: [Sources/Handoff/, Tests/HandoffTests/, apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, apps/ios/Packages/ScenicApp/Sources/DesignSystem/]
pins_affected: []
reviewer: null
depends_on: [T-0153, T-0170]
verify: [ops/test, ops/check-pins]
acceptance:
  - "Sources/Handoff/ gains a second route type (one type per file, e.g. SantaMonicaMountainsRoute) with at most nine pins, every coordinate reverse-geocoded by Nominatim before it is written (way id + road name quoted beside the literal, one request per second, a descriptive User-Agent), destination and pins inside regions/la's bbox; a Linux test types out the pin count, the leg order and the maximum consecutive spacing per leg, RED by name when a pin is removed"
  - "the home screen offers BOTH drives (a two-row picker or segmented control, DesignTokens only, identifiers home.drive.skyline / home.drive.la, 44 pt), the title and road line follow the selected drive, the LA drive is the default when the device locale region or the last-known coarse position is Southern California - rule it, and say what happens with Location denied (the plan's 5.1.1(iv) case)"
  - "ios-compile dispatch on the branch green with the run id quoted; bash ops/lib/check-line-cap, bash ops/queue-check, bash ops/lib/check-safety-disclaimer bare at the final commit"
---
## Brief

The owner lives and commutes in Los Angeles. The plan's success criterion is "the developer drives a route this
app made" (plan:22), and every human gate is a drive; the M1.5 skeleton's only drive is the Bay Area Skyline
loop (T-0151), which the owner can check on a desk in Apple Maps or Google Maps but cannot drive. The LA region
exists on main (`services/etl/regions/la/region.json`, T-0107, PR #68, UCLA-centred bbox; T-0142 notes the
bbox's Orange County sliver).

Build the LA counterpart of T-0151 with T-0151's discipline: a loop the owner would take on a weekday evening
with 25 spare minutes - the 405 or the 10 as the freeway baseline, the scenic middle on Sunset Boulevard west,
PCH north, Topanga Canyon Boulevard up, Mulholland Drive east, back down (Sepulveda or the 405) - decision-point
pins only, the CA-27/Topanga and Mulholland junctions pinned so Apple Maps cannot shortcut through the canyon
residential grid (the rat-run the plan forbids), and the same ridge-leg spacing bound. Rule in the Log, before
code: which roads (with the Nominatim way ids), the order property that is actually true for this loop, why
each junction pin exists, and the school-zone cut-throughs the pins must exclude (Topanga's residential
streets; the Mulholland side streets). Do NOT touch SkylineRoute.swift or its tests; do not add the route line
(M4).

## Log
- 2026-09-19T00:49:41Z filed by agent/claude-fable-5-1 from the owner's instruction ("I am in LA"); depends on T-0153 because both edit ScenicHomeScreen.swift. Not started.
- 2026-09-19T06:29:45Z depends_on += T-0170 by agent/claude-fable-5-1 (00:13 panel, grounded): #110 also edits apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ScenicHomeScreen.swift (10 lines, git diff --stat origin/main...origin/task/T-0170), the file this task touches; starting after #101 but before #110 merges conflicts on it. Both LA drivers on the 00:13 panel stopped on the same two strings - 'Skyline loop - ends back in San Francisco' and the I-280/Canada/CA-92/Skyline road line - 'it is not my drive'; this task is the only queued item that puts a drive the owner can start on the screen. NEXT START the moment #101 and #110 are both merged.
- 2026-09-19T07:47:40Z claimed by agent/claude-opus-5; lease until 2026-09-19T13:47:40Z
- 2026-09-19T08:14:31Z RULINGS by agent/claude-opus-5, before any code. The query scripts are in
  `.artifacts/T-0178/` (gitignored); every result that decided something is quoted here or beside the literal
  it produced.

  R0 THE BRIEF AGAINST REALITY - MULHOLLAND IS NOT CONTINUOUS FROM TOPANGA. The Brief's shape is "Topanga
  Canyon Boulevard up; Mulholland Drive east; back down (Sepulveda or the 405)". That sequence is not
  drivable. Two Overpass shared-node joins found NO node common to a way named `~"Topanga Canyon Boulevard$"`
  and any Mulholland-named way: bbox (34.095,-118.615,34.125,-118.590) against `~"Mulholland (Drive|Highway)$"`
  and bbox (34.118,-118.612,34.142,-118.585) against `~"Mulholland"` - 0 shared nodes both times, while the
  same query shape returned the PCH/Topanga node (122761988) and the Sunset/PCH node (6031887097) in the same
  session, so the join works and the answer is real. The Mulholland-named ways nearest the crest span
  (34.13731,-118.64177) to (34.12905,-118.51389): the crest-to-Encino stretch, which is the unpaved "Dirt
  Mulholland". NOT VERIFIED HERE, and therefore not claimed: the `surface` tags themselves - `out tags;` over
  that name gateway-timed out (HTTP 504) on two bboxes. What is verified is the missing shared node, and that
  is what the pins are chosen against. The loop therefore takes Mulholland Drive on its PAVED eastern section
  (way 1533792498, `highway=secondary`, reverse-verified below) and reaches it the way a car can: north on
  CA-27 to Ventura Boulevard, the freeway baseline east and south, off the 405 at Mulholland.
  CARRIED, not hidden: this is a ~47 km straight-line / ~70 km road loop, not a 25-minute detour off a
  commute. The Brief's "25 spare minutes" is not true of the Brief's own road list. No screen in this task
  states a duration (T-0152's rule, `ScenicHomeScreen` has none), so nothing claims otherwise. STILL OPEN.

  R1 THE LOOP, in driving order - nine pins, every one a decision point, against `maxWaypoints` of 9 and the
  plan's "<=9 pinned waypoints at decision points". West on Sunset, north up the coast, up the canyon, over
  the crest to the Valley, the freeway baseline back over the Sepulveda Pass, east along the paved ridge and
  down Beverly Glen into Westwood:
    1 way 399990528  West Sunset Boulevard, Brentwood        34.05820,-118.47930
    2 way 522193485  West Sunset Boulevard, Pacific Palisades 34.04739,-118.52581
    3 way 675941117  West Sunset Boulevard at PCH             34.03857,-118.55562
    4 way 675540508  Pacific Coast Highway at Topanga (CA-27) 34.04011,-118.57930
    5 way 667514947  North Topanga Canyon Boulevard, village  34.09312,-118.60182
    6 way 38311861   Topanga Canyon Boulevard, the crest      34.12587,-118.60045
    7 way 401296501  Topanga Canyon Boulevard, Woodland Hills 34.16801,-118.60576
    8 way 1533792498 Mulholland Drive, east of the 405        34.13208,-118.45321
    9 way 402237654  North Beverly Glen Boulevard             34.12922,-118.44168
    destination way 763033286 Westwood Boulevard, Westwood Village 34.06110,-118.44548
  WHY EACH JUNCTION PIN EXISTS, and WHAT IT EXCLUDES. Pins constrain by order: Apple Maps reads repeated
  `waypoint` parameters in array order, so any path that skips a pinned point is refused, and a cut-through
  that bypasses a pinned point cannot be taken without failing to reach it.
   - Pin 1 (Sunset east of the Palisades) excludes the freeway run that skips the whole scenic middle:
     405 south -> 10 west -> PCH north -> Chautauqua Boulevard up to Sunset, which reaches every later pin in
     order with Sunset Boulevard never driven. Pin 2 is west of the Chautauqua junction on Sunset, so the
     Chautauqua and San Vicente/Ocean Avenue cuts cannot serve as a shortcut between pins 1 and 2 either.
   - Pin 4 is the CA-27/PCH junction the Brief names, pinned on the PCH side (the approach that has to be
     driven), exactly as T-0151 pinned the Canada side of the CA-92 junction rather than the CA-92 side.
   - Pin 5 (the village) and pin 6 (the crest) are what keep the drive on the CA-27 carriageway through
     Topanga. THE SCHOOL-ZONE AND RESIDENTIAL CUT-THROUGHS THEY EXCLUDE, by name: Tuna Canyon Road (OSM way
     73156338, `highway=tertiary`, met at 34.04429,-118.58889 in this session's reverse scan) and Fernwood
     Pacific Drive, which leave CA-27 below the village and climb the residential grid; Entrada Road and
     Topanga School Road, the village streets past Topanga Elementary; and Old Topanga Canyon Road, which
     leaves CA-27 just north of the village and runs to Calabasas - a different way to the Valley entirely.
     None of them touches pin 5 or pin 6, both of which are reverse-verified points on the state highway, so
     no route through them reaches these pins.
   - Pin 6 is also the Mulholland junction the Brief asks to be pinned. R0 is why it is pinned on the CA-27
     side and why the drive continues north from it instead of turning east.
   - Pin 7 (CA-27 at Ventura Boulevard) is the turn onto the freeway baseline and the pin that forbids Dirt
     Mulholland as a shortcut between the crest and pin 8.
   - Pin 9 (North Beverly Glen Boulevard) is the descent, and choosing it excludes Roscomare Road - the other
     way down off Mulholland here, past Roscomare Road Elementary - and Benedict Canyon.

  R2 NOMINATIM. Every literal above is a REVERSE result, `format=jsonv2&zoom=17&extratags=1`, User-Agent
  `scenic-drive-T-0178 (github.com/phineasfritsch/scenic_drive; owner-contact via repo)`, one request per
  1.1-1.2 s, on 2026-09-19 from this worktree. The way id, the `name` field, the class and the point Nominatim
  returned are quoted beside each pin in `SantaMonicaMountainsRoute.swift`. Nominatim was reachable for every
  query; nothing here is typed unverified. Three candidate points were REFUSED because the reverse result
  named a side street and not the carriageway claimed - 34.07160,-118.47530 (Firth Avenue), 34.06800,-118.47600
  (North Bundy Drive) and the Sunset/Bundy junction node 123082348 at 34.06032,-118.47594 (South Bundy Drive) -
  which is why pin 1 sits mid-block on Sunset instead of on the Bundy junction. Overpass was used only to
  LOCATE geometry (junction nodes, the ways' extent); no forward or Overpass result became a pin. The
  direction of the query is the rule, from T-0151: a waypoint is a reverse result or it does not go in.

  R3 THE ORDER PROPERTY, ruled against the numbers rather than assumed. "Latitude monotone" is FALSE for this
  loop and "longitude monotone" is false too; what is true is one direction of travel per leg, and the legs
  are not the same axis:
    pins 1..4  west on Sunset, then north-west on PCH   longitude strictly decreasing (latitude is NOT
               monotone: it falls to 34.03857 at PCH and rises again to 34.04011 at the Topanga junction)
    pins 4..7  up the canyon to the Valley              latitude strictly increasing (longitude is NOT
               monotone: -118.57930, -118.60182, -118.60045, -118.60576)
    pins 7..9  the freeway baseline and the ridge       latitude strictly decreasing AND longitude strictly
               increasing (east); the last hop, pin 9 to Westwood, turns back west (-118.44168 ->
               -118.44548) while latitude keeps falling, so latitude is the invariant that runs to the end.
  SPACING, per leg, by the spherical law of cosines written out in the test file (deliberately not
  `ScenicKit.Geo`, so a wrong `Geo` and a wrong bound cannot agree): coast leg 4450.3 / 2916.5 / 2188.6 m,
  bound 6000 m, and without pin 2 the gap is 7362.5 m - over it. Canyon leg 6248.8 / 3643.8 / 4711.2 m, bound
  8000 m, and without pin 5 the gap is 9733.0 m - over it. The canyon bound is looser than the coast's for the
  reason T-0151's ridge bound is looser than its Canada bound: the climb from PCH to the village is 6.2 km of
  CA-27 with no junction in it to pin. The return leg is NOT bounded and must not be: pin 7 to pin 8 is
  14595.4 m of 101 and 405, the freeway baseline, and a bound there would be a number written to fit. What is
  asserted instead is the shape: EXACTLY ONE consecutive gap in the whole chain exceeds the canyon bound, and
  it is that one (next widest: 7582.7 m, pin 9 to the destination).
  THE STRAIGHT LINE. `StraightLineDistance` gains an LA chain - `santaMonicaMountainsRoutePoints` and
  `santaMonicaMountainsRouteWholeKilometers`, two additions beside the Skyline pair; the Skyline literal, its
  chain and `StraightLineDistanceTests` are not touched. Haversine over the nine pins plus the destination is
  47445.124 m -> 47 km floored. Cross-check that the arithmetic used to compute it is `Geo`'s: the same code
  gives 112268.093 m for the Skyline chain, which is the metre literal `StraightLineDistanceTests` already
  pins. BBOX: all ten points are inside `services/etl/regions/la/region.json` (-119.0,33.7,-117.85,34.45), and
  the Linux suite reads that file rather than only re-typing the numbers, so a bbox edit cannot silently leave
  a pin outside the region it claims.

  R4 THE PICKER, and the default. Two rows, not a segmented control: `Picker(.segmented)` renders with
  `UISegmentedControl`'s own colours, which are not `DesignTokens`, and the acceptance line says DesignTokens
  only. `DriveSelector` is two buttons, each `frame(maxWidth: .infinity, minHeight: 44)` with the label inside
  the frame (the 44 pt target holds at the smallest Dynamic Type setting), identifiers `home.drive.skyline` and
  `home.drive.la`, selected row filled `primary`/`onPrimary`, unselected `surface`/`fg` with a `border`
  hairline. Title, road line, distance line, map centre and the handoff URL all read the selection.
  THE DEFAULT IS THE LA DRIVE, UNCONDITIONALLY, and the condition in the acceptance line cannot be evaluated:
  (i) `Locale.current.region` is a COUNTRY - `US` - and there is no region identifier for Southern California,
  so the locale cannot distinguish Westwood from the Bay Area; (ii) a last-known coarse position requires
  CoreLocation authorization, and this app has never asked for one and must not - `AppleMapsDirections(source:
  nil, ...)` exists precisely so the handoff needs no location, CLAUDE.md bans CoreLocation from the Linux
  targets, and feature targets import DesignSystem, ScenicKit, PlaceStore and their own protocols only. So the
  plan's 5.1.1(iv) "nothing is known" case is the ONLY case, and `HandoffDrive.defaultDrive` is `.santaMonicaMountains`
  with the reasoning written where the value is. WHAT THE OWNER IN WESTWOOD SEES ON FIRST LAUNCH: the LA drive
  selected, its title, its roads and its 47 km, no permission prompt of any kind. WHAT THE FRIEND WITH LOCATION
  DENIED SEES: exactly the same screen, because nothing here reads a location to decide - a denial changes
  nothing, and the Skyline drive is one 44 pt tap away. The selection is `@State` and is not persisted; a
  device that is relaunched is back on the LA drive. STILL OPEN.

  R5 THE HANDOFF - ONE CALL SITE, TWO DRIVES. `SkylineHandoff.open(` stays the single occurrence in
  `GatedHandoffButton.swift` that `ops/lib/check-safety-disclaimer` (iv) counts; it gains a parameter rather
  than a sibling. `HandoffDrive` (Linux, in `Handoff`, so both drives' coordinates stay testable) is passed
  from the screen through `GatedHandoffButton`'s `drive` property into `SkylineHandoff.open(drive)`, behind the
  same `guard isSafetyDisclaimerAcknowledged else`. A second `SkylineHandoff.laOpen(` would have been a second
  door with one lock, which is the hole P-SAFE-03 exists to refuse. Every count the check makes is unchanged:
  `SkylineHandoff.open(` once in GatedHandoffButton.swift; `GatedHandoffButton(` once in ScenicHomeScreen.swift
  with `isSafetyDisclaimerAcknowledged: isSafetyDisclaimerAcknowledged` in its argument list and no `: true`;
  `isSafetyDisclaimerAcknowledged` at GatedHandoffButton.swift(2) and ScenicHomeScreen.swift(4); the key
  `safety.disclaimer.acknowledged.v1` at ScenicHomeScreen.swift(1). The new `DriveSelector.swift` and
  `DriveCopy.swift` mention none of them. The type keeps the name `SkylineHandoff` although it now hands over
  either drive: the check's anchors are that identifier and that file name, and `ops/` is outside this task's
  `touches:`. STILL OPEN.
- 2026-09-19T09:16:08Z BUILT by agent/claude-opus-5, against the rulings above. What landed, and how each
  ruling turned into a symbol.

  R2 RE-VERIFIED, not trusted. Every one of the ten literals was reverse-geocoded AGAIN in this session,
  one request per 1.1 s, `format=jsonv2&zoom=17&extratags=1`, same User-Agent, transcript in
  `.artifacts/T-0178/reverse-final.txt` (gitignored). All ten came back on the way, with the name, the
  class and the point now quoted beside each literal in `SantaMonicaMountainsRoute.swift`:
  399990528 / 522193485 / 675941117 West Sunset Boulevard (secondary); 675540508 Pacific Coast Highway
  (trunk); 667514947 North Topanga Canyon Boulevard and 38311861 / 401296501 Topanga Canyon Boulevard
  (primary); 1533792498 Mulholland Drive (secondary); 402237654 North Beverly Glen Boulevard
  (secondary); destination 763033286 Westwood Boulevard (secondary). Nominatim was reachable for all ten.

  R3 RE-MEASURED, and every number in the ruling reproduces exactly (`.artifacts/T-0178/verify.py`):
  gaps 4450.3 / 2916.5 / 2188.6 | 6248.8 / 3643.8 / 4711.2 | 14595.4 / 1107.9 / 7582.7 m; without pin 2
  7362.5 m; without pin 5 9733.0 m; exactly ONE gap over 8000 m and it is the 14595.4 m freeway
  baseline, next widest 7582.7 m; haversine chain 47445.124 m -> 47 km, and the SAME code gives
  112268.093 m for the Skyline chain, which is the metre literal `StraightLineDistanceTests` already
  pins. All ten points inside regions/la's bbox.

  THE CODE. `Sources/Handoff/SantaMonicaMountainsRoute.swift` (178) - nine pins + destination, the
  reverse result beside each, the excluded cut-throughs named where the pin that excludes them is.
  `Sources/Handoff/HandoffDrive.swift` (67) - the two-case selector, `defaultDrive`, and the R4 ruling
  written where the value is. `StraightLineDistance` (52 -> 78) gains `santaMonicaMountainsRoutePoints`,
  `santaMonicaMountainsRouteWholeKilometers` and `wholeKilometers(for:)`; the Skyline pair, its literal
  and `StraightLineDistanceTests` are untouched. UI: `DriveSelector.swift` (68, two 44 pt rows,
  DesignTokens only, `home.drive.la` / `home.drive.skyline`, `.isSelected` stated), `DriveCopy.swift`
  (66, the per-drive title / road line / short name / caption), `DriveFacts` takes the drive,
  `HandoffFailureCard` takes the drive so the pasted kilometres and the pasted roads are one drive's,
  `ScenicHomeScreen` holds `selectedDrive` and every line reads it. R5 held: `SkylineHandoff.open(` is
  still ONE occurrence and now takes a `HandoffDrive`; no second entry point exists.

  RED FIRST, BY NAME. The type was written before the suites in this session, so the red that is
  recorded is the one the acceptance line asks for - a pin removed. Deleting pin 5 (the village) from
  the shipped array: `swift test --scratch-path .build/T0178 --filter SantaMonicaMountains` ->
  "Test run with 20 tests in 2 suites failed after 0.011 seconds with 18 issues", naming
  "there are nine pins, and the number is pinned" (count 8 == 9),
  "no gap on the Topanga canyon leg is wider than the bound" (widest 9732.98 < 8000.0),
  "exactly one gap in the whole chain is over the canyon bound, and it is the freeway one" (over.count
  2 == 1), "the canyon leg is the slice this test thinks it is", "every pin is the coordinate the
  reverse geocode returned", "the chain is the shipped pins in driving order, then Westwood",
  "every pin and the destination are inside the LA region's bbox" (chain.count 9 == 10),
  "the whole-kilometre figure is the number the LA drive shows" (159.6 m off the pinned metres) and
  "the pins run the drive..." - then the pin restored and the whole bundle green again.
  A SECOND red, not asked for and worth recording: `HandoffSourceTests`' capitalised-identifier
  allow-list went red on BOTH new type names ("names the type HandoffDrive, which is not on the Handoff
  allow-list" / "... SantaMonicaMountainsRoute"), 8 issues, before either was argued onto the list.
  That is the list doing its job a third time, after T-0151's and T-0170's.

  WHAT THE BBOX TEST READS. `SantaMonicaMountainsChainTests` READS `services/etl/regions/la/region.json`
  through `#filePath` rather than re-typing the four numbers: a box moved in that file would otherwise
  leave nine pins outside the graph that is supposed to contain them, with a green suite. It fails
  rather than skips when the file is unreadable, and `theSkylineDriveIsOutsideTheLARegion` is the
  standing demonstration that the predicate can refuse a point - all eight Bay Area points are outside.

  STILL OPEN, carried forward: (a) R0's length - a ~47 km line / ~70 km loop is not the Brief's
  "25 spare minutes"; no screen states a duration, so nothing claims otherwise, but the Brief's own
  road list and its time budget disagree and the roads won. (b) Dirt Mulholland's `surface` tags are
  NOT verified (Overpass 504 twice); what is verified is the missing shared node, and pin 7 is what
  keeps the drive off it. (c) The selection is `@State` and not persisted; a relaunch is back on the LA
  drive. (d) No route line is drawn for either drive (M4), so the map still says nothing at the scale
  of a drive. (e) No XCUITest proves the picker is tappable or that a row's 44 pt target holds - this
  package has no test target and this tree has never been on a device; the compiler is the only proof
  the UI half has.
- 2026-09-19T09:33:00Z ACCEPTANCE BLOCK, re-run BARE at the final pre-review commit by agent/claude-opus-5,
  quoted whole (the author rule). The code commit is 7b06049; this entry adds no code, so the
  ios-compile proof below is for the tree the reviewer reads.

    swift test --scratch-path .build/T0178 --filter HandoffTests
      -> "Test run with 71 tests in 10 suites passed after 0.084 seconds." (was 55 before this task)
    gh run view 35434325610 --json status,conclusion,headSha
      -> {"conclusion":"success","headSha":"7b06049bac47692a22b4c1601964ab82f55a0f74","status":"completed"}
      -> gh run view 35434325610 --log: "** BUILD SUCCEEDED **" x1 (simulator-build, 09:19:09Z),
         ` error:` count 0. ONE dispatch, per the ENV rule; it was green first time.
    bash ops/lib/check-safety-disclaimer -> exit 0, every count unchanged:
      SkylineHandoff.open( once (GatedHandoffButton.swift line 87) dominated by the guard at line 82;
      GatedHandoffButton( once in ScenicHomeScreen.swift, the acknowledgement passed through, no `: true`;
      isSafetyDisclaimerAcknowledged at GatedHandoffButton.swift(2) ScenicHomeScreen.swift(4);
      the key safety.disclaimer.acknowledged.v1 at ScenicHomeScreen.swift(1)
    bash ops/lib/check-safety-disclaimer --prove-red -> "prove-red: 13/13 mutations refused by name"
    bash ops/lib/check-line-cap
      -> "P-SRC-02: 84 Swift files tracked (Sources=29, Tests=40, apps/ios=15), none over 300 lines"
    bash ops/queue-check -> "QUEUE OK (199 tasks)"
    bash ops/check-pins --source-only
      -> "PINS ok=13 skipped=14 pending=1 expired=0 failed=0 tier=linux source-only"

  wc -l, every touched Swift file: SantaMonicaMountainsRoute.swift 178, HandoffDrive.swift 67,
  StraightLineDistance.swift 78, SantaMonicaMountainsRouteTests.swift 265,
  SantaMonicaMountainsChainTests.swift 169, HandoffSourceTests.swift 201, DriveCopy.swift 66,
  DriveSelector.swift 68, DriveFacts.swift 65, GatedHandoffButton.swift 110, HandoffFailureCard.swift 133,
  ScenicHomeScreen.swift 250, SkylineHandoff.swift 90.
  state: claimed and reviewer: null are untouched - the owner never signs off its own task.
- 2026-09-19T09:55:04Z R6 (orchestrator, from the 02:13 panel), ruled BEFORE the code below. PR #112 put
  the LA Protomaps basemap on main (`MapAdapter.BasemapResolver.losAngeles()` returns a `MapStyle` whose
  `url` and `attributionText` travel together; with no `la.pmtiles` on the device it returns the demo case
  with the demo credit) and NOTHING mounts it: `ScenicHomeScreen` still read `MapStyle.maplibreDemoTiles`.
  THE MOUNT IS PER DRIVE. The LA drive resolves `BasemapResolver.losAngeles()`; the Skyline drive KEEPS the
  demo case, because the LA archive covers -119.0,33.7,-117.85,34.45 only and the Skyline map is centred on
  the Peninsula - a global mount would draw an empty map under the Protomaps credit. The map caption and the
  `AttributionFooter` follow the RESOLVED style, never the selection: when the resolver falls back to demo
  tiles the caption says the map does not show roads yet and the credit is MapLibre's.
  HOW THE RESOLVE IS KEPT OFF THE BODY'S HOT PATH, ruled: `BasemapResolver.losAngeles` is not a lookup - on
  the success path it MATERIALISES a style document into the caches directory and touches the bundle and the
  file system. SwiftUI re-runs `body` whenever anything it reads changes and may re-run a `View`'s property
  initialisers as it rebuilds the value, so neither is a call site. The resolved value is `@State` (`style`,
  initialised to the demo case) and `resolveBasemap()` runs from exactly three modifiers - `.task` (first
  appearance), `.onChange(of: selectedDrive)` and `.onChange(of: colorScheme)`. Those are the only three
  inputs the answer has: which drive, is the archive there, light or dark.
  THE CAPTION WORDS, ruled. The demo case keeps the existing sentence verbatim. The Protomaps case is
  "Preview build: two fixed drives, <name> selected. The map shows Los Angeles roads, but not this drive's
  line yet - tap below and it opens in Apple Maps." - it may claim roads, because those tiles have them, and
  it may not claim the drive, because no route line is drawn for either drive until M4.
- 2026-09-19T10:25:36Z R6 BUILT and the ACCEPTANCE BLOCK RE-RUN BARE AND QUOTED WHOLE by
  agent/claude-opus-5 (the author rule; a correction commit that touches a measured file re-measures it,
  so every `wc -l` below is re-measured and `check-line-cap`'s file counts moved with the new file).
  First `git fetch origin && git merge --no-edit origin/main` - #112 merged, no conflict, MapAdapter is
  not this task's to edit and was not edited (merge commit 37cbdb8). Code commit 76a0444.

  WHAT LANDED, in FeatureScenicHome only. `DriveBasemap.swift` (42, new) - `resolve(for:appearance:)`,
  `BasemapResolver.losAngeles(appearance:)` for `.santaMonicaMountains` and `.maplibreDemoTiles` for
  `.skyline`, with the bbox reason written where the switch is. `ScenicHomeScreen` - `style` is now
  `@State` seeded with the demo case plus `@Environment(\.colorScheme)`, `resolveBasemap()` called from
  `.task`, `.onChange(of: selectedDrive)` and `.onChange(of: colorScheme)`; `MapView(styleURL:)` and
  `AttributionFooter(text:)` read that one resolved value, as they already did, so the credit follows the
  tiles by construction. `DriveCopy.mapCaption(for:style:)` switches over the RESOLVED style: the demo
  sentence is unchanged, the Protomaps sentence is the R6 wording. DOC ITEMS: `HandoffDrive`'s note named
  `HandoffDriveTests`, a suite that has never existed - corrected to
  `SantaMonicaMountainsChainTests.eachDriveMapsToItsOwnRoute`; pin 7's comment in
  `SantaMonicaMountainsRoute` asserted an unpaved crest track as fact - it now records that those `surface`
  tags are STILL UNVERIFIED (Overpass 504 twice, not retried) and that the pin is chosen against the
  missing shared node, which is what the type note already said.

    swift test --scratch-path .build/T0178 --filter HandoffTests
      -> "Test run with 71 tests in 10 suites passed after 0.068 seconds." (unchanged; no Swift API changed
         in the Linux targets - both edits there are documentation)
    gh run view 35436962939 --json status,conclusion,headSha
      -> {"conclusion":"success","headSha":"76a0444c7af1270b9158d7a61962d77203a44ed6","status":"completed"}
      -> gh run view 35436962939 --log: "** BUILD SUCCEEDED **" x1, ` error:` count 0. ONE dispatch; green
         first time. This is the run for the code; the entry you are reading adds no code.
    bash ops/lib/check-safety-disclaimer -> exit 0, every anchor count unchanged:
      SkylineHandoff.open( once (GatedHandoffButton.swift line 87) dominated by the guard at line 82;
      GatedHandoffButton( once in ScenicHomeScreen.swift, the acknowledgement passed through, no `: true`;
      isSafetyDisclaimerAcknowledged at GatedHandoffButton.swift(2) ScenicHomeScreen.swift(4);
      the key safety.disclaimer.acknowledged.v1 at ScenicHomeScreen.swift(1);
      `@AppStorage(...)` now reported at line 59 (was 49) - the declaration moved down the file, the count
      did not. The ONE number in its report that did change is its inventory line, "9 Swift file(s) under
      .../FeatureScenicHome" (was 8): `DriveBasemap.swift` is the ninth. That is a count of files, not of
      anchors, and it moves whenever the feature gains a file.
    bash ops/lib/check-safety-disclaimer --prove-red -> "prove-red: 13/13 mutations refused by name"
    bash ops/lib/check-line-cap
      -> "P-SRC-02: 90 Swift files tracked (Sources=29, Tests=40, apps/ios=21), none over 300 lines"
         (84/15 before: +5 apps/ios from #112's MapAdapter files arriving in the merge, +1 DriveBasemap)
    bash ops/queue-check -> "QUEUE OK (201 tasks)"
    bash ops/check-pins --source-only
      -> "PINS ok=13 skipped=14 pending=1 expired=0 failed=0 tier=linux source-only"

  wc -l, RE-MEASURED, every touched Swift file: SantaMonicaMountainsRoute.swift 182 (was 178),
  HandoffDrive.swift 71 (was 67), StraightLineDistance.swift 78, SantaMonicaMountainsRouteTests.swift 265,
  SantaMonicaMountainsChainTests.swift 169, HandoffSourceTests.swift 201, DriveBasemap.swift 42 (new),
  DriveCopy.swift 81 (was 66), DriveSelector.swift 68, DriveFacts.swift 65, GatedHandoffButton.swift 110,
  HandoffFailureCard.swift 133, ScenicHomeScreen.swift 281 (was 250, cap 300 - the new views went in their
  own file for that reason), SkylineHandoff.swift 90.

  STILL OPEN, carried and added to: (a) the Brief's "25 spare minutes" against its own ~70 km road list;
  (b) Dirt Mulholland's `surface` tags unverified - now recorded where the pin is, not only here;
  (c) the selection is `@State` and is not persisted; (d) no route line for either drive (M4); (e) no
  XCUITest for the picker; (f) NEW - nothing in this tree can execute `DriveBasemap.resolve`: the ScenicApp
  package has no test target, so that the LA drive takes the Protomaps case on a device with the archive,
  and the Skyline drive never does, is proved by the compiler and by reading only. (g) NEW - no device has
  run this: `la.pmtiles` is 63 MB and gitignored, so every run anywhere - including run 35436962939 - takes
  the demo fallback, and the Protomaps caption has never been on a screen.
  state: claimed and reviewer: null are untouched - the owner never signs off its own task.
