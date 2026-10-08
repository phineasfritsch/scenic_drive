---
id: T-0320
title: ScenicKit learns corridor speeds on the device - a TrafficProvider protocol and LearnedCorridorSpeeds (H3-8 cell x hour-of-week EWMA of actual/free-flow, clamped to [0.3, 1.0]) that re-times a route's per-edge times, with the estimate badge until a corridor has 5 learned samples (P-SAFE-07)
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-08T10:45:37Z
lease_expires_at: 2026-10-08T18:45:37Z
worktree: .worktrees/T-0320
branch: task/T-0320
exclusive: []
touches: [Sources/ScenicKit/, Tests/ScenicKitTests/, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-SAFE-07, P-PRIV-05]
reviewer: null
depends_on: [T-0294]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST in a dated Log entry: the plan's ETA honesty row and Traffic section (H3-8 x hour-of-week actual/free-flow ratio, EWMA, badge until >= 5 samples, learned ratio in [0.3, 1.0], departsAt shifts the hour-of-week); P-SAFE-07 and P-PRIV-05 (learned speeds have no Codable conformance, never leave the device) as written in pins/PINS.yaml; where an H3-8 cell id comes from without a Package.swift change (Sources/Telemetry holds the H3 builder; ScenicKit may not import it unless the root Package.swift already allows it - rule it, never edit Package.swift here); what per-edge time the app holds today (PlanResponse / PlanPreview etaIsEstimate) and how the learned ratio reaches the preview"
  - "TrafficProvider protocol + LearnedCorridorSpeeds: record(cell, hourOfWeek, actualSeconds, freeFlowSeconds) and retime(edges, departsAt) by full equality over a table: 0 / 4 / 5 / 6 samples (badge on through 4, off at 5 exactly), EWMA alpha ruled and tested at its first and second update, ratio clamp at 0.3 and 1.0 with nextafter on both sides, NaN / infinite / zero / negative inputs refused without changing state, hour-of-week wrap (Sunday 23:00 -> Monday 00:00) and departsAt crossing an hour boundary mid-route if ruled"
  - "The learned type has no Codable/Encodable conformance and no path into ScenicAPIClient or Telemetry - a source guard anchored on a whitelist of the identifier's sites (CLAUDE.md), seen red then green; P-SAFE-07 and P-PRIV-05 bind the new tests by name (quoted strings per memory pins-yaml-strict)"
  - "Digest rows for new Sources files; a mutation population with a literal floor, at least three entries MISSED before and CAUGHT by name after (the 5-sample bound, a clamp bound, the EWMA weight)"
---
## Brief

Plan, ETA honesty + Product invariants: "ETAs show the *estimate · no traffic data* badge until a corridor has >= 5
learned samples." M7 exit: "badge gone after 5 drives". The paid flow source (TomTom) is V1.1 behind the same
TrafficProvider protocol; this task is the on-device learner only, Linux-tested. The app wiring (feeding completed
drive legs from DriveSession into record, and retime into the preview) is a follow-up task once T-0317 lands.

## Log
- 2026-10-08T10:45:25Z filed by agent/claude-opus-5 (orchestrator) from the milestone gap map (M7 corridor learner).
- 2026-10-08T10:45:37Z claimed by agent/claude-opus-5; lease until 2026-10-08T18:45:37Z
- 2026-10-08T10:48:29Z MEASURE then RULE (agent/claude-opus-5, before any code).
  MEASURED. (a) The plan's ETA honesty row (line 55): "Learned corridor speeds on-device (H3-8 x hour-of-week
  actual/free-flow ratio, EWMA) + `TrafficProvider` protocol with a paid flow source slot (TomTom Flow) in V1.1.
  *estimate · no traffic data* badge until >=5 samples"; Problem A step 5 (line 119): "`TrafficProvider` re-times
  per-edge `details=time` -> displayed ETA (badge until learned). `departsAt` shifts the hour-of-week ratio and the
  twilight math only"; acceptance table (line 227): "learned ratio in [0.3, 1.0]"; the source tree (line 160) puts
  "Traffic (TrafficProvider, LearnedCorridorSpeeds)" in ScenicKit; line 189 "learned speeds never leave the
  device". (b) pins/PINS.yaml: P-PRIV-05 exists ("learned speeds have no `Codable` conformance"; its
  why_no_test_catches_it says "the learned-speed Codable ban stays" NOT ASSERTED); P-SAFE-07 has NO row in
  PINS.yaml at all (`grep -rn P-SAFE-07 pins/ ops/` = 0 hits) - it exists only in the plan's pin table (line 248:
  "*estimate* badge until >=5 samples | unit + snapshot | linux+mac"); named-tests.json has no P-SAFE-07 key.
  (c) Root Package.swift: target ScenicKit has NO dependencies; Telemetry has none either ("no dependency on
  ScenicKit"). Sources/Telemetry/H3Cell.swift is resolution 5 ONLY (`public static let resolution = 5`, "no public
  initializer from an index"), and H3IndexBuilder is internal. (d) The app holds NO per-edge time today:
  PlanResponse carries `etaSeconds`, `fastestEtaSeconds`, `etaIsEstimate` ("always true from the server") and the
  route's coordinates, no `details=time`; PlanPreview has `etaIsEstimate` and `showsEstimateBadge { etaIsEstimate }`.
  (e) `grep -rn "TrafficProvider|LearnedCorridor|CorridorRatio|CorridorSlot|RetimedRoute" Sources apps Tests ops`
  = 0 hits: no site exists before this task.
  RULINGS.
  R1 (cell id, no Package.swift change). ScenicKit may not import Telemetry (no dependency declared) and Telemetry
  makes only resolution-5 cells. The learner therefore keys on an opaque `CorridorCell(index: UInt64)` the CALLER
  supplies - the H3-8 index as uber/h3 spells it; ScenicKit neither computes nor validates H3. Making a res-8 cell
  (Telemetry's builder generalised, or a port beside the app wiring) is the follow-up wiring task's, not this one.
  R2 (the ratio). "actual/free-flow ratio" in [0.3, 1.0] is a SPEED ratio: one observation is
  freeFlowSeconds / actualSeconds (traffic only slows; 1.0 = free flow, 0.3 = the floor), clamped to [0.3, 1.0]
  per observation BEFORE the EWMA, so the EWMA, a convex combination, stays inside. A retimed edge is
  freeFlowSeconds / ratio.
  R3 (EWMA). alpha = 0.25 (exact in binary, so full-equality tests need no tolerance). The first sample SEEDS the
  ratio (ratio = observation); every later one is ratio' = (1 - 0.25) * ratio + 0.25 * observation.
  R4 (refusals). record refuses - returns false and leaves the whole store unchanged (compared with ==) - when
  either seconds value is NaN, infinite, zero or negative. An out-of-range hour cannot be built: HourOfWeek(_:) is
  failable over 0...167 (bounds -1, 0, 167, 168 tested).
  R5 (hour-of-week). Monday 00:00 = 0 ... Sunday 23:00 = 167, in the learner's TimeZone (an init argument: rush hour
  is local), gregorian calendar; Sunday 23:xx -> 167 and Monday 00:xx -> 0 (the wrap).
  R6 (departsAt mid-route - ruled IN). Each edge's slot is the hour-of-week of the instant the car ENTERS it:
  departsAt + the sum of the previous edges' RETIMED seconds (not free-flow), so a route crossing an hour boundary
  reads the next hour's ratio from that edge on.
  R7 (badge, P-SAFE-07). A slot (cell, hour-of-week) is LEARNED at >= 5 samples. retime uses the learned ratio only
  on a learned slot; an unlearned edge keeps its free-flow seconds. The result's isEstimate is true unless EVERY
  edge's slot is learned; an empty route is an estimate. Table 0 / 4 / 5 / 6 samples: badge on at 0 and 4, off at 5
  and 6, edge seconds free-flow at 0 and 4, freeFlow/ratio at 5 and 6.
  R8 (protocol). `TrafficProvider` is `retime(_:departsAt:) -> RetimedRoute` - what the V1.1 flow source also
  answers; `record` belongs to the learner only (a flow feed does not learn from the device).
  R9 (privacy, P-PRIV-05). LearnedCorridorSpeeds, CorridorSlot, CorridorRatio and RetimedRoute declare no
  Codable/Encodable/Decodable conformance. Held two ways: a ScenicKit test casting each metatype to Encodable.Type
  and Decodable.Type (bound by name in P-PRIV-05), and a source guard ops/lib/check-learned-speeds-sites (whole-line
  WHITELIST, //-leading lines dropped only, per memory source-guards-fail-closed) over every *.swift under Sources/
  and apps/: every line naming one of those identifiers or TrafficProvider must be an approved (file, line) pair,
  all in Sources/ScenicKit/Traffic/ - so a conformance line, an extension, a typealias or any use in
  ScenicAPIClient or Telemetry is red by name. It runs in P-PRIV-05's assertion.
  R10 (how it reaches the preview). Not wired here (Brief: a follow-up once T-0317 lands). PlanPreview stays as is;
  the follow-up feeds DriveSession legs to record and replaces etaIsEstimate with RetimedRoute.isEstimate. Per-edge
  free-flow times do not exist on the device yet (d), so that task also needs `details=time` from the Worker.
  R11 (pins). P-SAFE-07 gets a new PINS.yaml row bound by name (swift key) to the badge table test; P-PRIV-05's swift
  filter and tests widen to the Codable test, its assertion runs the guard first. Quoted strings (pins-yaml-strict).
- 2026-10-08T11:21:43Z RED then GREEN (agent/claude-opus-5). Tests first, against the shipped API with stubbed
  bodies (record `false`, retime free flow + isEstimate true, HourOfWeek.of `HourOfWeek(0 * day)!`):
  `swift test --scratch-path .../.build/t320 --filter "LearnedCorridorSpeedsTests|HourOfWeekTests|LearnedSpeedsPrivacyTests"`
  -> "Test run with 9 tests in 3 suites failed after 0.021 seconds with 123 issues"; FAILED by name: "the estimate
  badge: on at 0 and 4 samples, off at 5 and 6, and on whenever another edge is unlearned" (72 issues), "an empty
  route is an estimate with no edges", "the EWMA: the first sample seeds the ratio, the second moves it by alpha
  0.25", "the ratio clamp at 0.3 and 1.0, one ulp either side of each bound", "NaN, infinite, zero and negative
  times are refused and change nothing", "departsAt: an edge entered after Sunday 23:59 reads Monday 00:00's ratio,
  and the hour shifts the ratio", "Sunday 23:00 is 167 and wraps to Monday 00:00 = 0; the zone decides the hour".
  Passing against the stubs, by design: "HourOfWeek(_:) holds 0...167 ..." (the failable init is the type, not a
  body) and "no learned-speed type is Encodable or Decodable" (seen red below). With the bodies (commit a146e897):
  "Test run with 9 tests in 3 suites passed after 0.007 seconds."
  SOURCE GUARD ops/lib/check-learned-speeds-sites.py: whitelist absent -> "REFUSING - the whitelist
  check-learned-speeds-sites.txt is missing or empty" exit 2; whitelist written from --print-sites (13 sites, all in
  Sources/ScenicKit/Traffic/, read line by line) -> "ok - 13 sites, every one approved, in 5 files" exit 0;
  --prove-red -> "PROVE-RED OK: 8 of 8 rows red by name, control 0" (an extension declaring Codable, the
  declaration gaining Encodable, CorridorRatio gaining Codable, ScenicAPIClient taking the learner, Telemetry
  aliasing a slot, the app holding a RetimedRoute, a code line with a trailing comment, an approved line repeated).
  LIVE TREE: `Codable` added to CorridorRatio's declaration -> guard "REFUSED site not on the whitelist: ...
  public struct CorridorRatio: Equatable, Sendable, Codable {" + "approved site missing", exit 1, and the test
  "no learned-speed type is Encodable or Decodable" recorded 2 issues (CorridorRatio is Encodable / Decodable);
  restored -> guard ok exit 0.
  DIGESTS: `bash ops/lib/check-safety-disclaimer` refused "root: added Sources/ScenicKit/Traffic/CorridorCell.swift
  ... TrafficProvider.swift" until the eight rows were added to [PINNED_ROOT_SOURCES]; then exit 0 ("226 root +
  pbxproj file(s) (-linked)").
- 2026-10-08T12:06:49Z POPULATION and BINDINGS (agent/claude-opus-5). ops/mutate/traffic.py (traffic_mutations.py
  MIN_MUTATIONS = 29, MIN_EQUIVALENT = 1; DRIVERS + COVERED_FLOOR gain it; TrafficProvider.swift allowlisted as a
  one-method protocol). --prove-floor: "FLOOR PROOF OK: 7 of 7 arms refused and the control did not".
  MISSED BEFORE: `python ops/mutate/traffic.py --prove-vacuity --only 1,5,9,10,13,28` (the three test files
  replaced by empty suites) -> "MISSED 1 learned at 4 samples", "MISSED 5 alpha 0.3", "MISSED 9 the floor one ulp
  lower", "MISSED 10 the ceiling one ulp higher", "MISSED 13 a zero actual time accepted", "MISSED 28 CorridorRatio
  is Codable"; "VACUITY PROOF OK: with the 3 test file(s) emptied, caught=0 (need 0) and MISSED=6 of 6".
  CAUGHT AFTER, by name: `python ops/mutate/traffic.py` -> "1 learned at 4 samples by: the estimate badge: on at 0
  and 4 samples, off at 5 and 6, ..."; "5 alpha 0.3 by: the estimate badge ... | the EWMA: the first sample seeds
  the ratio, the second moves it by alpha 0.25"; "9 the floor one ulp lower" and "10 the ceiling one ulp higher" by
  "the ratio clamp at 0.3 and 1.0, one ulp either side of each bound"; "13 a zero actual time accepted by: NaN,
  infinite, zero and negative times are refused and change nothing"; "28 CorridorRatio is Codable" and "29
  RetimedRoute is Codable" by "no learned-speed type is Encodable or Decodable"; the EQUIVALENT E1 (the clamp
  applied ceiling first) MISSED as required. That run printed "caught by the test that names it: 28 of 29 (wrong
  killer 1 ...)": entry 25 (a slot keeps no hour) named the EWMA test too, which cannot see it - the EWMA test's
  expected slot is built with the same mutated CorridorSlot init, so both sides lose the hour; only the departsAt
  test was red. Ruled: entry 25 names that test alone (f3933863's successor commit); `--only 25` -> "MUTATE OK
  caught=1/1". With the other 28 unchanged, the population stands at 29 of 29 caught by name.
  BINDINGS: `run-named-tests.py P-SAFE-07` -> "NAMED P-SAFE-07 passed=8/8"; badgeAtFiveSamples() renamed ->
  "RED ...LearnedCorridorSpeedsTests/badgeAtFiveSamples(): MISSING - no test of this name ran", "NAMED P-SAFE-07
  passed=7/8" exit 1; restored. P-PRIV-05's swift list gains
  ScenicKitTests.LearnedSpeedsPrivacyTests/noLearnedTypeIsCodable() and its assertion runs the site guard first.
- 2026-10-08T12:19:29Z ACCEPTANCE re-run on the merged head 42671b53 (origin/main ef4d937b..07ee792b merged, T-0317
  in; named-tests.json conflict resolved as the union - main's P-NAV-01 and P-SAFE-09, this branch's P-PRIV-05 and
  P-SAFE-07; the digest rows and DRIVERS/COVERED_FLOOR auto-merged with both sides kept).
  1 MEASURE/RULE: the 10:48:29Z entry above, before any code.
  2 `swift test --filter "LearnedCorridorSpeedsTests|HourOfWeekTests|LearnedSpeedsPrivacyTests"` exit 0, "Test run
  with 9 tests in 3 suites passed"; `run-named-tests.py P-SAFE-07` exit 0, "NAMED P-SAFE-07 passed=8/8".
  3 `check-learned-speeds-sites.py` exit 0, "ok - 13 sites, every one approved, in 5 files" (red: 11:21:43Z entry).
  4 `bash ops/lib/check-safety-disclaimer` exit 0 ("232 root + pbxproj file(s)"); `check-mutate-population.py`
  exit 0, "every added module is covered or allowlisted; the floor of 135 holds"; population 29/29 by name
  (12:06:49Z entry). Also `check-line-cap` exit 0 ("463 Swift files ... none over 300 lines"), `check-pins-yaml.py`
  exit 0 ("pins=47 fields=379"), `ops/queue-check` exit 0 ("QUEUE OK (312 tasks)").
  OPEN (not this task's acceptance): the app wiring - an H3-8 cell for the caller, DriveSession legs into record,
  retime's isEstimate into PlanPreview, `details=time` per edge from the Worker (R1, R10) - is the Brief's follow-up.
- 2026-10-08T13:19:06Z PRE-REVIEW SURVIVORS M1 and M3 CLOSED BY CLASS (agent/claude-opus-5). The fable pass ran
  three mutants against 4d0cc889; two SURVIVED (BLOCKING): M1, the badge counted per CELL (the sum of a cell's
  samples over every hour) instead of per (cell, hour) slot (R7) - no row taught one cell at two hours with one of
  them under 5; M3, retime read the hour in UTC instead of the learner's timeZone (R5) - every learner in
  LearnedCorridorSpeedsTests was built with `Self.utc`, and population entry 19 mutates HourOfWeek.of, not the
  pass-through in retime. RULED: both are test gaps, the shipping code is right; no Sources/ file changes, so no
  digest row moves. The classes, as population entries (MIN_MUTATIONS 29 -> 33): 30 the badge counts a cell over
  every hour (M1 itself), 31 the badge counts any learned hour of the cell, 32 retime reads the hour in UTC (M3
  itself), 33 retime reads the device's zone (TimeZone.current).
  MISSED BEFORE (26ca4e60, tests unchanged; 13:03:25Z) `python ops/mutate/traffic.py --only 30,31,32,33` ->
  "MISSED 30 the badge counts a cell over every hour exit=0 no test objected", "MISSED 31 the badge counts any
  learned hour of the cell", "MISSED 32 retime reads the hour in UTC"; 33 was caught on this box only because its
  zone is America/Los_Angeles - on a UTC box (CI) it is 32 exactly; "MUTATE FAILED caught=1/4".
  KILLER ROWS, crossed into the existing tables (table rows as functions of input): badgeAtFiveSamples gains a
  third dimension - both cells also taught 0, 1 or 5 times at hour 9, which no edge enters, each at the other
  cell's ratio - and its expected answer stays a function of (n, otherLearned) only; hourBoundaryMidRoute runs
  every expectation under Self.zones = UTC, UTC-7 and UTC+5:30, the departure moved by the zone's offset so the
  local wall clock (Sunday 23:58:30) is the same in each. 117 -> 135 lines.
  CAUGHT AFTER (1df940c3; 13:12:56Z) `python ops/mutate/traffic.py --only 30,31,32,33` -> "caught 30 ... by: the
  estimate badge: on at 0 and 4 samples, off at 5 and 6, and on whenever another edge is unlearned", "caught 31
  ... by: the estimate badge ...", "caught 32 retime reads the hour in UTC by: departsAt: an edge entered after
  Sunday 23:59 reads Monday 00:00's ratio, and the hour shifts the ratio", "caught 33 ... by: departsAt ... | the
  estimate badge ..."; "caught by the test that names it: 4 of 4"; "MUTATE OK caught=4/4". `--prove-floor` ->
  "FLOOR PROOF OK: 7 of 7 arms refused and the control did not". P-SAFE-07's quote of the floor reads 33.
- 2026-10-08T13:59:36Z rv1-t0320 B1 RULED BEFORE CODE (agent/claude-opus-5). The reviewer's mutant - the
  observation clamp removed and the clamp applied instead to the STORED ratio at both record sites (the seed and the
  EWMA) - survives the 9 tests at ed247a66. R2 stands (each observation clamped BEFORE the EWMA); the shipping code is
  right, this is a test gap; no Sources/ file changes, so no digest row moves. CLASS: ewmaFirstAndSecondUpdate becomes
  the cross product {first observation in range, below 0.3, above 1.0} x {second in range, below, above}, each
  row's whole slot table after each record compared to 0.75 * clamp(o1) + 0.25 * clamp(o2), clamp written in the
  test from the literals 0.3 and 1.0. Population (MIN_MUTATIONS 33 -> 35): 34 the clamp after the EWMA at both
  record sites (the reviewer's mutant), 35 the clamp after the EWMA only (the seed unclamped).
  DISAGREEMENT RULED (the Brief's meta-check "no row's expected value is the same under clamp-after-EWMA"): it is
  unsatisfiable for 5 of the 9 rows. With c1 = clamp(o1) in [0.3, 1.0] the mutant stores clamp(0.75 c1 + 0.25 o2).
  If o2 is in range, a convex combination of two values in [0.3, 1.0] stays in it and the clamp is the identity:
  equal (3 rows). If o2 is below 0.3 and c1 is 0.3, both store 0.3; symmetrically above with c1 = 1.0 (2 rows). So
  the meta-check is a PARTITION over the input, computed per row from both functions: a row differs under
  clamp-after-EWMA IFF its second observation is out of range AND its first is not clamped onto that same bound
  (4 rows: in/below, in/above, below/above, above/below). Every row is a function of its input and none is ignored:
  a row on the wrong side of the predicate fails the meta-check. The reviewer's witnesses are rows: in (120/60) then
  above (1/60) -> 0.625, mutant 1.0; above (30/60, kept 1.0 = the witness's 60/60) then below (6000/60) -> 0.825,
  mutant 0.7525.
