---
id: T-0311
title: The plan request carries the vehicle profile - PlanRequestBody sends it, the Worker's /plan whitelist accepts exactly the enabled profiles, and an unknown or disabled profile is refused before quota with 0 upstream calls
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-08T02:22:15Z
lease_expires_at: 2026-10-08T16:22:15Z
worktree: .worktrees/T-0311
branch: task/T-0311
exclusive: []
touches: [Sources/ScenicAPIClient/, Tests/ScenicAPIClientTests/, services/api/src/, services/api/test/, ops/mutate/, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/named-tests.json, pins/PINS.yaml]
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
- 2026-10-08T02:22:15Z claimed by agent/claude-opus-5; lease until 2026-10-08T16:22:15Z
- 2026-10-08T02:26:06Z MEASURE, then RULINGS before code. agent/claude-opus-5 (owner).
  - MEASURED at 9e0c69be. `VehicleProfile` (Sources/ScenicKit/Vehicle/VehicleProfile.swift) raw values, in case
    order: `standard`, `lowClearance`, `motorcycle`, `trailer`, `rv`; `isEnabled` only for `.standard`; `stored(_:)`
    maps absent/unknown/disabled to `.standard`. Worker whitelists: planRequest.ts BODY_KEYS = origin, destination,
    budget_minutes, departs_at; loopRequest.ts = start, minutes; tripRequest.ts = origin, destination, days,
    extra_budget_pct - none has a vehicle key. `PlanRequestBody` encodes origin{lat,lon}, destination{place},
    budget_minutes, departs_at?; its one caller is `PlanClient.plan`, whose one app caller is `ClientPlanner` (a
    ScenicKit `RoutePlanning` conformer fed a `PlanTicket`, which carries no vehicle; ScenicKit is outside touches).
    Request bodies are held by full equality in PlanClientRequestTests (two literals) and PlanSheetGateTests
    (`P-PRIV-06 ... the body equal to its recomputation`). No ops/mutate population names PlanRequestBody.swift.
  - R1 WIRE. One optional top-level key `vehicle`, a JSON string, its values the ScenicKit raw values above. /plan,
    /loop and /trip each accept exactly ENABLED_VEHICLE_PROFILES = [`standard`] (one module, src/vehicle.ts, read by
    all three parsers). /isochrone is not in the acceptance and does not gain the key.
  - R2 COMPAT WINDOW. An ABSENT `vehicle` is `standard`, with no expiry: every build before this one could only
    have chosen `.standard` (the only enabled case, and `stored()` reads anything else back as `.standard`), so
    absent and `"standard"` mean the same route. The window is re-ruled by whichever task enables a second profile
    (it must then decide whether absent may still mean standard). The test holds it: absent observes exactly what
    `"standard"` observes, on every route.
  - R3 REFUSED. Every disabled raw value, every unknown string (case, padding, empty, prefix/suffix near-misses of
    `standard`) and every non-string (null, number, boolean, array, object - including `{lat, lon}`) is 400
    `invalid_request` with detail `vehicle must be "standard": the only profile <route> plans for`, from the parser,
    so it lands before the region gate, the deps, identify, the closures read and the quota reservation: 0 router
    requests, quota untouched. The vehicle check runs LAST in each parser, so every existing detail is unchanged.
  - R4 P-PRIV-05. The field is a closed string enum; a non-string is refused, so no coordinate can ride in it. The
    whitelist widens by exactly one top-level key per route; ORIGIN/START/DESTINATION key lists are untouched.
  - R5 PARSED REQUEST. The parsers validate the key and do not carry it into PlanRequest/LoopRequest/TripRequest:
    every accepted value is `standard` and the planners route one profile. Carrying it to routing is the task that
    enables a second profile.
  - R6 SWIFT. `PlanRequestBody` gains `vehicle: VehicleProfile` and always encodes `"vehicle": rawValue` (the app
    is explicit; the R2 default exists only for older builds). `validated(..., vehicle:)` refuses a disabled case
    with a new `PlanRefusal.vehicleNotEnabled`, zero requests. `PlanClient.plan` gains `vehicle: VehicleProfile =
    .standard`: ClientPlanner's ticket has no vehicle and ScenicKit is outside touches, and today the stored read can
    only return `.standard`, so the default is exactly what the stored profile would be. Threading the stored
    profile through PlanTicket is a follow-up (stillOpen).
  - R7 TESTS. Worker: test/vehicleWire.test.ts through `worker.fetch` (the region-gate-order harness shape); rows =
    (value) x (route), each body = f(route) = the route's reference body + `vehicle`; observation {status, json,
    router requests, quota touched}. Meta-test: no row ignores its route - the same row with `vehicle` set to
    `"standard"` observes the route's baseline (so every 400 is the vehicle's, not a body malformed for that route),
    and the refusal detail names the route. Swift: Tests/ScenicAPIClientTests/PlanVehicleWireTests.swift through
    `PlanClient.plan` - for every `VehicleProfile.allCases` case, enabled -> one request whose bytes EQUAL the body
    recomputed in the test; disabled -> `.refusedOnDevice(.vehicleNotEnabled)` with zero requests; and the raw
    values equal the Worker table's literal list. The three existing body literals gain `"vehicle":"standard"`.
  - R8 TOUCHES WIDENED by `ops/mutate/` (this entry): the Swift population is the plansheet population grown by
    PlanRequestBody.swift and PlanClient.swift as subjects and the new test file (its own MIN floors raised), not a
    new driver - a new driver would need ops/lib/mutate_population_table.py (DRIVERS), which is not in touches.
    Worker population: services/api/test/mutate/vehicleMutants.mjs (planMutants' shape). Both shown MISSED with the
    killer suite emptied (--prove-vacuity) and CAUGHT by name after.
  - R9 NAMED TESTS. The new Worker tests are bound by name under P-COST-01 and P-PRIV-05 in named-tests.json, the
    Swift test under P-PRIV-05; PINS.yaml text grows only where it counts bound tests.
