---
id: T-0340
title: The /trip and /loop answers carry the route's hazard runs, and the trip and loop cards render them from HazardCopy - today only /plan and /reroute report surface and road_access runs
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/api/src/, services/api/test/, Sources/ScenicAPIClient/, Sources/ScenicKit/, Tests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/check-safety-disclaimer-linked-digests.txt]
pins_affected: [P-SAFE-02]
reviewer: null
depends_on: [T-0339]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0339 M2 (measured at bdb77ca6): trip.ts, loop.ts, tripPlanner.ts and loopPlanner.ts never call `hazardsOf`, and
TripResponse / TripResponseDay / LoopResponse decode no hazards - so a trip or loop over a destination-only or gravel
stretch tells the driver nothing, while the same stretch on /plan does. MEASURE FIRST (which router paths the trip
days and the loop are built from, whether their details already carry surface / road_access), then the acceptance:
every day / the loop carries its runs, the readers decode them fail-closed, and TripItineraryCard / LoopPreviewCard
render them through HazardCopy (T-0339's closed table), never a raw key. Worker PRs conflict on the enumerating
tables - one at a time.

## Log
- 2026-10-09T08:33:30Z filed by agent/claude-opus-5 from T-0339 R4.
