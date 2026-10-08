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
