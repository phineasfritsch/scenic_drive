---
id: T-0321
title: NavAdapter - the app's only Ferrostar importer, pinned to an exact version, drives turn-by-turn on the planned scenic route through a custom RouteProvider and calls ScenicKit DriveSession for every decision (off-route, reroute with remaining waypoints + same lambda, offline rejoin, motion gate)
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-08T11:51:00Z
lease_expires_at: 2026-10-08T21:51:00Z
worktree: .worktrees/T-0321
branch: task/T-0321
exclusive: [package-swift, package-resolved]
touches: [apps/ios/Packages/ScenicApp/Package.swift, apps/ios/Packages/ScenicApp/Package.resolved, apps/ios/ScenicDrive.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved, queue/LOCKS/, queue/backlog/, apps/ios/Packages/ScenicApp/Sources/, apps/ios/Packages/ScenicApp/Tests/, apps/ios/ScenicDrive/, Sources/ScenicKit/, Tests/ScenicKitTests/, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-NAV-01, P-SAFE-09, P-ATTR-01]
reviewer: null
depends_on: [T-0317]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST in a dated Log entry: the Ferrostar release to pin (exact version, its Swift package URL and products, its license, its minimum iOS - must be <= 18.4), how its RouteProvider / custom route adapter accepts a pre-computed route (our GraphHopper polyline + instructions via ScenicKit Guidance), what its off-route and location hooks expose, and how they map onto ScenicKit DriveSession (T-0317) - every decision stays in DriveSession, NavAdapter is a thin shell; the CLAUDE.md rule that NavAdapter is the ONLY importer of Ferrostar"
  - "apps/ios/Packages/ScenicApp/Package.swift gains Ferrostar pinned with exact: and a NavAdapter target; Package.resolved committed; a source guard (whitelist of import sites, CLAUDE.md) refuses 'import Ferrostar' anywhere but NavAdapter, seen red then green"
  - "NavAdapter feeds every location fix and connectivity edge into DriveSession and acts only on its outputs; when the connection drops it cancels the in-flight reroute and drops a late reply/failure (rv2-t0317 recordable 4); offline -> rejoin banner, zero requests; the >4.5 m/s minimal surface is what the drive screen shows; attribution stays visible on the drive map (P-ATTR-01)"
  - "ios-compile + ios-screenshot pass on the branch (the drive screen in the screenshot set if ruled feasible on the simulator); digests re-approved; population entries for the adapter's own wiring (e.g. a fix not forwarded, the late reply not dropped) MISSED before and CAUGHT by name after, or EQUIVALENT with a witness where only device runs can observe them"
---
## Brief

Plan: Navigation on the scenic path (Ferrostar) + M7 + the Turn-by-turn decision row ("pinned to an exact version,
custom RouteProvider"). T-0317 put every decision into Linux-tested ScenicKit DriveSession; this task is the Apple
shell. The Worker reroute wire (/plan carrying remaining waypoints + lambda) is T-0319; until it lands, NavAdapter
rules what a reroute does online (e.g. hand off, or rejoin) and records it. TTS (spoken guidance + audio background
mode) and Live Activity are separate follow-ups; Live Activity needs the xcodeproj lock (held by T-0180).

## Log
- 2026-10-08T11:50:51Z filed by agent/claude-opus-5 (orchestrator) from the milestone gap map (M7 NavAdapter) and rv2-t0317's recordable 4.
- 2026-10-08T11:51:00Z claimed by agent/claude-opus-5; lease until 2026-10-08T21:51:00Z
- 2026-10-08T12:03:05Z MEASURED then RULED, before any code, by agent/claude-opus-5 (owner).
  MEASURED (gh api, stadiamaps/ferrostar): releases 0.57.0 (2026-09-22, newest), 0.56.0, 0.55.0; tag 0.57.0 is
  object 80c7ebd6. Its root Package.swift (swift-tools 5.9): package name FerrostarCore (identity ferrostar),
  `platforms: [.iOS(.v16)]` (16 <= 18.4), products FerrostarCore (targets FerrostarCore + FerrostarCoreFFI),
  FerrostarMapLibreUI, FerrostarSwiftUI, FerrostarCarPlayUI; binaryTarget ferrostarFFI from the release zip,
  checksum de0bdf78...56d1; dependencies swiftui-dsl from 0.25.0 (whose manifest takes
  maplibre-gl-native-distribution from 6.21.2 - our exact 6.31.0 satisfies it) and swift-snapshot-testing. License:
  LICENSE.txt at the tag; GitHub's detector says NOASSERTION (it is BSD-3-Clause text with Stadia's header; the
  owner's Legal & Attribution screen is T-0271's and gains the row with the drive screen, see R6).
  API at the tag: `RouteProvider.customProvider(CustomRouteProvider)`, whose one requirement is
  `getRoutes(userLocation:waypoints:) async throws -> [Route]`; `FerrostarCore(routeProvider:locationProvider:
  navigationControllerConfig:networkSession:)` sets `locationProvider.delegate = self`; `startNavigation(route:
  userLocation:config:)` takes a pre-built `Route(geometry:bbox:distance:waypoints:steps:)`, each
  `RouteStep(geometry:distance:duration:roadName:exits:instruction:visualInstructions:spokenInstructions:
  annotations:incidents:drivingSide:roundaboutExitNumber:)`; off-route is `SwiftRouteDeviationTracking` (.none |
  .staticThreshold | .custom) plus `FerrostarCoreDelegate.core(_:correctiveActionForDeviation:remainingWaypoints:)
  -> CorrectiveAction (.doNothing | .getNewRoutes)`; locations arrive as `UserLocation(coordinates:
  horizontalAccuracy:courseOverGround:timestamp:speed:)` through `LocationManagingDelegate.locationManager(_:
  didUpdateLocations:)`. Our plan: PlanPreview carries `route`, `waypoints`, `lambda` and NO instructions (the
  Worker's /plan returns none today).
  R1 PIN: Ferrostar 0.57.0, `exact:`, product FerrostarCore only (the MapLibre UI product would make a second
  MapLibre importer). NavAdapter imports FerrostarCore and FerrostarCoreFFI (the records live in the FFI module);
  CLAUDE.md's rule is enforced by a new whole-line WHITELIST guard, ops/lib/check-ferrostar-imports: every line of
  every .swift under apps/ios and Sources that imports a Ferrostar module is one of the typed approved lines, in
  NavAdapter, and NavAdapter is the only target whose manifest entry names the ferrostar package. Seen red first.
  R2 DECISIONS STAY IN SCENICKIT. Ferrostar's deviation tracking is `.none` and the delegate answers `.doNothing`:
  Ferrostar never decides off-route or reroutes. Every location fix is tapped before Ferrostar sees it
  (DriveLocationTap wraps CoreLocationProvider) and forwarded to a NEW ScenicKit DriveController, which wraps
  DriveSession and owns the recordable-4 obligation as pure, Linux-tested logic: each reroute is issued with a
  ticket; the online-to-offline edge with a ticket out emits `.cancel(ticket)`; a reply or failure whose ticket is
  not the one in flight is DROPPED (returns false, changes nothing). That is the only way a late reply from before
  the drop cannot answer the request after the reconnect. The adapter maps `.send` to a Task and `.cancel` to
  Task.cancel(), and hands replies back by ticket - no decision.
  R3 ONLINE REROUTE UNTIL T-0319: the wire does not carry pins or lambda, so the sender is ScenicKit's
  RerouteUnavailable, which fails immediately with no request: online off-route is rejoin mode, zero requests,
  exactly like offline. T-0319 swaps the sender; nothing else changes.
  R4 STEPS: with no instructions on the wire, the Ferrostar Route is built from a NEW pure ScenicKit split,
  DriveSession.legs: one leg per stretch between the pins' vertices, ending `.reachedWaypoint` (GuidanceMapping's
  `.reachedVia`) and the last `.arrive` (`.finish`). Turn-by-turn per junction needs GraphHopper instructions on
  /plan - the wire task's (T-0319) scope, recorded there by the orchestrator.
  R5 CUSTOM ROUTE PROVIDER: PlannedRouteProvider (CustomRouteProvider) returns the pre-built Route; it is what
  Ferrostar would call, and it never touches the network.
  R6 THE DRIVE SCREEN IS NOT IN THIS PR (ruled infeasible within this task's locks and budget, filed as T-0322): a
  drive map is a second `MapView(styleURL:` surface, which ops/lib/check-map-attribution's whitelist refuses by name
  until its rows, the shell's frozen block and the -pinned digests are raised with it; a launchable screen needs
  a door in the app shell and a `-screen drive` shot in ios-screenshot.yml, which T-0180 (holder of the xcodeproj
  lock, whose touches include .github/workflows/) is editing. So acceptance 3's "minimal surface is what the drive
  screen shows" and "attribution on the drive map", and acceptance 4's drive screenshot, move to T-0322; this PR
  exposes `surface` and `mode` on NavAdapter's DriveNavigator for it. ios-screenshot must still pass unchanged.
  R7 LINKING WITHOUT project.pbxproj: NavAdapter rides the FeatureScenicHome product (as Entitlements and
  PlanAdapter do), so the app links and ios-compile compiles it; the shell does not import it yet (T-0322 does).
  R8 Package.resolved: the acceptance's apps/ios/Packages/ScenicApp/Package.resolved does not exist - the app's
  resolution lives at apps/ios/ScenicDrive.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved,
  a serial-only file of its own (T-0167's `package-resolved` lock, free now), not project.pbxproj. touches gains
  that path and exclusive gains package-resolved. It is never hand-written (originHash is SwiftPM's): a throwaway
  probe/T-0321 branch dispatches ios-compile.yml with -disableAutomaticPackageResolution removed and its existing
  upload step returns the file Xcode wrote (T-0257's method); the probe branch is deleted after.
  R9 LANGUAGE MODE: NavAdapter compiles in Swift 5 mode - Ferrostar 0.57.0's records and core carry no Sendable
  annotations, and the shell is a thin bridge; every decision it forwards to is Swift 6 ScenicKit.
  R10 POPULATION: ops/mutate/drive.py gains DriveController.swift, DriveCommand.swift and the legs split as
  subjects, with mutants MISSED before the new tests and CAUGHT by name after. The adapter's own lines (a fix not
  forwarded, a ticket not handed back) are compiled only on macOS CI and run only on a device: EQUIVALENT entries
  with that witness, not claimed caught.
  R11 DIGESTS: every new or changed Sources/ and apps/ios file is re-approved in
  ops/lib/check-safety-disclaimer-linked-digests.txt.
- 2026-10-08T12:25:40Z RED FIRST then GREEN (Linux, swift 6.3.3 native, --scratch-path .build/t321). Stubs first
  (DriveController without the ticket checks or the cancel; DriveLeg.split returning []): `--filter
  "DriveControllerTests|DriveLegTests"` -> "Test run with 10 tests in 2 suites failed after 0.020 seconds with 20
  issues", red BY NAME: lostEdgeCancels (2 issues), lateReplyDropped (4), lateFailureDropped (3),
  answerWithNothingInFlight (2), innerPinsCut (3), endPinsCutNothing (5), rerouteLegs (1); green on the stub:
  everyFixReachesTheSession, senderUntilWireFails, legLength (their subjects already had their final form; the
  population's mutants bind them). After the implementation, the five drive suites: "Test run with 33 tests in 5
  suites passed". named-tests.json P-NAV-01 gains both suites (filter and all 10 names).
  P-NAV-02 GUARD (ops/lib/check-ferrostar-imports.py, 100755): RED before NavAdapter existed (both approved lines
  0 times; "holds no `import FerrostarCore` line"), exit 1. Red arms over scratch copies of the tree, each exit 1
  naming the line: `import FerrostarCore` appended to FeatureScenicHome/DriveRoute.swift; `@preconcurrency import
  FerrostarCoreFFI` in Sources/ScenicKit/Drive/DriveLeg.swift; `import struct FerrostarCore.Route` in
  MapAdapter/MapView.swift; `import` + newline + `FerrostarCore` in PlanAdapter/LivePlanner.swift (refused on the
  `FerrostarCore` line); the product line moved into the MapAdapter target ("a dependency of name: \"MapAdapter\",");
  NavAdapter deleted. Baseline copy and the worktree: exit 0, "2 line(s) naming Ferrostar outside .../NavAdapter/,
  each one of the 2 approved whole lines, once; ... NavAdapter imports FerrostarCore (5 line(s))".
  Digests: six NavAdapter rows and the manifest's new sha in -pinned; seven Sources rows in -linked-digests;
  -doors gains the NavAdapter target map rows and the product's new targets list. Bare guards: check-safety-disclaimer
  0, check-map-attribution 0, check-store-links.py 0. PINS.yaml gains P-NAV-02; check-pins-yaml "ok pins=47".
- 2026-10-08T12:39:20Z R8 AMENDED by the owner before the first CI run: the pins are SwiftPM's own, not typed - `swift package resolve`
  on apps/ios/Packages/ScenicApp (swift 6.3.3 native, --scratch-path .build/t321app) resolved ferrostar 0.57.0
  (4e2d7f64), swiftui-dsl 0.25.0 (139e83d1), swift-syntax 602.0.0 (47992865), maplibre 6.31.0 (13e41ab3, unchanged); those
  pin objects are merged verbatim into the Xcode workspace file beside its GRDB pin, Xcode's originHash 3bd20783...0cfe
  kept (T-0257 measured it unmoved when a dependency was added; SwiftPM's own originHash is the manifest's sha256,
  a different hash). ios-compile runs with -disableAutomaticPackageResolution, so a wrong file fails the build; the
  probe method is the fallback. The package-local Package.resolved SwiftPM wrote is NOT committed: Xcode ignores a
  local package's file, and two would disagree.
