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
touches: [Package.swift, Sources/Telemetry/, Tests/TelemetryTests/, ops/mutate/, ops/lib/mutate-population-allowlist.json, ops/lib/mutate_population_table.py]
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
- 2026-10-05T18:38:18Z RULINGS (agent/claude-opus-5, owner), before any code. Disagreements between plan :148, the Brief, the acceptance block and the tree:
  - R1 "14 events" vs the plan's list of fifteen names. The plan writes `paywall_shown/converted` as ONE slot of the fourteen. TelemetryEvent has EXACTLY 14 cases; the fourteenth is `paywall(PaywallStep)` with PaywallStep {shown, converted}. The wire keeps the plan's two names (`paywall_shown`, `paywall_converted`) so ops/funnel can count each, i.e. 14 cases, 15 wire names. TelemetryEventKind (CaseIterable, 14 cases) is the closed list the encoding table ranges over; a test pins `allCases.count == 14`, a row per kind, and an exhaustive switch over TelemetryEvent in the test file (no `default`) so a new case is a compile failure of the suite.
  - R2 Workers Analytics Engine shape. AE's `writeDataPoint({indexes, blobs, doubles})` - indexes max 1 (the sampling key), blobs/doubles positional (blob1.., double1..). TelemetryDataPoint is that object, Encodable to exactly those three keys, with a FIXED WIDTH so SQL over blobN/doubleN never shifts by event: indexes = [wire name]; blobs = [wire name, label, h3 cell or ""]; doubles = [v1, v2] (0 where unused). AE stamps its own `timestamp` server-side, so the payload carries NO time at all - stricter than P-PRIV-05's "nothing finer than the hour". Every case's whole encoded value is pinned by exact equality (full-equality oracle); the JSON of one point is pinned byte-for-byte.
  - R3 Where the H3 cell rides. The plan says the payload is "feature ids, H3-5 cell, durations" without naming the event. Only `planRequested(feature:budgetMinutes:origin:)` carries a cell - the origin of the plan, one cell per user action, matching "one coordinate per action". No other case carries any location.
  - R4 Payload types (the P-PRIV-05 whitelist). Associated values may only be: PlanFeature, PlanResultKind, HandoffApp, SurpriseNotThisReason, PaywallStep (closed String enums - no free-form String), CompletionPercent (whole percent clamped 0...100), Int (budget minutes, deviation count, corpus version), Bool (prettier), H3Cell. No Coordinate, no Double, no Date, no String. A Mirror-based test walks every row's associated values and refuses BY CASE NAME any type outside that list. Telemetry imports Foundation only and does NOT depend on ScenicKit: it never sees a Coordinate type, so the cell factory takes two Doubles and returns only the cell.
  - R5 H3 is REAL H3, not a stand-in. Ported from uber/h3 v4.1.0 (src/h3lib/lib/faceijk.c, coordijk.c, baseCells.c, h3Index.c; Apache-2.0, fetched raw from github.com/uber/h3 at tag v4.1.0) for latLngToCell at a FIXED resolution 5 only: closest icosahedron face, gnomonic hex2d, ijk+, aperture-7 up-walk, faceIjkBaseCells lookup, pentagon rotations. The reference is uber/h3's own test input tests/inputfiles/rand05centers.txt at v4.1.0 (5000 rows `h3index lat lng`, sha256 8bf6e8d5597ea7d72a931e239bb91bc1184510abc82c92e789cfee1119791066, all 16 res-5 hex prefixes 850..85f present) - copied UNEDITED into Tests/TelemetryTests/Fixtures/ and every row asserted equal (>= 10 is the floor; 5000 is the population). The first three rows as published: `850dab63fffffff 67.194014 191.598258`, `850336b7fffffff 87.372197 166.176925`, `85440d83fffffff 27.350796 272.064443`. If the port cannot meet the 5000 within budget the fallback ruling (a coarser equal-area grid, never called H3) is taken here in a dated entry, not silently.
  - R6 Touches widened by one path: ops/lib/mutate_population_table.py. A new driver under ops/mutate/ with a `__main__` is refused by P-PROC-06 until it is in DRIVERS, and its subjects must join COVERED_FLOOR; both tables live in that file, which the Brief's touches missed.
  - R7 Mutation population: ops/mutate/telemetry.py (+ _mutations, _run, the straightline.py family shape) over the numeric files - the H3 port and CompletionPercent and the encoder; the closed payload enums and the data-point struct compute nothing and are allowlisted with one reason each.
