---
id: T-0317
title: The drive session's decisions live in ScenicKit and are Linux-tested - off-route detection, reroute request (remaining pinned waypoints + same lambda, never bare O->D), offline rejoin mode with zero requests, and the >4.5 m/s motion gate - ready for the Ferrostar adapter (M7)
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-08T07:53:28Z
lease_expires_at: 2026-10-09T03:53:28Z
worktree: .worktrees/T-0317
branch: task/T-0317
exclusive: []
touches: [Sources/ScenicKit/, Tests/ScenicKitTests/, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-NAV-01, P-SAFE-06]
reviewer: null
depends_on: [T-0294]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST in a dated Log entry: the plan's Navigation section (off-route -> if online re-request /plan with the same lambda and the REMAINING pinned waypoints, never bare O->D; if offline keep guiding to rejoin the planned line, no request) and P-NAV-01 / P-SAFE-06 as written in pins/PINS.yaml; what /plan accepts today for a reroute (read services/api/src/plan.ts whitelist - if it cannot carry waypoints + lambda, rule the gap and file the Worker half; never widen the Worker here)"
  - "ScenicKit DriveSession: a pure state machine fed location fixes (coordinate, speed, timestamp) and connectivity; off-route = distance to the planned polyline above a ruled threshold for a ruled dwell; the reroute it asks for carries exactly the waypoints not yet passed and the same lambda (full equality); offline -> rejoin mode with zero requests; back online -> one reroute; table over every bound (threshold +/- nextafter, dwell edges, speed exactly 4.5 m/s) per memory range-checks-every-bound"
  - "Motion gate: above 4.5 m/s the session exposes only the one large action and voice; a full-equality table over speed bounds and over hysteresis if ruled"
  - "P-NAV-01 and P-SAFE-06 bind the new tests by name (PINS.yaml quoted strings, memory pins-yaml-strict); digest rows for new Sources files; a mutation population with a literal floor, three entries MISSED before and CAUGHT by name after"
---
## Brief

Plan, Navigation on the scenic path + M7. The Apple-side Ferrostar adapter (NavAdapter, the only importer of Ferrostar)
is a later task under the package-swift lock; this task puts every decision it will call into Linux-testable ScenicKit
first, so the adapter is a thin shell. Calm, minimal-distraction driving UI (memory owner-route-intent).

## Log
- 2026-10-08T07:53:18Z filed by agent/claude-opus-5 (orchestrator) from the milestone gap map (M7 navigation, logic half).
- 2026-10-08T07:53:28Z claimed by agent/claude-opus-5; lease until 2026-10-09T03:53:28Z
- 2026-10-08T07:57:21Z MEASURED, then RULED, before any code (author rule).
  MEASURED. (m1) Plan `### Navigation on the scenic path (Ferrostar)` (plan line 132): "Off-route hook -> if online,
  re-request `/plan` with the same lambda and the *remaining* pinned waypoints (never bare O->D); if **offline**,
  Ferrostar keeps guiding to rejoin the planned line ("rejoin mode")." Plan pin table line 247: `P-SAFE-06 | Motion
  gate >4.5 m/s | unit + UI | linux+mac`; line 272: `P-NAV-01 | Reroute request carries remaining pinned waypoints +
  same lambda; offline -> no request | unit with fake location feed | mac`; screens line 318: "Drive (... >4.5 m/s one
  >=60 pt button + voice; rejoin banner)"; lifecycles line 146: `offlineDuringDrive` -> rejoin mode banner.
  (m2) pins/PINS.yaml: P-NAV-01 does NOT exist. P-SAFE-06 DOES exist and is a different property - "A GraphHopper
  sign that nothing maps fails the build" (added 2026-09-15, assertion `bash ops/lib/check-guidance-gate`). P-SAFE-02
  and P-SAFE-07 are free in PINS.yaml but reserved by the plan table (hazards at 3 layers; estimate badge).
  (m3) services/api/src/planRequest.ts: BODY_KEYS = origin, destination, budget_minutes, departs_at, vehicle;
  ORIGIN_KEYS = lat, lon (2 dp, refused otherwise); DESTINATION_KEYS = place (a corpus place id). Every key at every
  level is whitelisted and anything else is 400. /plan today carries NO waypoints and NO lambda.
  (m4) ScenicKit: Coordinate (Model/), Geo.distanceMeters (haversine), ScenicPlan.waypoints = PlanWaypoints
  .decisionPoints, which returns VERTICES of the routed path (path.coordinates[i]), outcome.lambda. No Drive/ dir.
  RULED.
  R1 (P-SAFE-06 id clash). The acceptance's "P-SAFE-06" is the plan's motion-gate row; that id in PINS.yaml has
  held the guidance catch-all gate since 2026-09-15 and is referenced by check-guidance-gate and closed tasks, so it is
  NOT renamed or repurposed. The motion gate is pinned as NEW id P-SAFE-09 (02 and 07 are the plan's), its statement
  saying it is the plan's P-SAFE-06 row. P-SAFE-06 itself is unchanged by this task. P-NAV-01 is added. Both bind
  their tests by name through ops/lib/run-named-tests.py (named-tests.json), runs_on [linux, mac] (the plan's `mac`
  for P-NAV-01 was because a fake location feed was assumed to need Ferrostar; the logic is ScenicKit here).
  R2 (the Worker gap). /plan cannot carry waypoints or lambda (m3), and CLAUDE.md's invariant "never more than one
  coordinate per user action, never more than 2 dp" forbids the naive encoding (N pinned waypoints = N coordinates
  at full precision). The Worker is NOT widened here. ScenicKit emits a device-side RerouteRequest {origin = the
  current fix, remainingWaypoints, firstRemainingWaypoint (index into the plan's pins), destination, lambda} -
  full fidelity, so the wire half can choose an encoding that sends at most one 2-dp coordinate (e.g. a plan
  token the Worker remembers + the index of the first remaining pin + lambda) without ScenicKit changing. The
  Worker half is filed as its own task (backlog) by ops/new-task in this branch.
  R3 (off-route). distance = least distance from the fix to the planned polyline, measured in a local
  equirectangular frame around the fix (metres, R = Geo.earthRadiusMeters). AWAY iff distance > 50 m (50.0 is ON
  the line). OFF-ROUTE iff away continuously for >= 5 s (fix.timestamp - firstAwayTimestamp >= 5; exactly 5.0 is
  off, nextDown(5) is not). Any on-line fix resets the dwell. Bounds tabled at 50 (exact), the smallest float
  distance above 50, dwell 5 and nextDown(5). A non-finite or out-of-range fix coordinate is ignored (no state
  change) - fail closed: it can neither trigger a reroute nor clear one.
  R4 (remaining waypoints). Progress = the segment index of the nearest segment among the CONTIGUOUS run of
  within-50 m segments that starts at the first within-50 m segment at or after the current progress (forward
  only, so a loop's closing leg next to its start cannot jump progress to the end). Updated only by on-line fixes.
  A pinned waypoint at vertex v is passed iff progress >= v. Each waypoint must be a vertex of the line, matched
  in order (PlanWaypoints guarantees it); otherwise the session is not constructed (failable init). The request's
  waypoints are EXACTLY the not-passed ones, in order, and lambda is the plan's, compared by full equality.
  R5 (online/offline). Off-route + online -> exactly one request, mode rerouting; further fixes and online edges
  while rerouting ask for nothing. Off-route + offline -> mode rejoining, zero requests for any number of fixes.
  Rejoining + an on-line fix -> guiding. Rejoining + offline->online edge -> exactly one request from the latest
  fix. rerouteFailed -> rejoining (no automatic retry; the next request needs a new offline->online edge or a new
  off-route episode). rerouteArrived(line, waypoints) replaces the line and pins (same lambda) and returns to
  guiding; it is ignored unless rerouting.
  R6 (motion gate). surface = .minimal (the one large action + voice) iff speed > 4.5 m/s; exactly 4.5 is .full.
  A speed that is NaN, negative (CoreLocation's -1 = invalid) or infinite is .minimal (fail closed: unknown speed
  is treated as moving). NO hysteresis is ruled: the plan names one bound, a dip below 4.5 shows the full surface
  only when the car is crawling, and the release direction is a device-iteration (M7 TestFlight) question, not a
  Linux one; the table covers 4.5, nextDown/nextUp(4.5), 0, -0.0, -1, +-inf, NaN, greatestFiniteMagnitude.
  R7 (scope). One type per file under Sources/ScenicKit/Drive/; Foundation only; no Ferrostar types (NavAdapter is a
  later task). Digest rows for every new Sources file; mutation population ops/mutate/drive*.py, DRIVERS + COVERED_FLOOR.
- 2026-10-08T09:02:16Z R6 addendum, ruled at GREEN: the surface BEFORE the first fix is `.minimal` (fail closed - the
  speed is unknown), tested by minimalBeforeAnyFix. RerouteRequest is checked field by field as well as whole,
  because both sides of `==` go through its init (mutation 15 would otherwise survive full equality).
- 2026-10-08T09:02:16Z ACCEPTANCE RE-QUOTED on head a5dc726c (origin/main 9cf2b986 merged: already an ancestor, main
  had not moved; T-0314 not yet on main).
  (1) MEASURE then RULE FIRST: the 07:57:21Z entry (m1-m4, R1-R7), committed alone as 3d6189ba before any code.
  The Worker gap is ruled (R2) and filed as queue/backlog/T-0318 (ops/new-task answered T-9902 from a stray ref;
  renumbered to the next id after origin/main's T-0317). The Worker is not touched.
  (2) DriveSession (Sources/ScenicKit/Drive: DriveSession, DriveLine, DriveFix, DriveMode, DriveSurface,
  RerouteRequest; Foundation only). RED first by name at e49037dd against signature stubs: `Test run with 20 tests
  in 3 suites failed ... with 85 issues`, 19 named failures (the meta-test noRowIgnoresItsVariant green by design).
  GREEN at eaa73290: `swift test --filter "DriveSessionTests|DriveRerouteTests|DriveMotionGateTests|
  GuidanceMappingTests"` -> `Test run with 36 tests in 4 suites passed` (exit 0). Bounds tabled: 50 m exact and the
  smallest float distance above it (awayThresholdIsExact), dwell 5 s and nextDown(5) plus the restart
  (dwellBoundIsExact), lat/lon +-90/+-180 exact vs nextUp/nextDown, NaN/inf position and time (unusableFixIsIgnored);
  remaining pins over two variants whose rows differ (rerouteCarriesRemainingPinsAndLambda,
  offlineThenOnlineCarriesRemainingPins, noRowIgnoresItsVariant); offline 0 requests (offlineRejoinsWithZeroRequests),
  back online exactly one (backOnlineAsksOnce), one while rerouting (reroutingAsksOnce).
  (3) Motion gate: DriveMotionGateTests, full equality over 0, -0.0, least nonzero, 3, nextDown/4.5/nextUp, 30,
  greatest finite, +-inf, -least nonzero, -1, NaN, through observe(_:); no hysteresis ruled (R6), tested by
  eachFixSetsTheSurface.
  (4) Pins: P-NAV-01 and P-SAFE-09 (R1) added, assertion `run-named-tests.py <id>`; `NAMED P-NAV-01 passed=15/15`,
  `NAMED P-SAFE-09 passed=5/5`. SEEN RED: with mutations 5 and 14 applied by hand, `NAMED P-NAV-01 passed=12/15`
  (exit 1; rerouteCarriesRemainingPinsAndLambda, offlineThenOnlineCarriesRemainingPins,
  arrivalReplacesLineKeepsLambda FAILED) and `NAMED P-SAFE-09 passed=4/5` (exit 1; minimalBeforeAnyFix FAILED);
  restored by git checkout. check-pins-yaml: `PINS-YAML ok pins=46 fields=371`. P-SAFE-06 unchanged.
  Digest rows: six Sources/ScenicKit/Drive rows in PINNED_ROOT_SOURCES (706ee8a2 DriveFix, b18ff436 DriveLine,
  2b8736c2 DriveMode, fcf84ec8 DriveSession, 82f295cd DriveSurface, 8cf25184 RerouteRequest) - new files;
  check-safety-disclaimer exit 0 (`209 root + pbxproj file(s) (-linked)`), check-guidance-gate exit 0.
  Population ops/mutate/drive.py: MIN_MUTATIONS = 28, MIN_EQUIVALENT = 1. `--prove-floor`: `FLOOR PROOF OK: 7 of 7`.
  MISSED BEFORE: `--only 7,14,22 --prove-vacuity` -> MISSED 7, 14, 22, `VACUITY PROOF OK ... MISSED=3 of 3`.
  CAUGHT AFTER: the full run -> `caught by the test that names it: 28 of 28 (wrong killer 0, trapped 0,
  compile-only 0, MISSED 0, skipped 0)`, E1 MISSED as required, `MUTATE OK caught=28/28 equivalent_caught=0`.
  DriveMode.swift allowlisted (a three-case enum). check-mutate-population exit 0 (`the floor of 119 holds`),
  check-line-cap exit 0 (`426 Swift files ... none over 300 lines`; DriveSession 103, DriveRerouteTests 156,
  DriveSessionTests 145), queue-check exit 0 (`QUEUE OK (309 tasks)`).
