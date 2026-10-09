---
id: T-0325
title: Learned corridor speeds reach the ETA - completed drive legs feed LearnedCorridorSpeeds.record with an H3-8 cell, and the preview's ETA and estimate badge come from retime, so the badge goes away after 5 drives on a corridor (M7 exit)
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-09T10:44:52Z
lease_expires_at: 2026-10-09T22:44:52Z
worktree: .worktrees/T-0325
branch: task/T-0325
exclusive: []
touches: [Sources/ScenicKit/, Sources/ScenicAPIClient/, Sources/PlaceStore/, Tests/, apps/ios/Packages/ScenicApp/Sources/, services/api/src/, services/api/test/, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-SAFE-07, P-PRIV-05]
reviewer: null
depends_on: [T-0320, T-0317]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE (a)-(d) in a dated Log entry before any code (the 2026-10-09T10:50:51Z entry)."
  - "H3-8 on the device (R1): CorridorCell.containing(latitudeDegrees:longitudeDegrees:) - Telemetry's internal latLngToCell port (uber/h3 v4.1.0) copied into ScenicKit and run at resolution 8 - equals h3-py 4.1.2 latlng_to_cell by FULL EQUALITY over a generated table (LA and Bay Area points, the 12 pentagon centres, both poles, the antimeridian, 200 seeded random points) at resolution 8, and the same port at resolution 5 equals h3-py over the same table (the Telemetry parity: the code Telemetry ships at 5 answers uber/h3 at 8); nil for NaN, infinities and every out-of-range bound (latitude -90 / 90 accepted, nextafter outside refused; longitude -180 / 180 accepted, nextafter outside refused)."
  - "Per-edge free-flow (R2): CorridorRoute(route:timeRuns:) over GraphHopper details=time runs (from, to, whole milliseconds) - one CorridorEdge per maximal stretch of consecutive runs whose first vertex lies in the same H3-8 cell, freeFlowSeconds = summed ms / 1000 - nil unless the runs tile 0...count-1 edge for edge (tripPlanner.ts edgesOf's rule) with ms >= 0, not all zero, and every vertex a cell; a full-equality table over every bound (no runs, first.from 1, a gap, an overlap, from == to, last.to one short and one long, ms -1 / 0 / all zero, a vertex out of range, one route, a route whose cells repeat non-adjacently)."
  - "Completed legs (R3): CorridorClock.observe(_ session: DriveSession, at: Date, into: inout LearnedCorridorSpeeds) records exactly one record(cell:hourOfWeek:actualSeconds:freeFlowSeconds:) per corridor edge driven from its entry to the next edge's entry with every observation between on the line (legEnd non-nil), actual = exit date - entry date, hour = HourOfWeek.of(entry, in: speeds.timeZone); the first edge is entered at the drive's first on-line observation in it, the last closes on arrival (legEnd at the line's last vertex within DriveSession.awayThresholdMeters); a skipped edge, an off-line observation inside an edge, and everything after the session's line changes (a reroute) record nothing. Table over those transitions with the learner's slots compared WHOLE."
  - "The preview from retime (R4): RetimedPreview.of(_ preview:, timeRuns:, by: TrafficProvider, departsAt:) answers the preview with etaSeconds and etaIsEstimate from retime over CorridorRoute(route: preview.route, timeRuns:), every other field equal; with no route (no or bad runs) the preview unchanged - the badge stays. Table: every edge at 0 / 4 / 5 / 6 samples x one edge unlearned x no runs, previews compared WHOLE; the badge is off only when every edge is learned (P-SAFE-07)."
  - "End to end on the Linux path (R5): five completed drives through CorridorClock on one route clear RetimedPreview's badge and four do not (the M7 exit), the learner compared whole."
  - "P-PRIV-05 (R6): ops/lib/check-learned-speeds-sites.py's whitelist extended to every new line naming a guarded identifier, CorridorClock and CorridorObservation added to the guarded identifiers, seen red then green; LearnedSpeedsPrivacyTests covers the new types (none Encodable or Decodable); no new line in ScenicAPIClient, Telemetry or apps/ names a guarded identifier."
  - "Tests RED first by name against stubbed bodies, then green; P-SAFE-07 binds the new tests by name; digest rows for every new or changed Sources/ file; ops/mutate/traffic population extended to every new subject with a raised literal floor, the new entries CAUGHT by name; check-mutate-population, check-line-cap, check-pins-yaml, queue-check green; ios-compile and ios-screenshot CI success."
  - "The rest FILED as follow-ups with ids (R7): the Worker passes details=time through /plan (and reroute) and ScenicAPIClient/PlanPreview carry the runs; the app wiring (NavAdapter feeds CorridorClock, PlanAdapter shows RetimedPreview) with the learner persisted across launches in PlaceStore."
---
## Brief

T-0320 owner stillOpen 1 (PR #207): LearnedCorridorSpeeds exists but nothing feeds it or reads it. Open questions
the claimer MEASURES and RULES before writing acceptance (CLAUDE.md: measure the population first):
(a) where an H3-8 index comes from - Telemetry builds resolution 5 only, internal, and ScenicKit cannot import it
without a Package.swift change (serial file);
(b) per-edge free-flow times - PlanResponse carries only etaSeconds; does the Worker pass GraphHopper details=time
through (a Worker change) or does the device split the ETA by edge length (ruled honestly);
(c) where completed legs come from - DriveSession (T-0317) progress + fix timestamps, recorded on device only,
persisted across launches (PlaceStore, no Codable path to the server per P-PRIV-05);
(d) the preview's etaIsEstimate becomes retime's isEstimate; the "estimate · no traffic data" badge stays until every
edge is learned (product invariant).

## Log
- 2026-10-08T13:58:47Z filed by agent/claude-opus-5 (orchestrator) from T-0320's stillOpen 1.
- 2026-10-08T13:59:22Z renumbered T-0324 -> T-0325 by agent/claude-opus-5 (orchestrator): task/T-0321 already holds a T-0324.
- 2026-10-09T10:44:52Z claimed by agent/claude-opus-5; lease until 2026-10-09T22:44:52Z
- 2026-10-09T10:50:51Z MEASURE then RULE (agent/claude-opus-5, before any code).
  MEASURED. (a) Sources/Telemetry/H3*.swift is 482 lines (H3BaseCells 53, H3Cell 37, H3CoordIJK 139,
  H3FaceProjection 140, H3IndexBuilder 113), all internal; the port is resolution-generic -
  H3FaceProjection.faceIJK(latitude:longitude:resolution:) and H3IndexBuilder.index(face:coord:resolution:) take
  the resolution, the Class III rotation is `resolution % 2 == 1` - and only H3Cell fixes `resolution = 5`. Root
  Package.swift: ScenicKitTests depends on ["ScenicKit"] only, TelemetryTests on ["Telemetry"] only (serial file,
  not in touches). h3-py 4.1.2 imports on this box (`python -c "import h3"`). (b) services/api/src/scenicPlanner.ts
  ROUTE_DETAILS = scenic_score, road_class, osm_way_id + HAZARD_DETAILS - no `time`; ScenicPlanResult carries eta_s
  only; tripPlanner.ts already asks GraphHopper for TRIP_DETAILS ["time", "distance", "scenic_score"] and edgesOf
  holds the runs to tile [0, last point] edge for edge with whole-millisecond values - so the router answers
  details=time today. (c) DriveSession exposes progressSegment (DriveLine.progress, a forward-only search), legEnd
  (nil before the first usable fix and while it is away from the line), line (replaced whole by a taken reroute)
  and awayThresholdMeters 50; DriveNavigator.swift:73 stamps each DriveFix with
  location.timestamp.timeIntervalSinceReferenceDate, a wall clock. (d) PlanPreview.etaIsEstimate is the server's
  eta_is_estimate, always true (scenicPlanner.ts `eta_is_estimate: true`); showsEstimateBadge reads it.
  RULED. R1 (a): no Package.swift change - the four internal files H3BaseCells, H3CoordIJK, H3FaceProjection and
  H3IndexBuilder are copied unchanged in body into Sources/ScenicKit/Traffic/ (internal, same names - internal
  types of two modules never meet - Apache-2.0 notice kept), and CorridorCell gains containing(latitudeDegrees:
  longitudeDegrees:) at resolution 8. Parity with Telemetry is by the shared oracle: the copy run at 5 AND at 8
  equals h3-py 4.1.2 over one generated table (Telemetry's own res-5 tests already pin its copy to uber/h3). The
  duplicate is the price of the serial file; folding Telemetry onto ScenicKit's copy needs Package.swift and is
  named in stillOpen. R2 (b): the device does NOT split the ETA by length. Worked example: a route of two
  equal-length cells, a freeway one taking 2 min and a back-road one 8 min at free flow; the length split gives
  each 5 min, a free-flow drive observes ratios 5/2 = 2.5 (clamped to 1.0) and 5/8 = 0.625, and retime answers
  5/1.0 + 5/0.625 = 13 min against a true 10 - and after five drives the badge would go away on a 30% wrong ETA.
  Per-edge free-flow is GraphHopper's details=time, passed through by the Worker; the device's half ships here
  (CorridorRoute over the runs, edges grouped by the cell of each run's first vertex - a run longer than a cell is
  attributed wholly to its start's cell). The Worker field and its PlanResponse/PlanPreview decode are a
  follow-up: T-0333 is changing the Worker and ScenicAPIClient now (memory parallel-worker-prs-conflict). Until it
  lands no preview carries runs and RetimedPreview leaves the badge on - it fails safe. R3 (c): CorridorClock reads
  the shipped DriveSession after each observe plus the wall Date of the fix; only edges driven end to end on the
  line are recorded, so a partial, skipped or detoured edge never teaches a ratio; after a reroute nothing more is
  recorded this drive (a reroute answer carries no runs until the R2 follow-up). Persistence across launches is
  the PlaceStore follow-up (GRDB suites run only in CI linux-core); until then the learner is in memory. R4 (d):
  RetimedPreview.of replaces etaSeconds and etaIsEstimate only; fastestEtaSeconds stays the server's (the fastest
  route carries no runs). The ceiling invariant (returned ETA <= fastest + budget) is the Worker's, on free-flow
  times both sides; a retimed ETA is the device's re-estimate of the same route and does not re-run that check.
  R5: the M7 exit is shown on the Linux path end to end (five drives clear the badge, four do not). R6: P-PRIV-05's
  whole-line whitelist grows by every new site and two identifiers. R7: this task is the device slice; the Worker
  pass-through and the app wiring with PlaceStore persistence are filed as follow-ups.
- 2026-10-09T11:43:20Z RED then GREEN, GUARD, BINDINGS (agent/claude-opus-5; code commit 30462645).
  Tests first against the shipped API with stubbed bodies (an early `return nil` / `return 0` / `return preview`
  in CorridorCell.containing, CorridorRoute.init, CorridorClock.observe and RetimedPreview.of): `swift test --filter
  ScenicKitTests\.(CorridorCellTests|CorridorRouteTests|CorridorClockTests|RetimedPreviewTests|LearnedSpeedsPrivacyTests)`
  exit 1 with EIGHT FAILED by name - "every reference point's cell equals h3-py's latlng_to_cell at resolution 8,
  and at 5 as Telemetry's", "latitude -90 and 90 and longitude -180 and 180 are cells; one ulp outside, NaN and
  infinities are nil", "runs tile the route edge for edge into corridor edges; every bound of the tiling refused",
  "a segment's edge is the last edge starting at or before it", "a clean drive teaches every edge once; a skip, a
  detour, a late start, no arrival and a reroute do not", "a fix after arrival teaches nothing more, and observe
  answers how many edges each fix taught", "the badge: on at 0 and 4 samples, off at 5 and 6, on with one edge
  unlearned, and kept without runs", "five completed drives clear the badge and four do not" - while "the five
  reference points are in five different cells" (a check of the h3-py table itself) and "no learned-speed type is
  Encodable or Decodable" passed. Stubs removed: the same filter plus LearnedCorridorSpeedsTests|HourOfWeekTests
  exit 0, all 18 passed. The ScenicKit copy of the uber/h3 port answers h3-py 4.1.2 at resolution 8 AND 5 on all
  249 reference rows. P-PRIV-05: CorridorClock added to IDENTIFIERS; check-learned-speeds-sites.py exit 1 "FAILED -
  4 unapproved, 0 missing of 13 approved" naming the four new lines (CorridorClock.swift x3, RetimedPreview.swift x1),
  then approved: "ok - 17 sites, every one approved, in 7 files"; --prove-red "PROVE-RED OK: 10 of 10 rows red by
  name, control 0" (two new rows: CorridorClock gains Codable, the app holds a corridor clock). Acceptance R6 named a
  CorridorObservation type; the build needed none (observe records straight into the learner and answers a count), so
  only CorridorClock joins the identifiers. LearnedSpeedsPrivacyTests casts CorridorClock as well. P-SAFE-07:
  named-tests.json binds the 8 new tests (filter widened); `run-named-tests.py P-SAFE-07` "NAMED P-SAFE-07
  passed=16/16". Digests: nine rows added or re-approved in check-safety-disclaimer-linked-digests.txt (CorridorCell
  re-approved; CorridorClock, CorridorRoute, CorridorTimeRun, H3BaseCells, H3CoordIJK, H3FaceProjection,
  H3IndexBuilder, RetimedPreview added); ops/lib/check-safety-disclaimer exit 0. Population: ops/mutate/traffic
  grows by 27 entries (36-62) over the eight new subjects, MIN_MUTATIONS 35 -> 62, MIN_TEST_FILES 3 -> 7;
  check-mutate-population "every added module is covered or allowlisted; the floor of 146 holds". check-line-cap
  "530 Swift files tracked ... none over 300 lines" (largest new file: CorridorCellReference.swift, 255).
  Follow-ups FILED (R7): T-0342 (the Worker passes details=time through /plan and reroute; ScenicAPIClient and
  PlanPreview carry the runs) and T-0343 (the app feeds CorridorClock, persists the learner in PlaceStore, shows
  RetimedPreview). Highest id in use before filing: T-0341 (queue/ and origin task/T-0333, task/T-0339).
- 2026-10-09T12:36:58Z MUTANTS and iOS CI (agent/claude-opus-5). `python ops/mutate/traffic.py --only 36,...,62` at
  e1e3859a: "MUTATE FAILED caught=25/27" - MISSED 51 (an entry after an off-line fix counted: the detour row came
  back on the line inside the same edge, so previousOnLine was true at the transition) and MISSED 56 (a reroute
  ignored: the rerouted line [far, v4] never reached the plan's arrival vertex, so the mutant taught nothing either).
  Closed by two rows in CorridorClockTests.transitionTable (094d5d3c): "off the line in edge 1, back on it in edge
  2" (expected edges [0, 3]) and "rerouted onto a line that rejoins the plan" (a five-vertex line ending v2, v3, v4;
  expected [0]); `--only 51,56` at 094d5d3c: "MUTATE OK caught=2/2", both by the transition test's name. Every
  other new entry CAUGHT by a test it names (36-50, 52-55, 57-62). iOS CI at 30462645 (the code commit):
  ios-compile run 37925460060 success; ios-screenshot run 37925466654 success - plan-preview-light.png looked at:
  "55 min · 20 min longer than the fastest way" with the "estimate · no traffic data" badge under it, as ruled (no
  preview carries time runs until T-0342, so the badge stays).
- 2026-10-09T14:05:35Z RULING on rv1-t0325 FAIL (agent/claude-opus-5; PR #226 head ed27efb1). B1 is right: the
  arrival conjunct `end.vertex == route.coordinates.count - 1` is the only thing telling a pin from arrival, and every
  CorridorClock and five-drives drive was built with `waypoints: []`, so legEnd.vertex was always the last vertex and
  the mutant could not fail. The shipped code is right (the witness's baseline teaches all four edges); the gap is
  the tables' input population. Closed by CLASS - the tables range over waypoints too: CorridorClockTests'
  transition table and RetimedPreviewTests' five-drives test run every row under three variants - no pins; a pin
  inside the last corridor edge in that edge's cell (line v0 v1 v2 v3 m v4 with m = on(3, 0.0005), runs
  80000/90000/40000/1000/99000 ms, the reviewer's witness); a pin at an edge boundary (v3, the last edge's first
  vertex). The variant sets the line, the runs and the pins; drive() checks the variant reached the session (legs =
  pins + 1) and that its corridor edges equal the no-pin route's, so the per-row answer is the same table for every
  variant. Every transition row is compared whole: the learner's slots AND the count observe answered per fix. f3
  moves to on(3, 0.0001), 300 s (inside 50 m of m, as the witness); a row "stops at m" is added. Population: entry 63
  "arrival ignores the last-vertex check" (the B1 mutant), MIN_MUTATIONS 62 -> 63, run --only 63 MISSED at the old
  tests and CAUGHT by name at the new. Tests only - no Sources/ change, so no digest re-approval from this fix (the
  merge of origin/main may still need one). R1: the acceptance R6 line is re-quoted below to name what shipped
  (CorridorClock only); the dated entries above stay as written. R2 and R3 stay recorded for T-0343; R4/R5 need
  nothing.
