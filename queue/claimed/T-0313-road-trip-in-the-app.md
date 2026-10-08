---
id: T-0313
title: Road trip in the app - a TripClient for POST /trip, a road-trip sheet (destination, days, daily limits), a day-by-day itinerary preview, and per-day "Open in Apple Maps" with that day's pinned waypoints
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-08T04:26:07Z
lease_expires_at: 2026-10-09T04:26:07Z
worktree: .worktrees/T-0313
branch: task/T-0313
exclusive: []
touches: [Sources/ScenicAPIClient/, Tests/ScenicAPIClientTests/, Sources/ScenicKit/, Tests/ScenicKitTests/, Sources/Handoff/, Tests/HandoffTests/, apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/ScenicDriveApp.swift, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-SAFE-03, P-ATTR-01, P-PRIV-05]
reviewer: null
depends_on: [T-0268, T-0249, T-0294, T-0311]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST in a dated Log entry: the shipped /trip request and response (services/api/src/trip.ts, tripRequest.ts, roadTrip.ts: one origin coordinate at 2 dp + a destination place id + days/limits + vehicle), the ScenicKit RoadTrip day splitter, how the app composes a new sheet without a Package.swift edit (as T-0294/T-0306 did) and with ScenicAPIClient imported only in PlanAdapter, and the free-vs-paid split (plan: preview free, full itinerary paid - read the T-0272 tier seam; if the app has no paid check yet, rule what the free preview shows)"
  - "TripClient: request body by full equality to a recomputation; every Worker answer (200, 400, 404 unknown_place, 422 region_unsupported, 429, 503 planning_paused/unavailable) mapped to one typed outcome by a table; no retries"
  - "A ScenicKit trip-sheet state machine (destination chosen -> planning -> itinerary | failed) with a full-equality transition table; the disclaimer gate still blocks the first plan (P-SAFE-03 - counting transport 0 before acceptance)"
  - "Per-day handoff builds one Apple Maps URL per day from that day's waypoints (Handoff AppleMapsDirections, <= 9 waypoints, the repeatable waypoint form) by full equality; a day with more stops than the URL allows is split by a ruled rule"
  - "The itinerary sheet is full-height or gets a typed whole-line P-ATTR-01 approval; ios-compile + ios-screenshot pass on the head; digests re-approved; a mutation population with a literal floor, three entries MISSED before and CAUGHT by name after"
---
## Brief

Plan, Features: "Road trip | A->B over N days, +40% scenic budget, day splitter, 2-4 stops/day, overnight town per
boundary | Preview free | Full itinerary, per-day handoff/navigation (paid)". The Worker /trip (T-0268) and the ScenicKit
day splitter (T-0249) are shipped; the app has no road-trip surface (grep RoadTrip under apps: none). Calm copy (memory
owner-route-intent).

## Log
- 2026-10-08T04:25:58Z filed by agent/claude-opus-5 (orchestrator) from the milestone gap map (M5 road trip UI).
- 2026-10-08T04:26:07Z claimed by agent/claude-opus-5; lease until 2026-10-09T04:26:07Z
