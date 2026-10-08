---
id: T-0316
title: Road trips name an overnight town per day boundary and 2-4 corridor stops per day - the Worker's planTrip passes the corpus places it already holds into the ScenicKit-parity day splitter
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-08T06:33:22Z
lease_expires_at: 2026-10-08T20:33:22Z
worktree: .worktrees/T-0316
branch: task/T-0316
exclusive: []
touches: [services/api/src/, services/api/test/, ops/lib/named-tests.json, pins/PINS.yaml]
pins_affected: [P-COST-01, P-PRIV-05]
reviewer: null
depends_on: [T-0268, T-0313]
verify: [ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST: which places the Worker already holds (D1 places table, T-0256 resolver), the plan's rule (overnight = lodging within 15 km of the day boundary; 2-4 corridor POIs/day), and that no new coordinate leaves the device (the server picks from its own corpus)"
  - "planTrip passes the candidate places to the splitter; a full-equality table over {no lodging near a boundary, one, several} and {0, 1, 5 corridor places} through worker.fetch; an itinerary with no lodging says so honestly"
  - "Every route-enumerating table unchanged (no new route); population entries MISSED before and CAUGHT by name after; new PINS.yaml text double-quoted"
---
## Brief

T-0313 owner stillOpen (PR #201): the Worker's planTrip passes no places, so stops are always empty and overnight towns
read "not searched yet" in the app (T-0268). Plan, Road trip: "2-4 corridor POIs/day; overnight town = lodging within
15 km".

## Log
- 2026-10-08T06:32:40Z filed by agent/claude-opus-5 (orchestrator) from T-0313's stillOpen.
- 2026-10-08T06:33:22Z claimed by agent/claude-opus-5; lease until 2026-10-08T20:33:22Z
