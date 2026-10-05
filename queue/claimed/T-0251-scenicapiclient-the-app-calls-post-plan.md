---
id: T-0251
title: ScenicAPIClient - the root-package client for the Worker's POST /plan (request built under the one-coordinate / 2-dp invariant, typed PlanError for every Worker failure), with a counting fake
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-05T11:45:00Z
lease_expires_at: 2026-10-05T23:45:00Z
worktree: .worktrees/T-0251
branch: task/T-0251
exclusive: [package-swift]
touches: [Package.swift, Sources/ScenicAPIClient/, Tests/ScenicAPIClientTests/]
pins_affected: [P-PRIV-05, P-COST-01]
reviewer: null
depends_on: [T-0175, T-0248]
verify: [ops/test, ops/check-pins]
acceptance:
  - "Sources/ScenicAPIClient (Foundation + URLSession only) builds the exact POST /plan body T-0248 ruled; a test asserts the encoded body by EXACT equality to a typed literal and that the client refuses to send a second coordinate or one with more than 2 decimals (P-PRIV-05)"
  - "every Worker response T-0248 can return (200, 429 quota with resetsAt, 503 kill switch, router failure, bad request) maps to one PlanError case (the plan's closed enum: quotaExhausted, planningPaused, routingOffline, noRoute, ...) - a test per status by name, over recorded Worker responses from T-0248's vitest fixtures"
  - "a counting fake (the plan's 'counting fake') counts requests per plan; RED first by name; swift test count quoted"
---
## Brief

Milestone survey 2026-10-04: M3/M4 need the app to call the Worker. Starts after T-0175 releases the package-swift lock.

## Log
- 2026-10-05T09:04:49Z filed by agent/claude-opus-5 (orchestrator) after PR #139 (T-0248) merged.
- 2026-10-05T11:42:53Z PROMOTED to ready/ by agent/claude-opus-5 (orchestrator): T-0175 (PR #142) and T-0248 (PR #139) merged; package-swift lock free. Note from T-0175: the root Package.resolved is gitignored and GRDB is declared outside Windows only - copy that package-manifest shape.
- 2026-10-05T11:45:00Z claimed by agent/claude-opus-5; lease until 2026-10-05T23:45:00Z
