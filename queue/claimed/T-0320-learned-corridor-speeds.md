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
