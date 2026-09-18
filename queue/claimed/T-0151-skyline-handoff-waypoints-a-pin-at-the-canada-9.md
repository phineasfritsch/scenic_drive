---
id: T-0151
title: SkylineHandoff waypoints - a pin at the Cañada/92 junction, a mid-Cañada pin, pin 5 moved onto CA-35, and a maximum-spacing test so Apple Maps cannot shortcut back onto 280
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-18T20:32:52Z
lease_expires_at: 2026-09-19T04:32:52Z
worktree: .worktrees/T-0151
branch: task/T-0151
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, apps/ios/Packages/ScenicApp/Tests/, Sources/Handoff/, Tests/HandoffTests/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/check-pins]
acceptance:
  - "swift test --scratch-path .build/T0151 --filter SkylineRouteTests -> 8 tests: the helper against one degree of latitude and against a zero-distance NaN; seven pins; the seven literals; the Cañada leg slice; the per-leg order; the spacing bound; the bound needs the mid pin; the handoff URL. Ends `Test run with 8 tests in 1 suite passed`, exit 0"
  - "swift test --scratch-path .build/T0151 -> `Test run with 258 tests in 33 suites passed`, exit 0 (the whole root package, including HandoffSourceTests whose allow-list this change had to be argued onto)"
  - "RED, by name: the same --filter run with the mid-Cañada pin deleted from SkylineRoute.waypoints -> `Test no gap on the 280 -> Cañada -> 92 leg is wider than the bound recorded an issue at SkylineRouteTests.swift:192:9: Expectation failed: (widest -> 9681.899324888309) < (Self.canadaLegMaxSpacingMeters -> 6000.0)` and `Test run with 8 tests in 1 suite failed after 0.005 seconds with 6 issues`. The pin was put back; no part of the demonstration is in the commit"
  - "gh workflow run ios-compile.yml --ref task/T-0151 -> run 35394012179, conclusion success, ONE dispatch, first try. gh run view 35394012179 --log contains `simulator-build build for the iOS Simulator 2026-09-18T20:56:21.0158350Z ** BUILD SUCCEEDED **`, and above it `Compiling SkylineRoute.swift` (target Handoff) and `Compiling SkylineHandoff.swift ... (in target FeatureScenicHome from project ScenicApp)`, so both changed Swift files were compiled and not merely present"
  - "wc -l on the four touched Swift files -> 150 Sources/Handoff/SkylineRoute.swift, 226 Tests/HandoffTests/SkylineRouteTests.swift, 184 Tests/HandoffTests/HandoffSourceTests.swift, 78 apps/ios/.../SkylineHandoff.swift; all under CLAUDE.md's 300-line cap, one type per file, filename == type name"
  - "gh pr checks 96 -> `pins-source-only pass 51s` and `core pass 2m20s` (both jobs of actions run 35394456751), exit 0. Read on the PR rather than run locally, as the task text instructs; ops/check-pins and ops/test are what those two jobs run"
  - "NOT RUN, on the record: `bash ops/check-pins` and `bash ops/test` were not run locally - the task text forbids it on this box (the default swift scratch path does not build in a worktree here), and `gh pr checks` is what reads them instead. No pin in pins/PINS.yaml is touched or added by this change (pins_affected: []), so nothing here is enforced by check-pins; the spacing bound is enforced by a test in the suite ops/test runs"
  - "NOT RUN, on the record: nothing here has been on a device or in a simulator at runtime. ios-compile COMPILES for the iOS Simulator and runs no test; no Apple test target exists to run (apps/ios/Packages/ScenicApp/Package.swift says why). Nobody has driven this route. Whether Apple Maps in fact refuses the Edgewood Road shortcut given these seven pins is NOT demonstrated by anything in this PR - the test measures pin spacing, which is the proxy this repository can check"
---
## Brief

Found by DRIVER ONE on the 2026-09-18 panels (02:45 and 10:13), grounded by the fable pass against Nominatim
reverse geocoding and the file's own comments. `SkylineHandoff.swift` (on task/T-0141, PR #88) pins the
280 -> Cañada -> 92 -> Skyline shape with five waypoints:

- pins 1-4 lie on the roads their comments name (verified: ways 23995546, 305925415, 27672021, 276909112);
- the CA-92 pin (:64) is WEST of the Cañada/92 junction - the file says so itself (:43-44) - so nothing is
  pinned AT the junction, and from the Cañada pin (:58, its south end) to the 92 pin is ~11 km with no pin:
  Apple Maps is free to take Edgewood Rd back to 280 and rejoin 92 at the interchange, which is the exact
  rat-run-shaped shortcut the product exists to avoid;
- pin 5 (:77, the Sky Londa CDP centroid) reverse-geocodes to La Honda Road (CA-84), way 32506261, 1.7 km
  from the CA-35/84 junction its comment names; the handoff's last pin is off the road it claims.

**Do:** add a pin at the Cañada/92 junction and a mid-Cañada pin between Edgewood Rd and CA-92; move pin 5
onto CA-35 south of Sky Londa; keep the total at or under the plan's nine (plan: "<=9 pinned waypoints at
decision points"). Every coordinate verified by Nominatim reverse geocoding BEFORE it is written, the way
and its name quoted in the comment - a comment naming a road the pin is not on is the defect this repository
exists to catch. Add a test (in the Apple package's test target when it exists, or as a Linux-runnable check
over the literal array if the coordinates are moved into ScenicKit) asserting the maximum great-circle
spacing between consecutive pins on the 280 -> Cañada -> 92 leg is under a stated bound, demonstrated red by
removing the mid-Cañada pin. Note Bicycle Sunday (Cañada Rd closed to cars Sunday mornings, spring-autumn)
in the comment - it is why a Sunday-morning tester will see Apple Maps route around it.

Depends on T-0141 (PR #88) landing; do not open a second PR on the same file while round 2 is under review.

## Log
- 2026-09-18T17:55:00Z filed by agent/claude-fable-5-1 from the 10:13 panel (Driver One, grounded; the "pins 4 and 5 are off the ridge" claim was WRONG for pin 4 and right for pin 5). Not started.
- 2026-09-18T20:32:52Z claimed by agent/claude-opus-5; lease until 2026-09-19T04:32:52Z
- 2026-09-18T20:53:03Z **Rulings - agent/claude-opus-5, owner and author.** Written where the plan, the
  Brief, the existing code and the map disagree or are silent. Rulings 1, 4 and 6 were settled from the
  Nominatim queries below before any literal was written; rulings 2, 3 and 5 were settled while the test
  was written (20:46Z-20:50Z) and are recorded here rather than back-dated.

  1. **Where the literals live: `Sources/Handoff/SkylineRoute.swift`, not the feature target.** The Brief
     offers two homes - "in the Apple package's test target when it exists, or as a Linux-runnable check
     over the literal array if the coordinates are moved into ScenicKit". The Apple test target does not
     exist, and its own manifest says why: `apps/ios/Packages/ScenicApp/Package.swift` ends "NO TEST
     TARGETS HERE, deliberately and temporarily ... a test target added now would be a suite nobody has
     ever seen go red". So the first branch cannot produce a check. Ruled: the second, with `Handoff`
     rather than `ScenicKit` as the target - the root manifest's own comment on the `Handoff` target
     forbids the arrow back into ScenicKit ("ScenicKit ... has no business knowing that a URL to a
     third-party maps app exists"), and a pinned waypoint list for a maps app is handoff data.
     `FeatureScenicHome` already depends on the `Handoff` product, so `SkylineHandoff` re-exports
     `SkylineRoute.destination` and `.waypoints` and `ScenicHomeScreen` needs no edit. **Neither
     `Package.swift` is touched**: both are serial-only under CLAUDE.md and a new file inside an existing
     `path:`-declared target needs no manifest change. `touches:` extended with `Sources/Handoff/` and
     `Tests/HandoffTests/` for this move.
  2. **The Brief's suggested order property is false; here is the one that is true.** "latitude
     non-increasing from the I-280 pin onward" does not hold and never did: Cañada Road is driven
     NORTHBOUND from Woodside up to CA-92, so latitude rises across the middle of the array. Ruled, and
     asserted per leg in `orderIsTheDrive`: pins 0..1 southbound I-280, latitude strictly decreasing;
     pins 1..4 northbound Cañada then west on CA-92, latitude strictly increasing AND longitude strictly
     decreasing; pins 4..6 southbound CA-35, latitude strictly decreasing.
  3. **The spacing bound covers the Cañada leg, not the 280 run.** Pin 1 (Daly City) to pin 2 (Woodside)
     is the freeway shoulder; a bound wide enough to hold it would be wide enough to hold the rat-run it
     is supposed to exclude. Ruled: the bound governs the contiguous run from the Woodside pin to the
     Half Moon Bay Road pin. The test locates that run by its two typed-out END POINTS
     (`canadaLegAsShipped`), not by an index pair - with `1...4` hard-coded, deleting a pin slides the
     window onto the ridge and the red run reports a gap on a leg nobody asked about.
  4. **The junction pin goes on the Cañada side of the junction.** Ruling 3 of the task text says "a pin
     AT the Canada Rd / CA-92 junction". Both sides were reverse-geocoded. The CA-92 side
     (37.50707, -122.34210 -> way 417323967, "Half Moon Bay Road") sits 80-odd metres from the CA-92 pin
     this list already has, spending a decision-point slot on a pin next to another pin. The Cañada side
     (37.50621, -122.34073 -> way 417324930, "Cañada Road") is that way's own north-west bounding-box
     corner to five decimals, i.e. where Cañada Road ends at CA-92, and it is the approach that has to be
     driven. Ruled: the Cañada side.
  5. **The test's great-circle helper is not the product's.** `ScenicKit.Geo.distanceMeters` is haversine;
     `SkylineRouteTests.metresApart` is the spherical law of cosines with its own radius literal, so a
     wrong `Geo` and a wrong bound cannot agree. Production code does not measure the spacing of these
     pins at all, today. `helperMeasuresAKnownDistance` pins the helper against one degree of latitude
     (6_371_008.8 * pi / 180) and against a zero-distance NaN, which would otherwise compare false against
     any bound and pass the spacing test while measuring nothing.
  6. **Bicycle Sunday's dates and hours are NOT verified and are not written as facts.** The Brief says
     "Sunday mornings, spring-autumn". No query run for this task returned a schedule, so the doc comment
     says the closure exists, says which stretch it covers (Edgewood Road to CA-92, which is four of the
     seven pins), and says explicitly that the dates and hours are unverified here and that San Mateo
     County Parks is the authority. Also on the record: Nominatim's `extratags` carried no `ref` for any
     of these ways, so CA-35 / CA-84 / CA-92 / I-280 in the comments are the local signing, not query
     output; the `name` strings, way ids and returned points are.
- 2026-09-18T20:36Z-20:45Z **Nominatim, reverse, one request per 1.2 s, `User-Agent: scenic-drive-T-0151
  (claudemax3@phineasfritsch.com)`.** 20 reverse requests and 4 forward ones, from this worktree, through a
  probe script kept in `.artifacts/T-0151/` (gitignored, not committed). Every literal that reached
  `SkylineRoute.swift` was reverse-geocoded AS WRITTEN - the rounded five-decimal value, not a nearby one -
  and each is quoted beside its pin in the file. The seven that shipped:

      37.70526 -122.47165 -> way 23995546  "Junipero Serra Freeway" motorway  ret 37.7052581 -122.4716462
      37.44197 -122.26667 -> way 276909112 "Cañada Road"           secondary ret 37.4419720 -122.2666681
      37.47579 -122.30852 -> way 157466880 "Cañada Road"           secondary ret 37.4757907 -122.3085192
      37.50621 -122.34073 -> way 417324930 "Cañada Road"           secondary ret 37.5062107 -122.3407294
      37.50745 -122.34299 -> way 27672021  "Half Moon Bay Road"    primary   ret 37.5074482 -122.3429911
      37.38776 -122.26638 -> way 305925415 "Skyline Boulevard"     secondary ret 37.3877625 -122.2663781
      37.36648 -122.24765 -> way 258851767 "Skyline Boulevard"     secondary ret 37.3664803 -122.2476514

  The four carried over from T-0141 (rows 1, 2, 5, 6) were re-verified here rather than trusted; all four
  still return the way their comment names. The Brief's finding on the old last pin reproduces: forward
  `Sky Londa, California` returns relation 9966012 at `37.3722734, -122.2613336`, a CDP centroid, and the
  new last pin at 37.36648 is south of it on a carriageway Nominatim names "Skyline Boulevard".
  Supporting results, used in the comments and in ruling 3: `Edgewood Road, San Mateo County, California`
  (forward) -> way 262966568, "Edgewood Road", secondary, bounding box `["37.4676711", "37.4684281",
  "-122.2932501", "-122.2923190"]`, so the mid-Cañada pin at 37.47579 is north of the Edgewood junction;
  way 157466880's own bounding box is `["37.4648211", "37.5050132", "-122.3383518", "-122.2988550"]`, so
  that pin is on the reservoir run between Edgewood Road and CA-92. Two candidate points were REJECTED by
  their own results and are on the record: `37.4930, -122.3064` returns way 27878050 "Junipero Serra
  Freeway" (the 280/92 interchange, not the Cañada junction), and `37.35000, -122.24800` returns way
  8924042 "Rapley Ranch Road", not Skyline Boulevard.
- 2026-09-18T20:50:40Z **RED, by name, verbatim.** With the mid-Cañada pin deleted from
  `SkylineRoute.waypoints` and nothing else changed, `swift test --scratch-path .build/T0151 --filter
  SkylineRouteTests`:

      × Test "no gap on the 280 -> Cañada -> 92 leg is wider than the bound" recorded an issue at
        SkylineRouteTests.swift:192:9: Expectation failed: (widest → 9681.899324888309) <
        (Self.canadaLegMaxSpacingMeters → 6000.0)
      → widest gap on the Cañada leg is 9681.899324888309 m, bound 6000.0 m;
        gaps were [9681.899324888309, 242.38957931576934]
      × Test run with 8 tests in 1 suite failed after 0.005 seconds with 6 issues.

  That is the rat-run gap: 9681.899324888309 m of Cañada Road with no pin in it, with the Edgewood Road
  junction inside it. Five other tests in the suite went red with it (the count, the literal comparison,
  the leg slice, the order `#require`, the URL), which is the list being checked from more than one angle;
  `midCanadaPinIsWhatKeepsTheBound` stayed GREEN throughout, because it measures this file's own literals
  and not the shipped array - that is the difference the suite comment argues for. The pin was then put
  back; the red was produced by editing `Sources/Handoff/SkylineRoute.swift` in place and reverting it, so
  nothing of the demonstration is in the commit.
- 2026-09-18T20:52:00Z **GREEN, and one check that had to be argued with first.** The first full-suite run
  after the move failed by name: `HandoffSourceTests` -> "every capitalised identifier in the shipping
  source is on the allow-list" -> `Expectation failed: (Self.allowedTypes → [...]).contains(String(token) →
  "SkylineRoute")`. That is the allow-list working exactly as its own doc comment says it should - a new
  type under `Sources/Handoff` is refused until somebody argues for it - so the argument is written into
  that list beside the entry rather than the entry being slipped in. `SkylineRoute` names no type the list
  did not already allow. Full suite after that: `√ Test run with 258 tests in 33 suites passed`.
- 2026-09-18T20:54:57Z-20:56:39Z **ios-compile, one dispatch, green first try.** `gh workflow run
  ios-compile.yml --ref task/T-0151` at 47f9f64 -> run **35394012179**, conclusion **success**. From
  `gh run view 35394012179 --log`:

      simulator-build	build for the iOS Simulator	2026-09-18T20:56:21.0158350Z ** BUILD SUCCEEDED **

  The log carries `Compiling SkylineRoute.swift` (target `Handoff`, six lines across the two
  architectures) and `SwiftCompile normal arm64 Compiling\ SkylineHandoff.swift
  /Users/runner/work/scenic_drive/scenic_drive/apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/SkylineHandoff.swift
  (in target 'FeatureScenicHome' from project 'ScenicApp')`, so the Apple side of this change was compiled
  and not merely carried along. A grep for `error:` over the 1682-line log matches nothing. This is a
  COMPILE and nothing more: the job runs no test, and no Apple test target exists for it to run.
- 2026-09-18T20:57:05Z **Acceptance re-run, bare, exit codes captured.** `swift test --scratch-path
  .build/T0151 --filter SkylineRouteTests` -> `√ Test run with 8 tests in 1 suite passed after 0.003
  seconds`, exit 0. `swift test --scratch-path .build/T0151` -> `√ Test run with 258 tests in 33 suites
  passed after 0.325 seconds`, exit 0. Neither was piped into anything before its status was read.

  **STILL OPEN.**

  1. **The bound is a proxy and is named as one.** What the product needs is "Apple Maps cannot leave
     Cañada Road at Edgewood and rejoin CA-92 off 280". What the test checks is "no consecutive pair on
     the Woodside -> CA-92 leg is more than 6000 m apart". The second implies a pin between Edgewood Road
     and CA-92 only because the pins are where they are; it is not the same statement, and no test in this
     repository can make the first one without a router. The 6000 m is a product choice, argued beside the
     constant, not a measurement.
  2. **Nothing has been driven, and nothing has run on a device.** ios-compile compiles; it does not
     launch. Whether Apple Maps honours seven waypoints in this order on a real phone is unproven here.
  3. **No pin covers any of this.** `pins_affected: []` is unchanged: the spacing bound and the
     reverse-geocode rule live in a test, not in `pins/PINS.yaml`. A future task could pin "every
     coordinate literal under `Sources/Handoff` has a way id beside it", which would be a structural
     check; this task did not, because the rule it would encode ("the comment names the road the pin is
     on") is exactly the kind of property CLAUDE.md forbids anchoring on a comment.
  4. **`SkylineHandoff.destination` and `.waypoints` became computed properties** (`static var`, forwarding
     to `SkylineRoute`) where they were `static let`. Behaviourally identical for two immutable constants;
     noted because it is a diff a reviewer will see and it is not load-bearing.
  5. **Bicycle Sunday's schedule is still unverified** - see ruling 6. Anyone testing the handoff on a
     Sunday morning should check San Mateo County Parks before touching a coordinate.
  6. **Untouched on purpose:** both `Package.swift` files (serial-only), `apps/ios/Packages/ScenicApp/Tests/`
     (does not exist; it stays in `touches:` as the Brief wrote it, unused), `pins/`, and the four
     coordinates carried over from T-0141, which were re-verified but not moved.
- 2026-09-18T21:00:59Z-21:03:11Z **PR #96 opened against main; its checks read on the PR, not locally; the
  whole acceptance block re-run at this commit.** `gh pr checks 96` -> `pins-source-only pass 51s` and
  `core pass 2m20s`, both jobs of actions run 35394456751, exit 0; that is `ops/check-pins` and `ops/test`
  reporting from CI, which is where the task text says to read them from on this box. Re-run here at
  21:03:11Z, each command bare: `swift test --scratch-path .build/T0151 --filter SkylineRouteTests` ->
  `√ Test run with 8 tests in 1 suite passed after 0.004 seconds`, exit 0; `swift test --scratch-path
  .build/T0151` -> `√ Test run with 258 tests in 33 suites passed after 0.323 seconds`, exit 0; `wc -l` ->
  150 / 226 / 184 / 78, all under the 300-line cap. ios-compile 35394012179 is not re-run: it was green on
  47f9f64 and the only commits after it are this task file, which the Apple build does not read.
  `state: claimed` and `reviewer: null` are unchanged - this task is not signed off by its own author.
