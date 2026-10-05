---
id: T-0263
title: ScenicKit SurpriseReach - turn the Worker's /isochrone buckets into the per-candidate round-trip minutes Surprise.pick takes, byte-identical to the TS reference
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/ScenicKit/Surprise/, Tests/ScenicKitTests/, Tests/Fixtures/t0263/, ops/mutate/, services/api/test/]
pins_affected: [P-PROD-02]
reviewer: null
depends_on: [T-0253, T-0262]
verify: [ops/test, ops/check-pins]
acceptance:
  - "Sources/ScenicKit/Surprise gains SurpriseReach (Foundation only, one type per file): decodes the /isochrone response body T-0262 ruled ({minutes, buckets:[{minutes, round_trip_minutes, polygon}]}) and answers roundTripMinutes(at: Coordinate) -> Int? with the SAME rule as services/api/src/surpriseReach.ts roundTripMinutesAt (smallest containing bucket, outer ring in, hole out, none -> nil)"
  - "a shared fixture under Tests/Fixtures/t0263/ (>= 40 points over >= 3 bucket polygons incl. a hole, ring-edge and vertex points, ruled) gives IDENTICAL answers from the Swift port and the TS reference - a vitest test and a Swift test each read the same file and compare to the same recorded answers (full equality)"
  - "Surprise.pick driven end-to-end from a decoded /isochrone body over the T-0253 fixture: a test by name shows a candidate outside every bucket is never picked and the reach minutes reach SurpriseReason; ops/mutate population with a literal floor"
---
## Brief

T-0262 (PR #150) serves the reach; T-0253 (PR #144) picks from per-candidate round-trip minutes; nothing on the
device connects them. T-0262's R8 ruled the conversion and shipped the TS reference (surpriseReach.ts). This is the
Swift port and the parity fixture (the T-0252 RetraceDetector parity pattern: one fixture, both suites).

## Log
- 2026-10-05T17:36:29Z filed by agent/claude-opus-5 (orchestrator) after PR #150 (T-0262) merged.
