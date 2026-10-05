---
id: T-0265
title: Sources/Telemetry - the plan's closed enum of 14 events, coarse payloads only (feature ids, H3-5 cell, durations), encoded by exact equality, never a coordinate
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-05T18:21:57Z
lease_expires_at: 2026-10-06T06:21:57Z
worktree: .worktrees/T-0265
branch: task/T-0265
exclusive: [package-swift]
touches: [Package.swift, Sources/Telemetry/, Tests/TelemetryTests/, ops/mutate/, ops/lib/mutate-population-allowlist.json]
pins_affected: [P-PRIV-05]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "a root-package target Telemetry (Foundation only) with TelemetryEvent, a closed enum of EXACTLY the plan's 14 events - plan_requested(feature, B), plan_result(kind), preview_shown, handoff_tapped(app), drive_started, drive_completed(pct, deviations), drive_abandoned(pct), post_drive_answer(prettier), surprise_shown, surprise_not_this(reason), surprise_take_me_there, surprise_arrived, corpus_activated(v), paywall_shown / paywall_converted (rule how 14 counts these) - each encoded to the Workers Analytics Engine data-point shape the author rules, tested by EXACT equality of the whole encoded value per case (a table over allCases that fails when a case is added without a row)"
  - "P-PRIV-05: no case carries a Coordinate, a Double latitude/longitude, a timestamp finer than the hour, or a free-form String; the only location is an H3 resolution-5 cell id produced by a Foundation-only H3 encoder (or a ruled coarser stand-in) whose output is pinned by equality against >= 10 published H3 reference cells; a test refuses by name any case whose associated values include a type outside a whitelist"
  - "a mutation population under ops/mutate/ with a literal floor; RED first by name; swift test count quoted"
---
## Brief

Plan 'Runtime lifecycles - Telemetry': Sources/Telemetry (Foundation, Linux), closed enum of 14 events, payload =
feature ids, H3-5 cell, durations only -> Workers Analytics Engine; ops/funnel reads it later. M5 lists Telemetry
as missing (milestone gap map). Root package, so Package.swift (exclusive package-swift). No network code here -
the sender is a later task.

## Log
- 2026-10-05T18:19:47Z filed by agent/claude-opus-5 (orchestrator) from the milestone gap map (M5 telemetry).
- 2026-10-05T18:21:57Z claimed by agent/claude-opus-5; lease until 2026-10-06T06:21:57Z
