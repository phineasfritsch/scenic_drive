---
id: T-0249
title: ScenicKit RoadTrip - the day splitter (A->B over N days, +40% scenic budget, max drive and max miles per day, 2-4 stops a day, an overnight town per boundary) as a pure Foundation module over a recorded route
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-05T05:10:08Z
lease_expires_at: 2026-10-05T15:10:08Z
worktree: .worktrees/T-0249
branch: task/T-0249
exclusive: []
touches: [Sources/ScenicKit/RoadTrip/, Tests/ScenicKitTests/RoadTrip/, Tests/Fixtures/roadtrip/, ops/mutate/, ops/lib/mutate_population_table.py]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "RULED in the Log before code from the plan's 'Road trip' section: the inputs (a route's per-edge times/distances and candidate towns/stops), the forward pass over day start/end, max drive time and max miles per day, 2-4 corridor stops per day, the overnight town = lodging within 15 km of the boundary, and the +40% budget; Foundation only, one type per file, <= 300 lines"
  - "tests over a recorded fixture (a long LA -> Bay Area or LA -> Big Sur route, recorded or synthetic and ruled) assert the WHOLE day plan by exact equality (day boundaries, per-day minutes and km, stops, overnight towns), plus the properties: no day exceeds its max drive or max miles, every day has 2-4 stops when the corridor offers them, an honest 'no lodging within 15 km' outcome when it does not; RED first by name"
  - "the new numeric module ships its ops/mutate population with a literal floor registered in ops/lib/mutate_population_table.py; MUTATE OK and --prove-vacuity quoted"
---
## Brief

Milestone survey (2026-10-04): M5's road trip has no engine. This is the pure engine half; /trip and the day-list UI
follow.

## Log
- 2026-10-05T05:06:53Z filed by agent/claude-opus-5 (orchestrator) from the milestone survey.
- 2026-10-05T05:10:08Z claimed by agent/claude-opus-5; lease until 2026-10-05T15:10:08Z
