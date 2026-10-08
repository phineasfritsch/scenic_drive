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
- 2026-10-08T03:05:27Z BUILT. agent/claude-opus-5 (owner).
  - RED FIRST, committed (c1bdfbf4: the tests, with compile-only Swift stubs - a defaulted `vehicle:` parameter that
    is ignored and an unused `.vehicleNotEnabled`). `npx vitest run test/vehicleWire.test.ts`: `x an absent vehicle
    and "standard" observe the same answer on every route, and that answer spent the quota and called the router`,
    `x every disabled and unknown vehicle is 400 invalid_request whole on every route, with zero router requests and
    an untouched quota`, `x no row ignores its route: ...`, `Tests 3 failed (3)`. `swift test --filter
    ScenicAPIClientTests\.(PlanVehicleWireTests|PlanClientRequestTests|PlanSheetGateTests)`: `x "a plan that names no
    vehicle is sent as standard"`, `x "every profile: an enabled one is sent as its raw value, ..."` (3 issues),
    `x "P-PRIV-06: a typed start leaves as ONE coordinate at 2 dp, the body equal to its recomputation"`,
    testSendsExactlyTheBodyT0248Ruled and testDepartsAtIsSentAsAUTCInstantInWholeSeconds failed.
  - GREEN (cf840780): src/vehicle.ts (ENABLED_VEHICLE_PROFILES, vehicleProblem) read LAST by the three parsers;
    loopRequest.ts's keysProblem gained a required list (its whitelist had been all-required). Four more body
    literals gained `"vehicle":"standard"` (PlanClientDeviceTests x2, URLSessionPlanTransportTests, the key-set
    test). Digests re-approved for PlanClient.swift, PlanRefusal.swift, PlanRequestBody.swift.
  - POPULATION. Worker services/api/test/mutate/vehicleMutants.mjs (floor 15, 1 EQUIVALENT with witness, 4
    subjects): `--prove-floor` 4 of 4 arms refused, control quiet; `--prove-vacuity` `RESULT caught=0 missed=15
    trap=0 of 15`; with the test `RESULT caught=15 missed=0 trap=0 of 15`, each CAUGHT by name. Swift: plansheet
    entries 33-37 + E2 (floors 37/2/4): `--only 33,34,35,36,37 --prove-vacuity` `VACUITY PROOF OK ... MISSED=5 of
    5`; `--only 33,34,35,36,37,E2` `caught by the test that names it: 5 of 5`, `MISSED E2 the encoder writes
    standard for the profile`, `MUTATE OK caught=5/5`. R8 AMENDED: plansheet.py's SUBJECT_MODULES is NOT widened -
    check-mutate-population refused it (`PlanClient.swift` / `PlanRequestBody.swift` `is allowlisted as computing
    no number AND is mutated by a population`); the allowlist is outside touches and its reasons stand (no number
    is computed), so the two files are mutated as the harness's own SUBJECTS only. `P-PROC-06: every added module
    is covered or allowlisted; the floor of 93 holds`.
  - ACCEPTANCE at 0a0e8fc6 (origin/main fetched: `Already up to date`, T-0310 not yet merged): `npx vitest run`
    `Test Files 76 passed (76)`, `Tests 2128 passed (2128)`; `swift test --filter ScenicAPIClientTests` `Executed 46
    tests, with 0 failures` and `Test run with 27 tests in 5 suites passed`; `run-named-tests.py P-COST-01` `NAMED
    P-COST-01 passed=46/46`; `run-named-tests.py P-PRIV-05` `NAMED P-PRIV-05 passed=45/46`, the one RED being
    `PlaceStoreTests.UserStorePrivacyTests/noColumnNamesAPlaceOrATrail(): MISSING` - that file is `#if
    canImport(GRDB)` and GRDB does not build on this Windows box; all six T-0311 bindings ran green; CI (Linux) is
    the proof of that row. `bash ops/lib/check-safety-disclaimer` rc=0, `bash ops/lib/check-map-attribution` rc=0,
    `check-pins-yaml.py` `PINS-YAML ok pins=44 fields=355`, `ops/queue-check` `QUEUE OK (302 tasks)`. Sizes:
    vehicle.ts 18, planRequest.ts 112, loopRequest.ts 69, tripRequest.ts 99, vehicleWire.test.ts 143,
    vehicleMutants.mjs 145, PlanRequestBody.swift 75, PlanClient.swift 60, PlanVehicleWireTests.swift 67.
  - GAPS (stillOpen): the app always sends `.standard` - PlanTicket/ClientPlanner do not carry the stored profile
    (ScenicKit outside touches); VehicleProfile.swift's doc comment still says the /plan body has no vehicle field
    (ScenicKit outside touches); /isochrone has no vehicle key (R1); the R2 compat window must be re-ruled by the
    task that enables a second profile.
