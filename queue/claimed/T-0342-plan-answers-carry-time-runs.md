---
id: T-0342
title: The /plan and reroute answers carry GraphHopper's per-edge time runs, and ScenicAPIClient hands them to the preview, so RetimedPreview can clear the estimate badge (T-0325 R2 follow-up)
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-09T14:53:12Z
lease_expires_at: 2026-10-10T00:53:12Z
worktree: .worktrees/T-0342
branch: task/T-0342
exclusive: []
touches: [services/api/src/, services/api/test/, Sources/ScenicAPIClient/, Sources/ScenicKit/, Tests/ScenicAPIClientTests/, Tests/ScenicKitTests/, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-SAFE-07]
reviewer: null
depends_on: [T-0325, T-0333]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Filed by T-0325 (R2, R7). T-0325 ruled that per-edge free-flow times are GraphHopper's `details=time`, never a
length split of eta_s (its Log has the worked example: a length split makes a free-flow drive read 13 min against a
true 10 and clears the badge on it). The device half ships in T-0325: CorridorTimeRun (from, to, whole ms),
CorridorRoute(route:timeRuns:) holding the runs to tile the drawn route edge for edge (tripPlanner.ts edgesOf's rule),
RetimedPreview.of(_:timeRuns:by:departsAt:). Today scenicPlanner.ts ROUTE_DETAILS has no `time` and
ScenicPlanResult carries eta_s only, so no preview has runs and the badge is always on (fails safe).

The claimer MEASURES then RULES: adding `time` to ROUTE_DETAILS changes every request-body equality test of /plan,
/loop and reroute (count them); the response field's name and shape (the chosen path's runs over route.coordinates,
whole ms); whether the reroute answer carries them too (DriveSession takes a reroute's line, CorridorClock stops
recording after one until it does); PlanResponse decode and PlanPreview's new field (ClientPlanner), refusals by full
equality; P-PRIV-05 is untouched (the runs come FROM the server). T-0333 is changing the Worker and ScenicAPIClient
now - merge it first (memory parallel-worker-prs-conflict).

## Log
- 2026-10-09T11:37:54Z filed by agent/claude-opus-5 (T-0325 owner) from T-0325 R2/R7.
- 2026-10-09T14:53:12Z claimed by agent/claude-opus-5; lease until 2026-10-10T00:53:12Z
