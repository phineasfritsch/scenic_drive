---
id: T-0317
title: The drive session's decisions live in ScenicKit and are Linux-tested - off-route detection, reroute request (remaining pinned waypoints + same lambda, never bare O->D), offline rejoin mode with zero requests, and the >4.5 m/s motion gate - ready for the Ferrostar adapter (M7)
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-08T07:53:28Z
lease_expires_at: 2026-10-09T03:53:28Z
worktree: .worktrees/T-0317
branch: task/T-0317
exclusive: []
touches: [Sources/ScenicKit/, Tests/ScenicKitTests/, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-NAV-01, P-SAFE-06]
reviewer: null
depends_on: [T-0294]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST in a dated Log entry: the plan's Navigation section (off-route -> if online re-request /plan with the same lambda and the REMAINING pinned waypoints, never bare O->D; if offline keep guiding to rejoin the planned line, no request) and P-NAV-01 / P-SAFE-06 as written in pins/PINS.yaml; what /plan accepts today for a reroute (read services/api/src/plan.ts whitelist - if it cannot carry waypoints + lambda, rule the gap and file the Worker half; never widen the Worker here)"
  - "ScenicKit DriveSession: a pure state machine fed location fixes (coordinate, speed, timestamp) and connectivity; off-route = distance to the planned polyline above a ruled threshold for a ruled dwell; the reroute it asks for carries exactly the waypoints not yet passed and the same lambda (full equality); offline -> rejoin mode with zero requests; back online -> one reroute; table over every bound (threshold +/- nextafter, dwell edges, speed exactly 4.5 m/s) per memory range-checks-every-bound"
  - "Motion gate: above 4.5 m/s the session exposes only the one large action and voice; a full-equality table over speed bounds and over hysteresis if ruled"
  - "P-NAV-01 and P-SAFE-06 bind the new tests by name (PINS.yaml quoted strings, memory pins-yaml-strict); digest rows for new Sources files; a mutation population with a literal floor, three entries MISSED before and CAUGHT by name after"
---
## Brief

Plan, Navigation on the scenic path + M7. The Apple-side Ferrostar adapter (NavAdapter, the only importer of Ferrostar)
is a later task under the package-swift lock; this task puts every decision it will call into Linux-testable ScenicKit
first, so the adapter is a thin shell. Calm, minimal-distraction driving UI (memory owner-route-intent).

## Log
- 2026-10-08T07:53:18Z filed by agent/claude-opus-5 (orchestrator) from the milestone gap map (M7 navigation, logic half).
- 2026-10-08T07:53:28Z claimed by agent/claude-opus-5; lease until 2026-10-09T03:53:28Z
