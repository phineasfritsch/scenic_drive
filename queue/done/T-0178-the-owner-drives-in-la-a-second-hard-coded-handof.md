---
id: T-0178
title: the owner drives in LA - a second hard-coded handoff drive (Sunset / PCH / Topanga / Mulholland) selectable on the home screen, pins Nominatim-verified like Skyline's
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T07:47:40Z
lease_expires_at: 2026-09-19T13:47:40Z
worktree: .worktrees/T-0178
branch: task/T-0178
exclusive: []
touches: [Sources/Handoff/, Tests/HandoffTests/, apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, apps/ios/Packages/ScenicApp/Sources/DesignSystem/, ops/lib/mutate-population-allowlist.json]
pins_affected: []
reviewer: agent/rv1-pr115
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
- 2026-09-19T11:34:00Z REVIEW PASS of PR #115 by agent/rv1-pr115 (not the owner), on a detached
  worktree at fb2f2b839eca84d09043ed2ffb6fb4e42d62af7b == origin/task/T-0178.

  SCOPE. `git diff --stat main...fb2f2b8` -> 15 files, 1359 insertions, 65 deletions: Sources/Handoff
  (HandoffDrive 71, SantaMonicaMountainsRoute 182, StraightLineDistance), Tests/HandoffTests (the two
  new suites + HandoffSourceTests), FeatureScenicHome (DriveBasemap 42 new, DriveCopy 81, DriveFacts,
  DriveSelector 68, GatedHandoffButton, HandoffFailureCard, ScenicHomeScreen 281, SkylineHandoff) and
  the task file. SkylineRoute.swift and its tests UNTOUCHED, MapAdapter UNTOUCHED, no serial file.
  Every `wc -l` in the 10:25:36Z acceptance block re-measured by the reviewer and equal.

  RE-DERIVED, not read. Three of the ten literals reverse-geocoded again by the reviewer
  (nominatim.openstreetmap.org/reverse?format=jsonv2&zoom=17, own descriptive User-Agent, 1.2 s apart):
  pin 4 -> way 675540508 "Pacific Coast Highway" highway/trunk, 34.0401096/-118.5792999; pin 5 ->
  way 667514947 "North Topanga Canyon Boulevard" highway/primary, 34.0931194/-118.6018208; pin 8 ->
  way 1533792498 "Mulholland Drive" highway/secondary, 34.1320831/-118.4532098. Way id, name, class
  and returned point match each literal's comment exactly. A reviewer's own haversine over the ten
  literals: 47445.1 m = 47.45 km, so "~47 km" and the shown 47 hold; leg 4->6 = 9733.0 m, the exact
  figure pin 5's comment quotes. All nine pins and the destination are inside
  services/etl/regions/la/region.json's bbox (min_lon -119.0, min_lat 33.7, max_lon -117.85,
  max_lat 34.45), computed by the reviewer from that file.

  BARE COMMANDS. `swift test --scratch-path .build/rv1-pr115 --filter HandoffTests` -> "Test run with
  71 tests in 10 suites passed after 0.072 seconds." `bash ops/lib/check-safety-disclaimer` -> exit 0,
  SkylineHandoff.open( called once (GatedHandoffButton.swift line 87) dominated by the guard at line
  82, GatedHandoffButton( constructed once, isSafetyDisclaimerAcknowledged written once at line 138 -
  every anchor count unchanged; the only moved numbers are inventories (9 files under FeatureScenicHome,
  21 under apps/ios). `bash ops/lib/check-line-cap` -> "P-SRC-02: 90 Swift files tracked (Sources=29,
  Tests=40, apps/ios=21), none over 300 lines". `bash ops/queue-check` -> "QUEUE OK (201 tasks)".
  `gh run view 35436962939` -> conclusion success, headSha 76a0444c7af1270b9158d7a61962d77203a44ed6,
  and `git diff --name-only 76a0444..fb2f2b8 -- "*.swift"` is EMPTY, so the compiled sha is this head's
  Swift.

  THREE REVIEWER MUTANTS on the Linux side, each restored with `git checkout --` and `git status
  --short` empty after: (1) `HandoffDrive.santaMonicaMountains` mapped to SkylineRoute's destination
  and waypoints -> KILLED, "each drive maps to its own route, and the default is the LA drive" failed
  with 3 issues; (2) pin 5 moved ~1.5 km south off CA-27 onto the Topanga village streets -> KILLED by
  six tests, including "nine pins still build a handoff URL" and "the whole-kilometre figure is the
  number the LA drive shows"; (3) `defaultDrive` flipped to `.skyline` -> KILLED by the same mapping
  test. The mapping test binds the accessors the app actually reads - `SkylineHandoff.destination(for:)`
  and `waypoints(for:)` forward straight to them and `directions(for:)` builds the URL from them - not
  a table against itself.

  READ-ONLY UI, at file:line. One door: `SkylineHandoff.open(` occurs once in the app, at
  GatedHandoffButton.swift:87, and takes the drive as a value - no sibling entry point. No location
  read: `grep -rn CoreLocation apps/ios Sources` hits only comments plus the pre-existing MapAdapter
  boundary (MapView.swift:1, on main before this branch); nothing new reads a position, and
  HandoffDrive.defaultDrive:50 is unconditional. Picker: DriveSelector.swift:34-35 carries
  home.drive.la and home.drive.skyline, :52 is `minHeight: 44` with the label inside the frame, and
  :50/:55/:59 are DesignTokens only. R6: DriveBasemap.swift:34-40 switches the STYLE over the drive
  (losAngeles for LA, demo for Skyline); ScenicHomeScreen.swift:126 gives AttributionFooter
  `style.attributionText` and :215 gives the caption the same resolved `style`, and DriveCopy.swift:72
  switches over MapStyle, so a false credit and a blank map under the Protomaps credit are both
  unreachable - the credit travels inside the MapStyle (MapStyle.swift:97). The resolve is NOT in a
  property initialiser: `style` is @State seeded with the demo case (ScenicHomeScreen.swift:50) and
  `resolveBasemap()` runs only from .task/.onChange (:133-135).

  NOT BLOCKING, recorded: the owner's (a)-(g) stand, in particular (f)/(g) - nothing in this tree can
  execute DriveBasemap.resolve and no device has rendered the Protomaps caption; and the two DriveCopy
  road lines are human-written text that no test ties to the pins.

  NOT DONE by this review: ops/test, the full ops/check-pins and any iOS render.

### 2026-09-19T11:29:47Z — owner/fixer: P-PROC-06 refuses this branch at merge; RULING before any edit

PR #115 was signed off by agent/rv1-pr115 and then REFUSED at merge: CI's core job is red on P-PROC-06,
the population gate that landed on main in PR #114 (T-0186) AFTER this branch was cut. Merged
`origin/main` into `task/T-0178` (clean, no conflict; pre-merge head f8a7586, merge commit head below),
then ran the gate bare:

    $ python ops/lib/check-mutate-population.py
    P-PROC-06: 73 modules, 22 covered by 10 populations, 25 allowlisted, 2 added by this branch
    ...
    P-PROC-06: module(s) added by this branch with no mutation population:
      Sources/Handoff/HandoffDrive.swift
      Sources/Handoff/SantaMonicaMountainsRoute.swift
      CLAUDE.md, Verification: a new numeric module ships its mutation population under ops/mutate/
      with a literal floor.
      Either add a driver to ops/mutate that names it in SUBJECT_MODULES, or - if it computes no
      number reaching score, route or tags - add it to ops/lib/mutate-population-allowlist.json with
      the reason.

The refusal is correct and is about this branch's two new files. Ruled module by module, by READING each,
against CLAUDE.md's "a new NUMERIC module ships its mutation population":

**Sources/Handoff/SantaMonicaMountainsRoute.swift — ALLOWLIST, not a population.** The whole file is
`public static let destination` and `public static let waypoints: [Coordinate]`: nine `Coordinate(...)`
literals and one more, each reverse-geocoded and quoted beside itself. There is no operator in the file.
It computes nothing; it is a typed table of literals whose correctness is provenance (the Nominatim
reverse result quoted per pin) and whose ordering property is held by `SantaMonicaMountainsRouteTests`,
which types all nine out again. A mutation population over it would be a population over `git diff` —
every mutant is "change a literal", every mutant is killed by the test that re-types the same literal,
and the floor would measure the transcription, not a computation.

**How main classifies `SkylineRoute.swift`, the module this one is the twin of.** It is NOT allowlisted
and NOT covered: the gate prints it under `DEBT (informational, never red): 26 existing module(s) with
no population and no allowlist entry`, beside `StraightLineDistance.swift`, `Geo.swift`, `score.py` and
the rest. So main has not *ruled* SkylineRoute either way — it is pre-existing debt the gate reports and
never fails on. SantaMonicaMountainsRoute is the same KIND of module (same shape, same discipline, its
doc comment says so), but it cannot ride on that: DEBT is a grandfather clause keyed on "existed before
this branch", and a module added by this branch must be ruled explicitly. This entry is that ruling, and
it is the honest one for both files — SkylineRoute's debt line is, on this reading, an allowlist entry
nobody has written; writing it is not this task's to do, because CLAUDE.md forbids touching
SkylineRoute.swift here and the gate does not ask.

**Sources/Handoff/HandoffDrive.swift — ALLOWLIST, not a population.** A two-case `String` enum plus
`defaultDrive`, and three members that are pure `switch self` forwards to the two route types
(`destination`, `waypoints`) and one concatenation (`chain = waypoints + [destination]`). No arithmetic:
it selects an array, it does not compute a number. The one property worth breaking is the MAPPING — case
to route — and that is already bound by a named test on the shipping symbols the app reads
(`SantaMonicaMountainsChainTests.eachDriveMapsToItsOwnRoute`, plus `defaultDrive` and the case count);
the reviewer's mutant (1) above cross-mapped it and it went KILLED. A mutate driver would re-buy that
same kill through a slower door.

**Sources/Handoff/StraightLineDistance.swift is the numeric part of this chain, and it is NOT mine to
write here.** It is the haversine that turns a `chain` into the whole-kilometre figure the LA drive
shows on screen — a number that reaches the screen, so it does get a population. It is pre-existing
(gate DEBT, not added by this branch, so the gate stays green without it) and it belongs to the filed
task T-0199. No population for it is written on this branch.

So: no `ops/mutate/handoff.py` change. Its `SUBJECT_MODULES` stays
`("Sources/Handoff/AppleMapsDirections.swift", "Sources/Handoff/HandoffError.swift")` — the two modules
in `Sources/Handoff` that do compute (a URL's encoding and cap, and the error mapping) — and its floors
(`MIN_MUTATIONS = 30`, `MIN_EQUIVALENT = 1`, `MIN_TEST_FILES = 3`) are untouched. Extending it with two
literal-table modules would inflate a population with mutants that are diffs, which is exactly the
"equivalent mutant ruled in prose" failure CLAUDE.md names. Widening `touches:` by
`ops/lib/mutate-population-allowlist.json` only; `ops/mutate/` is NOT edited.

RE-RUN AFTER THE TWO ALLOWLIST ENTRIES, every command bare, same session:

    $ python ops/lib/check-mutate-population.py
    P-PROC-06: 73 modules, 22 covered by 10 populations, 27 allowlisted, 2 added by this branch
      DEBT (informational, never red): 24 existing module(s) with no population and no allowlist entry
    P-PROC-06: every added module is covered or allowlisted; the floor of 22 holds
    (exit 0; allowlisted 25 -> 27, DEBT 26 -> 24, the floor of 22 populations-covered UNCHANGED - no
     module moved out of a population)

    $ swift test --scratch-path .build/T0178 --filter HandoffTests
    Test run with 71 tests in 10 suites passed after 0.093 seconds.
    (including "The Santa Monica Mountains chain, the region and the number" and "The Skyline route's
     pins")

    $ bash ops/lib/check-safety-disclaimer
    P-SAFE-03: 9 Swift file(s) under .../FeatureScenicHome; ... over the 21 .swift file(s) under
    apps/ios, SkylineHandoff.open( called once (GatedHandoffButton.swift line 87), dominated by the
    guard at line 82; ... `isSafetyDisclaimerAcknowledged = true` written exactly once, at line 138
    (exit 0; every count identical to the sign-off run - 9, 21, line 87, line 82, line 138)

    $ bash ops/lib/check-line-cap
    P-SRC-02: 90 Swift files tracked (Sources=29, Tests=40, apps/ios=21), none over 300 lines
    $ bash ops/lib/check-exec-bits
    P-OPS-01: 76 files, 23 required present, all modes correct
    $ bash ops/queue-check
    QUEUE OK (205 tasks)
    (205, up from 201: main's four new backlog tasks arrived in the merge)

`ops/mutate/handoff.py` was NOT edited, so `python ops/mutate/handoff.py` is not re-run here; its last
run stands in the entries above and its floors are untouched.

NO SWIFT UNDER apps/ios CHANGED, by measurement: `git diff --name-only f8a7586..HEAD --
"apps/ios/**/*.swift"` over the whole range from the pre-merge head through the merge to this head is
EMPTY - the merge brought no apps/ios Swift and I wrote none - so the ios-compile proof quoted at
sign-off (run 35436962939, headSha 76a0444) still describes this head's Apple-side Swift byte for byte.
This fix touches two files: `ops/lib/mutate-population-allowlist.json` and this task file. The task
stays in `queue/done/`, `state: done` and `reviewer: agent/rv1-pr115` untouched; the `touches:` header
is widened by the allowlist path only.

### 2026-09-19T11:46:30Z — agent/rv2-pr115: narrow re-review of the post-sign-off fix — PASS

Scope: ONLY what changed since agent/rv1-pr115's sign-off commit `f8a7586`, minus the merge of main.
`git log --oneline origin/task/T-0178` gives `f8a7586` (sign-off) -> `4e23910` (merge of origin/main)
-> `0dcb0d9` (the fix). So the reviewed change is `git diff 4e23910..0dcb0d9`:

    $ git diff 4e23910..0dcb0d9 --raw
    :100644 100644 dc90524 419864e M  ops/lib/mutate-population-allowlist.json
    :100644 100644 6bbdb76 4899360 M  queue/done/T-0178-the-owner-drives-in-la-a-second-hard-coded-handof.md

Two files, two lines of JSON and one Log entry plus a widened `touches:` header. No source, no test, no
`ops/mutate/` driver and no gate script changed; both modes stay 100644. Review worktree
`.worktrees/rv2-pr115`, detached at 0dcb0d9.

**The gate, bare.**

    $ python ops/lib/check-mutate-population.py
    P-PROC-06: 73 modules, 22 covered by 10 populations, 27 allowlisted, 2 added by this branch
      DEBT (informational, never red): 24 existing module(s) with no population and no allowlist entry
      ... Sources/Handoff/SkylineRoute.swift, Sources/Handoff/StraightLineDistance.swift, ...
    P-PROC-06: every added module is covered or allowlisted; the floor of 22 holds
    exit=0

Identical to the numbers the fixer quotes; the floor of 22 populations-covered is unchanged, so no
module was moved out of a population to buy this green.

**The gate proved RED against this branch's own file (mutant, on the review worktree).** Deleted the
`Sources/Handoff/HandoffDrive.swift` line from `ops/lib/mutate-population-allowlist.json` and re-ran:

    P-PROC-06: module(s) added by this branch with no mutation population:
      Sources/Handoff/HandoffDrive.swift
      Either add a driver to ops/mutate that names it in SUBJECT_MODULES, or - if it computes no
      number reaching score, route or tags - add it to ops/lib/mutate-population-allowlist.json ...

KILLED. `git checkout -- ops/lib/mutate-population-allowlist.json`; `git status --short` empty. So the
green above is bound to these two entries and is not a green the checker would print regardless.

**The numeric-or-not ruling, judged by opening both files, not by reading the reason.**

- `Sources/Handoff/SantaMonicaMountainsRoute.swift` (182 lines) — CONFIRMED a table. The only
  executable content is `public static let destination = Coordinate(...)` and
  `public static let waypoints: [Coordinate] = [ ... ]` with nine `Coordinate(latitude:longitude:)`
  literals. There is no arithmetic operator, no comparison, no function body in the file; everything
  else is doc comment and the per-pin reverse-geocode provenance. Ten literals, which is what the
  allowlist reason says. A population here would mutate literals that
  `SantaMonicaMountainsRouteTests` re-types; the reason is accurate and the ALLOWLIST ruling is right.
- `Sources/Handoff/HandoffDrive.swift` — CONFIRMED non-numeric. Two cases, `defaultDrive`, two
  `switch self` forwards (`destination`, `waypoints`) that return the route types' own statics, and
  `chain = waypoints + [destination]`, an array concatenation. Nothing in the file computes a number.
  Its one breakable property is the case->route mapping, and that is bound on the SHIPPING symbols,
  not on a helper or on the table itself:

    $ grep -n ... Tests/HandoffTests/SantaMonicaMountainsChainTests.swift
    150: #expect(HandoffDrive.skyline.waypoints == SkylineRoute.waypoints)
    152: #expect(HandoffDrive.santaMonicaMountains.waypoints == SantaMonicaMountainsRoute.waypoints)
    154: #expect(HandoffDrive.santaMonicaMountains.chain == StraightLineDistance.santaMonicaMountainsRoutePoints)
    160: #expect(HandoffDrive.defaultDrive == .santaMonicaMountains, ...)
    161: #expect(HandoffDrive.allCases.count == 2, ...)

  in `func eachDriveMapsToItsOwnRoute()`. A cross-mapped enum fails there.

Neither file computes a number that reaches a score, a route or a tag, so neither is a module CLAUDE.md
asks for a population from. NOT BLOCKING. No population was written or extended on this commit, so
there was no population to run bare.

**Nothing regressed.**

    $ swift test --scratch-path .build/rv2-pr115 --filter HandoffTests
    Test run with 71 tests in 10 suites passed after 0.113 seconds.
    (including "The Santa Monica Mountains chain, the region and the number", "The Santa Monica
     Mountains route's pins", "The Skyline route's ridge leg", "Handoff shipping source")

    $ bash ops/lib/check-safety-disclaimer
    P-SAFE-03: 9 Swift file(s) under .../FeatureScenicHome; over the 21 .swift file(s) under apps/ios,
    SkylineHandoff.open( called once (GatedHandoffButton.swift line 87), dominated by the guard at
    line 82; ... `isSafetyDisclaimerAcknowledged = true` written exactly once, at line 138
    exit=0
    (9, 21, 87, 82, 138 - every count identical to the sign-off run and to the fixer's re-run)

    $ bash ops/queue-check
    QUEUE OK (208 tasks)
    (208, not the fixer's 205: three more backlog tasks landed on main since; queue-check is run
     against the main checkout, which is ahead of this branch)

    $ gh pr checks 115
    core             pass  2m1s
    pins-source-only pass  1m4s

**Recordable, not blocking (the fixer raised both and I agree with both).** (1)
`Sources/Handoff/SkylineRoute.swift` is the twin of the file ruled here and sits in the gate's DEBT
list with no allowlist entry; writing it is forbidden by this task's Brief and the gate does not ask,
so it should be filed as its own task. (2) `Sources/Handoff/StraightLineDistance.swift` is the
haversine whose whole-kilometre figure reaches the screen and it has no population; the fixer points
at task T-0199 for it, which I did not open.

NOT DONE by this re-review: `ops/test`, the full `ops/check-pins`, any iOS render, any re-check of the
work rv1-pr115 already signed off (the nine pins' provenance, the URL shape, the screen), and I did not
verify that task T-0199 exists or that it names StraightLineDistance.

VERDICT: PASS. The task stays in `queue/done/`; `reviewer:` stays `agent/rv1-pr115`. Not merged by me.
