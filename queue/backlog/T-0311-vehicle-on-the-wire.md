---
id: T-0311
title: The plan request carries the vehicle profile - PlanRequestBody sends it, the Worker's /plan whitelist accepts exactly the enabled profiles, and an unknown or disabled profile is refused before quota with 0 upstream calls
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/ScenicAPIClient/, Tests/ScenicAPIClientTests/, services/api/src/, services/api/test/, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/named-tests.json, pins/PINS.yaml]
pins_affected: [P-COST-01, P-PRIV-05]
reviewer: null
depends_on: [T-0309]
verify: [ops/test, ops/check-pins]
acceptance:
  - "RULE FIRST: the wire name and values (the ScenicKit VehicleProfile raw values, only .standard enabled), whether an absent field defaults to standard for older app builds (compat window ruled), and that the field adds no location data (P-PRIV-05)"
  - "Worker: /plan, /loop and /trip accept exactly the enabled profiles; every disabled and unknown value is 400 before the quota decrement with 0 upstream calls - table through worker.fetch, rows as functions of the route, meta-test no row ignores it; every route-enumerating table still complete"
  - "Swift: PlanRequestBody encodes the profile, built by full equality to a recomputation; digest rows re-approved; population entries for the whitelist and the encoding, MISSED before and CAUGHT by name after"
---
## Brief

rv1-t0309 recordable 1 / T-0309 owner R2 (PR #198): VehicleProfile stays on the device because /plan's whitelist has
no vehicle field; the plan's Decisions row says only .standard is enabled. This puts the profile on the wire without
widening anything else.

## Log
- 2026-10-08T01:56:34Z filed by agent/claude-opus-5 (orchestrator) from rv1-t0309's recordable.
