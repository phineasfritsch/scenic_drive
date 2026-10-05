---
id: T-0263
title: ScenicKit SurpriseReach - turn the Worker's /isochrone buckets into the per-candidate round-trip minutes Surprise.pick takes, byte-identical to the TS reference
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-05T17:38:25Z
lease_expires_at: 2026-10-06T05:38:25Z
worktree: .worktrees/T-0263
branch: task/T-0263
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
- 2026-10-05T17:38:25Z claimed by agent/claude-opus-5; lease until 2026-10-06T05:38:25Z
- 2026-10-05T17:46:46Z RULINGS before code (agent/claude-opus-5). R1 NAME: `SurpriseReach` already exists (T-0253: the budget + id -> minutes map Surprise.pick takes) and stays unchanged. The acceptance's "gains SurpriseReach" is ruled as: the port is `SurpriseIsochrone` (the decoded body: `decode(_ body: Data) throws`, `roundTripMinutes(at: Coordinate) -> Int?`, `reach(for: [SurpriseCandidate]) -> SurpriseReach`), with `SurpriseIsochroneBucket` and `SurpriseIsochronePolygon`, one type per file, synthesized Decodable (snake_case via the decoder's key strategy, no nested CodingKeys types). R2 BUDGET: `reach(for:).budgetMinutes` is the body's `minutes` (T-0262 R7: it echoes the request, i.e. the dial); a candidate with no containing bucket is absent from the map. R3 RULE: roundTripMinutesAt ported operation for operation - even-odd ray casting with the same IEEE expression order `(xj - xi) * (lat - yi) / (yj - yi) + xi`, outer ring in and no hole in, the SMALLEST `round_trip_minutes` read from the wire (not recomputed as 2*minutes, as the TS reads the field), none -> nil. R4 DECODE: strict where the TS Ring type is: `minutes`, `buckets`, each bucket's `minutes`, `round_trip_minutes`, `polygon` required; `polygon.type` must be "Polygon" and every position carry >= 2 numbers, else PlanFailure.malformedResponse; unknown keys ignored (the Worker whitelists). R5 PARITY FIXTURE: Tests/Fixtures/t0263/isochrone.json is a body as the handler emits it (minutes 90, buckets 15/30/45 one way, 30/60/90 round trip) on a 1/64-degree grid so every coordinate is an exact binary decimal; the 30 bucket has a hole inside the 45 and a triangular hole overlapping the 15, the 45 has a hole outside the 30; Tests/Fixtures/t0263/points.json holds >= 40 points with a `why` and the expected minutes, hand-ruled from even-odd's edge semantics (left/bottom edge in, right/top edge out, vertices per the half-open crossing) - diagonal-edge points are ruled by the TS reference, which the Brief names the reference, and any disagreement with my hand ruling is logged. make-fixture.py beside them writes both (provenance). Both services/api/test/surpriseReachParity.test.ts and Tests/ScenicKitTests/Surprise/SurpriseReachParityTests.swift read both files and compare the WHOLE answer array to the recorded one (full equality). R6 END-TO-END: Tests/Fixtures/t0263/la-reach.json, a 180-minute body (six buckets 15..90 one way, nested boxes over the T-0253 candidates, a hole in the 30 bucket over griffith-09) decoded through `SurpriseIsochrone.decode`; the ten ojai-* candidates (lon < -118.90) lie outside every bucket, and T-0253's own map picks them, so "never picked" is not vacuous. R7 MUTATE: the T-0253 population (ops/mutate/surprise_mutations.py, surprise.py, surprise_run.py) gains the three new subjects and the two new test files; MIN_MUTATIONS stays a literal, raised by exactly the rows added; fix rounds run `--only`. R8 pins_affected P-PROD-02: pins/ is outside touches and Surprise.pick is unchanged; no pin edit.
