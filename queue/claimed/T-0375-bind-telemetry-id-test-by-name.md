---
id: T-0375
title: P-PRIV-05 binds everyRequestStampsTheProvidersCurrentID() by name, so deleting the per-request install-id test is caught, not only weakened inside the suite filter
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T09:15:21Z
lease_expires_at: 2026-10-17T09:15:21Z
worktree: .worktrees/T-0375
branch: task/T-0375
exclusive: []
touches: [ops/lib/named-tests.json, pins/PINS.yaml, queue/]
pins_affected: [P-PRIV-05]
reviewer: null
depends_on: [T-0367]
verify: [ops/check-pins]
acceptance: []
---
## Brief

T-0367 (PR #254) moved the per-request install-id read into Sources/Telemetry and added
TelemetryClientTests.everyRequestStampsTheProvidersCurrentID() (rows: same id, id changed after a post, id changed
while a post is in flight). It runs inside P-PRIV-05's named swift filter, but its NAME is not in
ops/lib/named-tests.json, so deleting it leaves `run-named-tests.py P-PRIV-05` green (T-0367 R4: pins/ was outside
touches). Bind it by name, re-approve whatever PINS.yaml digest or count P-PRIV-05 carries, and show the binding
red by deleting the test (run-named-tests reports it MISSING) then green.

## Log
- 2026-10-16T09:40:00Z filed by agent/claude-opus-5 (orchestrator) from T-0367 R4 / rv2-t0367 (ids checked on main
  and task/T-0318, task/T-0368: highest T-0374).
- 2026-10-16T09:15:21Z claimed by agent/claude-opus-5; lease until 2026-10-17T09:15:21Z
