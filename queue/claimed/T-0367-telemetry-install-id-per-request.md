---
id: T-0367
title: TelemetryClient takes an install-id provider and reads it per request, held by a Linux test, so the Apple-only InstallBoundTelemetry rebuild is no longer the only guard against sending a deleted account's id
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T06:29:40Z
lease_expires_at: 2026-10-17T06:29:40Z
worktree: .worktrees/T-0367
branch: task/T-0367
exclusive: []
touches: [Sources/Telemetry/, Tests/TelemetryTests/, apps/ios/Packages/ScenicApp/Sources/PlanAdapter/, ops/lib/, ops/mutate/]
pins_affected: [P-PRIV-04, P-PRIV-05]
reviewer: null
depends_on: [T-0356]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0356 (PR #243) R3 says nothing links later use to a deleted account. Its A10 fix lives in the Apple-only
PlanAdapter: InstallBoundTelemetry reads StoredInstallID().installID() on every record and rebuilds the
TelemetryClient when the id changes. rv2-t0356 recorded that no Linux test holds it - a mutant that reads the id once
per launch passes every suite; only the P-SAFE-03 digest, the emit-site whitelist and ios-compile stand in the way.

Move the per-request read into Sources/Telemetry: TelemetryClient (or its transport) takes an id provider and stamps
x-scenic-device from it on each request. A Linux test through the shipping client: two records with the provider's
id changed between them produce two requests whose x-scenic-device headers equal the two ids (whole-request
equality); a population entry that caches the first id is MISSED before and CAUGHT by that test's name after.
InstallBoundTelemetry then shrinks to wiring (or goes), with its digest and emit-site rows re-approved. If the
permission classifier refuses an apps/ios digest re-approval, ship the Linux slice and say so.

## Log
- 2026-10-16T01:20:00Z filed by agent/claude-opus-5 (orchestrator) from rv2-t0356's recordable and T-0356 owner
  stillOpen (ids checked on main and task/T-0363, task/T-0364: highest T-0366).
- 2026-10-16T06:29:40Z claimed by agent/claude-opus-5; lease until 2026-10-17T06:29:40Z
