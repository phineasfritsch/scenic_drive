---
id: T-0355
title: The app emits the closed telemetry enum - a ScenicAPIClient TelemetryClient posts to /telemetry and every one of the 14 TelemetryEventKind cases has exactly one shipping emit site, so ops/funnel has a data source
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/ScenicAPIClient/, Sources/Telemetry/, Tests/ScenicAPIClientTests/, Tests/TelemetryTests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-PRIV-05]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Survey 2026-10-10 (M5 exit "Telemetry + ops/funnel"): the enum exists (Sources/Telemetry/TelemetryEventKind.swift,
T-0265) and the Worker ingests it (services/api/src/telemetry.ts, T-0279), but Sources/ScenicAPIClient has no
/telemetry client and apps/ios imports Telemetry only for H3Cell (LiveSurpriseLedger.swift). Nothing emits, so
ops/funnel (T-0284/T-0285) reads nothing.

MEASURE FIRST: the Worker's /telemetry request shape and refusals (quote telemetry.ts), the 14 cases and their
payloads, and where in the app each event's moment happens today (file:line per case). RULE: one client (fail-quiet:
telemetry never blocks or errors a user action; bounded queue, dropped on failure), payload exactly the plan's
"feature ids, H3-5 cell, durations only" (never a coordinate, never more than one cell per action - CLAUDE.md
privacy invariant), one emit site per case. Tests through the shipping client with exact request-body equality; a
whitelist guard that every emit site is approved and every case has one (fail-closed, red then green). Every apps/ios
Swift edit needs the P-SAFE-03 digest re-approval in ops/lib/check-safety-disclaimer-pinned; if the permission
classifier refuses it, ship the Linux slice and stop the app half with that in stillOpen. post_drive_answer's UI is
T-0358; this task wires the other 13 and the client.

## Log
- 2026-10-10T03:20:00Z filed by agent/claude-opus-5 (orchestrator) from the 2026-10-10 milestone survey (top-1).
