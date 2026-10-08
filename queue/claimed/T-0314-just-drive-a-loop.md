---
id: T-0314
title: "Just drive a loop" in the app - a LoopClient for POST /loop, a loop sheet (start = here or a typed place, minutes dial), a preview of the loop with its retrace check, and handoff to Apple Maps with the loop's pinned waypoints
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-08T06:32:56Z
lease_expires_at: 2026-10-09T06:32:56Z
worktree: .worktrees/T-0314
branch: task/T-0314
exclusive: []
touches: [Sources/ScenicAPIClient/, Tests/ScenicAPIClientTests/, Sources/ScenicKit/, Tests/ScenicKitTests/, Sources/Handoff/, Tests/HandoffTests/, apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/ScenicDriveApp.swift, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-SAFE-03, P-ATTR-01, P-PRIV-05]
reviewer: null
depends_on: [T-0252, T-0294, T-0310, T-0311]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST in a dated Log entry: the shipped /loop request/response (services/api/src/loop.ts, loopRequest.ts: one start coordinate at 2 dp, minutes, vehicle), where the 'Just drive a loop' entry lives (the Surprise card's secondary action per the plan's UI list, and/or the home), how it composes without a Package.swift edit, and the free tier (plan: Loop 1/day free, unlimited paid - read the T-0272 tier seam; rule what the app shows when the Worker answers 429)"
  - "LoopClient: request body by full equality to a recomputation (one coordinate, 2 dp, minutes, vehicle); every Worker answer (200, 400, 422 region_unsupported, 429, 503 planning_paused/unavailable) mapped to one typed outcome by a table; no retries"
  - "A ScenicKit loop-sheet state machine with a full-equality transition table; the minutes dial bounded by the Worker's range at every bound (memory range-checks-every-bound); the disclaimer gate still blocks the first plan (P-SAFE-03 - counting transport 0 before acceptance)"
  - "Loop handoff builds one Apple Maps URL that starts and ends at the start with the loop's pinned waypoints (<= 9) by full equality; the preview sheet is full-height or gets a typed whole-line P-ATTR-01 approval; ios-compile + ios-screenshot pass; digests re-approved; a mutation population with a literal floor, three entries MISSED before and CAUGHT by name after"
---
## Brief

Plan, Features: "Loop | 'Just drive 45 minutes and come back' | 1/day free | Unlimited"; UI: the Surprise card offers
`Take me there` / `Just drive a loop`. The Worker /loop (T-0252) is shipped with the retrace check; the app has no loop
surface. Calm copy (memory owner-route-intent).

## Log
- 2026-10-08T05:02:38Z filed by agent/claude-opus-5 (orchestrator) from the milestone gap map (M5 loop UI).
- 2026-10-08T06:32:56Z claimed by agent/claude-opus-5; lease until 2026-10-09T06:32:56Z
