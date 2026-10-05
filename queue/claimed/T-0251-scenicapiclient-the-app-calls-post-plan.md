---
id: T-0251
title: ScenicAPIClient - the root-package client for the Worker's POST /plan (request built under the one-coordinate / 2-dp invariant, typed PlanError for every Worker failure), with a counting fake
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-05T11:45:00Z
lease_expires_at: 2026-10-05T23:45:00Z
worktree: .worktrees/T-0251
branch: task/T-0251
exclusive: [package-swift]
touches: [Package.swift, Sources/ScenicAPIClient/, Tests/ScenicAPIClientTests/, Tests/Fixtures/t0251/, services/api/test/planWire.test.ts, ops/lib/mutate-population-allowlist.json]
pins_affected: [P-PRIV-05, P-COST-01]
reviewer: null
depends_on: [T-0175, T-0248]
verify: [ops/test, ops/check-pins]
acceptance:
  - "Sources/ScenicAPIClient (Foundation + URLSession only) builds the exact POST /plan body T-0248 ruled; a test asserts the encoded body by EXACT equality to a typed literal and that the client refuses to send a second coordinate or one with more than 2 decimals (P-PRIV-05)"
  - "every Worker response T-0248 can return (200, 429 quota with resetsAt, 503 kill switch, router failure, bad request) maps to one PlanError case (the plan's closed enum: quotaExhausted, planningPaused, routingOffline, noRoute, ...) - a test per status by name, over recorded Worker responses from T-0248's vitest fixtures"
  - "a counting fake (the plan's 'counting fake') counts requests per plan; RED first by name; swift test count quoted"
---
## Brief

Milestone survey 2026-10-04: M3/M4 need the app to call the Worker. Starts after T-0175 releases the package-swift lock.

## Log
- 2026-10-05T09:04:49Z filed by agent/claude-opus-5 (orchestrator) after PR #139 (T-0248) merged.
- 2026-10-05T11:42:53Z PROMOTED to ready/ by agent/claude-opus-5 (orchestrator): T-0175 (PR #142) and T-0248 (PR #139) merged; package-swift lock free. Note from T-0175: the root Package.resolved is gitignored and GRDB is declared outside Windows only - copy that package-manifest shape.
- 2026-10-05T11:45:00Z claimed by agent/claude-opus-5; lease until 2026-10-05T23:45:00Z
- 2026-10-05T12:00:20Z RULINGS before code (agent/claude-opus-5, owner). Read: services/api/src/plan.ts, planRequest.ts,
  index.ts, quota.ts, upstream.ts, scenicPlanner.ts; test/planHarness.ts, planCost/planCeiling/planRecorded/routes
  tests; T-0248's R1-R9; Package.swift (T-0175's shape); the plan's PlanError row (:146) and tree line (:161).
  R1 TARGET. Library target `ScenicAPIClient` at Sources/ScenicAPIClient, dependencies ["ScenicKit"] (for Coordinate,
     as Handoff does), imports Foundation + FoundationNetworking behind `#if canImport` and nothing else; test target
     ScenicAPIClientTests. No GRDB, so no Windows condition. The client type is `PlanClient` (a type named like its
     module forces ScenicAPIClient.ScenicAPIClient qualification). Entry point, the one production runs:
     `PlanClient.plan(from: Coordinate, to place: Int64, budgetMinutes: Int, departsAt: Date?) async throws(PlanError)
     -> PlanResponse`. Typed throws: every failure the app can see is a PlanError at compile time.
  R2 REQUEST (T-0248 R1). POST <base>/plan, content-type application/json, body encoded by JSONEncoder with
     .sortedKeys: {"budget_minutes":B,"destination":{"place":"<id>"},"origin":{"lat":x,"lon":y}} plus "departs_at":
     "yyyy-MM-ddTHH:mm:ssZ" (UTC, whole seconds; the Worker's INSTANT grammar) only when departsAt is non-nil.
     Tests assert the whole PlanHTTPRequest (url, method, headers, body bytes) by EXACT equality to a typed literal.
  R3 PRIVACY (P-PRIV-05, refused ON THE DEVICE, zero requests). ONE coordinate: the API has exactly one Coordinate
     parameter; the destination is the corpus `place_id`, an Int64 (services/etl/etl/schema.py `place_id INTEGER`,
     segid.place_id), sent as its decimal string - a whitelist BY TYPE: no String parameter exists through which a
     second coordinate could ride (T-0248's grammar would admit "34.0676:-118.5957" as a place id; an Int64 cannot
     spell it). T-0248's harness id "la:topanga" is a test id the Worker accepts; the shipped corpus id is the
     integer, and the Worker's production resolvePlace (follow-up, T-0248 R4) keys on it. 2 DECIMALS: the client
     REFUSES (PlanError.refusedOnDevice(.originMoreThanTwoDecimals)) an origin whose lat or lon is not the double
     nearest some k/100 - `(v * 100).rounded() / 100 == v`, the Swift twin of the Worker's
     `Number(v.toFixed(2)) === v`; out of [-90,90]/[-180,180] or non-finite -> .originOutOfRange; budget outside
     0...180 -> .budgetOutOfRange (T-0248's MAX_BUDGET_MINUTES). The client does NOT round: rounding the device fix
     is the location layer's job (T-0248 R2 "rounded on the device"), and a client that rounded silently would make
     a 4-dp caller look compliant. Each refusal is tested on the entry point with the counting fake showing 0 requests.
  R4 TRANSPORT. `protocol PlanTransport: Sendable { func send(_ request: PlanHTTPRequest) async throws -> PlanHTTPReply }`
     over our own Sendable Equatable structs (URLRequest's Sendable/Equatable differ across corelibs and Darwin).
     `URLSessionPlanTransport` (dataTask + checked continuation, the CLI's portable shape) is the production one;
     `CountingPlanTransport` (an actor, in Sources so app tests can use it - plan :161 "counting fake") replays one
     canned reply and records every request, the count and the peak in flight.
  R5 RESPONSE. 200 decodes into PlanResponse (T-0248 R8): route [[lon,lat]] -> [Coordinate], distance_m, eta_s,
     fastest_eta_s, ceiling_s, budget_s, lambda, evaluations, used_budget, eta_is_estimate, hazards
     [{kind,value,from_index,to_index}] -> [PlanHazard], waypoints [{lat,lon}] -> [Coordinate], apple_maps_url -> URL.
     A 200 that does not decode -> .unexpectedResponse(status: 200).
  R6 ERROR MAPPING - every response a POST to /plan can get from the shipped Worker, read from plan.ts/index.ts,
     matched on the exact (status, body.error) pair; a known code at a different status falls to the last two rows:
       200  ScenicPlanResult                          -> PlanResponse (not an error)
       400  invalid_request {detail}                  -> .invalidRequest(detail:)   (body not JSON / whitelist refusal)
       404  unknown_place                             -> .unknownPlace               (corpus does not know the id)
       404  "not found"   (index.ts: unknown path)    -> .unexpectedResponse(status: 404)  (client misconfigured)
       405  "POST only"                               -> .unexpectedResponse(status: 405)  (client never GETs)
       422  no_scenic_alternative                     -> .noScenicAlternative
       429  quota_exhausted {resets_at}               -> .quotaExhausted(resetsAt: Date) (ISO-8601 with .000Z;
                                                         an unparseable resets_at -> .unexpectedResponse(status: 429))
       500  ceiling_breached | no_recorded_lambda     -> .planRefused(reason:)       (the server's safety net)
       502  no_route {detail}                         -> .noRoute
       503  planning_paused (KILL=1, upstream_paused, invalid_state) -> .planningPaused
       503  planning_unavailable (production deps unwired, T-0248 R4) -> .routingOffline
       5xx  any other body (handlePlan RETHROWS an unrecognised error - e.g. the router fetch TypeError when the
            VPS is down - so workerd answers a non-JSON 500; Cloudflare edge 52x) -> .routingOffline
       any other status/body (1xx/3xx/other 4xx, 2xx != 200)  -> .unexpectedResponse(status:)
       transport throws (no network, DNS, timeout)    -> .routingOffline (from the device the Worker being
            unreachable and its router being down are indistinguishable; the plan's action for both is cached plans
            + saved-drive handoff. offlineDuringDrive is a drive-time state, not a plan request's).
     The plan's attestUnsupported, regionUnsupported, offlineDuringDrive stay in the closed enum; no T-0248 response
     produces them (no /attest, no region gate, no drive yet). Added beyond the plan, each because a T-0248 response
     needs it: noScenicAlternative, unknownPlace, planRefused, invalidRequest, unexpectedResponse, and
     refusedOnDevice(PlanRefusal) for R3.
  R7 FIXTURES - RECORDED FROM THE WORKER. Each Worker-producible row is recorded by driving the Worker in its own
     vitest pool (handlePlan with T-0248's planHarness counting fakes; SELF.fetch for the shipped ROUTES rows 404
     "not found" and 503 planning_unavailable) and writing the exact response text to Tests/Fixtures/t0251/<status>-
     <name>.json. A committed contract test services/api/test/planWire.test.ts re-drives every scenario and asserts
     status and text EQUAL the fixture bytes (imported ?raw, as planHarness imports t0221), so the Swift tests decode
     bytes the Worker is held to. NOT recordable by driving the Worker, so quoted LITERALLY in the Swift tests and
     ruled here: 500 ceiling_breached / no_recorded_lambda (searchLambda only returns measured lambdas, so neither
     branch is reachable through handlePlan; bodies typed from plan.ts `json({ error: error.reason }, 500)`), the
     uncaught non-JSON 500, and a transport throw. touches widened for the fixture dir, the contract test and R8.
  R8 MUTATION POPULATION. check-mutate-population refuses an added Sources/ module with neither. ScenicAPIClient
     computes no number reaching score, route or tags (the allowlist's own criterion): it encodes numbers it is
     given, refuses some, and maps status codes. Each added file gets an allowlist entry with a reason read from the
     file; the 2-dp predicate's boundary is held instead by tests on the entry point at both sides of each edge
     (34.02 sent / 34.021 refused, 90 sent / 90.01 refused, 180 / -180, 0 / 180 / 181 minutes).
  R9 PINS. P-PRIV-05 and P-COST-01 named in pins_affected do not exist in pins/PINS.yaml today (grep: 0 hits);
     pins/ is not in touches, so no pin is added here - recorded as open in the PR. pins/floor_linux.txt is not
     raised (serial-only, not in touches); the new tests ride above the existing floor.
