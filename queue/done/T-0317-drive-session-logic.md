---
id: T-0317
title: The drive session's decisions live in ScenicKit and are Linux-tested - off-route detection, reroute request (remaining pinned waypoints + same lambda, never bare O->D), offline rejoin mode with zero requests, and the >4.5 m/s motion gate - ready for the Ferrostar adapter (M7)
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-08T07:53:28Z
lease_expires_at: 2026-10-09T03:53:28Z
worktree: .worktrees/T-0317
branch: task/T-0317
exclusive: []
touches: [Sources/ScenicKit/, Tests/ScenicKitTests/, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-NAV-01, P-SAFE-06]
reviewer: agent/rv2-t0317
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
- 2026-10-08T10:13:14Z ROUND 2 (rv1-t0317 FAIL on PR #205, head 9910652c). Orchestrator rulings, recorded before code:
  B1 (blocking): deleting `awaySince = nil` from rerouteArrived(line:waypoints:) survives all three suites - the
  first fix after a landed reroute that is > 50 m from the NEW line reroutes again with zero dwell, breaking R3
  (away continuously >= 5 s). RULED: the reviewer's repro becomes a P-NAV-01 test in DriveRerouteTests, bound in
  ops/lib/named-tests.json; population entry 29 deletes the reset - MISSED at 9910652c, CAUGHT by that test's name
  (--only). R2: a missing cosine in DriveLine.distanceMeters(from:toSegment:) (`let scale = Self.metersPerDegree`)
  is caught only by the loop test, because every bound row offsets in latitude from an east-west line. RULED: bound
  rows against a NORTH-SOUTH segment at latitude 34 - exactly 50 m east (on), the next distance up (away), and a
  fix 42 m east, which the missing cosine measures as ~50.7 m (away); population entry 30 is that mutant, caught by
  the new row's name. R4: an unusable fix with a valid speed above 4.5 left the surface at its previous value
  (possibly .full), against R6 "unknown is moving". RULED: an unusable fix sets .minimal (the safe side of
  P-SAFE-09); unusableFixKeepsSurface becomes unusableFixIsMinimal (a table over bad-fix kinds x carried speeds x
  the surface before it); population entry 6 now REVERTS that (an unusable fix keeps the surface) and is CAUGHT.
  R5: losing connectivity while a reroute is out stayed .rerouting until NavAdapter called rerouteFailed. RULED
  session side (3 lines, under the 15-line bar): the online-to-offline edge while .rerouting enters .rejoining, so
  the next offline-to-online edge asks exactly once from the latest fix (R5's per-edge count). reroutingAsksOnce and
  backOnlineAsksOnce asserted the old stay-rerouting edge; they keep their counts over the edges that do not drop
  the connection, and the new test lostConnectionWhileReroutingRejoins carries the drop. Population entry 31 deletes
  the new line, caught by that name. OBLIGATION for NavAdapter (the Ferrostar half, not T-0318): on the lost edge it
  cancels the in-flight reroute and drops its reply or failure - a stale rerouteArrived/rerouteFailed after the
  next edge's request would answer the wrong request. Digest rows re-approved for every changed Sources file.
  Verification per memory faster-verification-in-rounds: the three suites, `--only 6,29,30,31` (and the vacuity arm
  over the new entries), the plain gates.
- 2026-10-08T10:43:28Z ROUND 2 GREEN, quoted on merged head f5c04c22 (origin/main d908849b merged - queue moves only;
  T-0314 has not landed, so DRIVERS/COVERED_FLOOR and the digest table needed no union).
  MISSED BEFORE (B1): population entry 29 committed alone at 0ebd8ea1, whose five subjects are byte-identical to
  9910652c (`pristine ... == HEAD` x5): `python ops/mutate/drive.py --only 29` -> `MISSED 29 a landed reroute keeps
  the dwell exit=0 no test objected`, `MUTATE FAILED caught=0/1`. R2's mutant was not MISSED at 9910652c (the
  reviewer: caught by the loop test only); R4's and R5's entries revert code that did not exist there.
  CAUGHT AFTER at 1b052aa4: `--only 6,29,30,31` -> caught 6 by unusableFixIsMinimal's name, 29 by
  landedRerouteRestartsTheDwell's, 30 by the loop test AND eastThresholdAtLatitude34's, 31 by
  lostConnectionWhileReroutingRejoins's; `caught by the test that names it: 4 of 4 (wrong killer 0, trapped 0,
  compile-only 0, MISSED 0, skipped 0)`, `MUTATE OK caught=4/4`. `--prove-floor` -> `FLOOR PROOF OK: 7 of 7`
  (floor now MIN_MUTATIONS = 31). The vacuity arm over the new entries was NOT run this round (the line above
  promised it): entry 29's MISSED at 0ebd8ea1 is the live-suite version of that proof; 30 and 31 were not shown
  MISSED anywhere.
  Suites on f5c04c22: `swift test --filter "DriveSessionTests|DriveRerouteTests|DriveMotionGateTests"` -> `Test run
  with 23 tests in 3 suites passed` (exit 0; 20 before, +3 new, unusableFixKeepsSurface renamed
  unusableFixIsMinimal). `NAMED P-NAV-01 passed=18/18`, `NAMED P-SAFE-09 passed=5/5`.
  Digest: DriveSession.swift re-approved fcf84ec8 -> 806ef8e4 (the only changed Sources file); bare `bash
  ops/lib/check-safety-disclaimer` exit 0 (`209 root + pbxproj file(s) (-linked)`). check-mutate-population exit 0
  (`the floor of 119 holds`), check-pins-yaml exit 0 (`PINS-YAML ok pins=46 fields=371`), queue-check exit 0
  (`QUEUE OK (309 tasks)`). Line cap: DriveSession 111, DriveSessionTests 190, DriveRerouteTests 172,
  DriveMotionGateTests 94, DriveFixtures 86.
- 2026-10-08T10:52:53Z CI on f9001f5f went red: `PINS ... failed=1` - P-PROC-01 (`bash ops/queue-check`) on the PR
  merge ref. Cause: main moved to 3840fb3d after the merge above (T-0314 PR #204 and T-0316 PR #203 landed), and
  T-0316 filed its own queue/backlog/T-0318 (trip places read after quota) - two tasks with one id. RULED: this
  branch's Worker-half task (filed above as T-0318) is renumbered T-0319 (git mv + its `id:` line; no ref on any
  branch or in the queue holds T-0319); the dated entries above keep the id they were written with. Merged
  origin/main 3840fb3d: DRIVERS / COVERED_FLOOR, named-tests.json, PINS.yaml and the digest table auto-merged as a
  union of T-0314's rows and this branch's; the gates below re-run on that head.
- 2026-10-08T11:42:52Z REVIEW PASS (round 2) by agent/rv2-t0317 (not the owner) on PR #205, head 8b56dff6 ==
  origin/task/T-0317. Fresh detached worktree, own scratch path. Baseline: `Test run with 23 tests in 3 suites
  passed`. Five hand-applied mutants, each over the three suites, sources restored byte-for-byte after each:
  B1 delete `awaySince = nil` in rerouteArrived -> CAUGHT by "a landed reroute restarts the dwell" only (1 issue);
  R2 `let scale = Self.metersPerDegree` -> CAUGHT by the north-south latitude-34 test and the loop test (2 issues);
  R4 drop the unusable-fix `surface = .minimal` -> CAUGHT by "an unusable fix is an unknown speed" (24 issues, the
  before=full rows); own M4 observe's `<=` -> `<` -> CAUGHT by "50 m exactly is on the line" and the latitude-34
  test; own M5 `!online, mode != .rejoining` (any offline edge rejoins) -> CAUGHT by "connectivity lost while a
  reroute is out" (the guiding-stays-guiding row). Survivors: 0. `gh pr checks 205`: core pass, pins-source-only
  pass. Bare: check-mutate-population.py exit 0 (`the floor of 128 holds`), queue-check exit 0 (`QUEUE OK (311
  tasks)`), check-safety-disclaimer exit 0. LAST: `git merge-base --is-ancestor origin/main origin/task/T-0317`
  (main 3840fb3d) exit 0. Recorded, not blocking: entries 30 and 31 were never run through `--prove-vacuity`;
  T-0319's id reservation and the NavAdapter cancel-on-disconnect obligation stay with the orchestrator.
