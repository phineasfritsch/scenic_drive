---
id: T-0358
title: After a drive the app asks "Prettier than your usual way?" once and records post_drive_answer - the funnel's answer stage
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/ScenicKit/, Tests/ScenicKitTests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: []
reviewer: null
depends_on: [T-0355]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Survey 2026-10-10: only the wire case exists (Sources/Telemetry/TelemetryEvent.swift post_drive_answer); no UI. The
plan: "Prettier than your usual way?" after a drive (paid: at drive_completed; free: at destination arrival via
region monitoring, else at next open) feeds W1/W4 and the Bradley-Terry tuning. Region monitoring needs a capability
(owner) - rule the free-tier trigger as "at next open after a handoff" if so.

MEASURE FIRST: where a drive completes in the app (DriveSession / drive screen) and what a handoff leaves behind.
RULE: when the question shows (once per drive, never during motion - P-SAFE-06's motion gate), the answer set, what is
sent (the telemetry case only, through T-0355's client), and dismissal. Tests on the ScenicKit model that decides
when to ask (a table over drive outcomes x tiers x motion). Every apps/ios Swift edit needs the P-SAFE-03 digest
re-approval; if refused, ship the Linux slice and say so.

## Log
- 2026-10-10T03:20:00Z filed by agent/claude-opus-5 (orchestrator) from the 2026-10-10 milestone survey (top-4).
