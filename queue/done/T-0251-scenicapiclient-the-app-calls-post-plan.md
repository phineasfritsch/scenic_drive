---
id: T-0251
title: ScenicAPIClient - the root-package client for the Worker's POST /plan (request built under the one-coordinate / 2-dp invariant, typed PlanError for every Worker failure), with a counting fake
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-05T11:45:00Z
lease_expires_at: 2026-10-05T23:45:00Z
worktree: .worktrees/T-0251
branch: task/T-0251
exclusive: [package-swift]
touches: [Package.swift, Sources/ScenicAPIClient/, Tests/ScenicAPIClientTests/, Tests/Fixtures/t0251/, services/api/test/planWire.test.ts, ops/lib/mutate-population-allowlist.json]
pins_affected: [P-PRIV-05, P-COST-01]
reviewer: agent/rv2-t0251
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
- 2026-10-05T12:28:01Z RECORDED + RED by name (agent/claude-opus-5). R7 recording: a throwaway generator in services/api/test (deleted, never
  committed) drove planWire.test.ts SCENARIOS with `npx vitest run -u` and `toMatchFileSnapshot`, writing the exact response
  text to Tests/Fixtures/t0251/ (11 files: 200-plan 16980 B, 200-plan-hazards, 400, 404 x2, 405, 422, 429, 502, 503 x2).
  planWire.test.ts against the EMPTY placeholder fixtures: 10 failed (every byte-equality row); after recording:
  `npx vitest run test/planWire.test.ts` -> Tests 12 passed (12). Swift RED against a stub PlanClient.plan that throws
  .unexpectedResponse(status: -1) without sending and a stub PlanResponseReader: `swift test --scratch-path .build/t0251
  --filter ScenicAPIClientTests` (Windows, swift 6.3.3) -> Executed 31 tests, 30 failed by name (all of
  PlanClientRequestTests 11/11 and PlanClientResponseTests 19/20); the one pass is testEveryRecordedReplyHasATest, the
  fixture-coverage meta test, which reads the directory, not the client - its red is shown separately at GREEN.
- 2026-10-05T13:34:05Z GREEN (agent/claude-opus-5). PlanResponseReader (the R6 table) and PlanClient.plan (validate -> sortedKeys encode ->
  ONE transport call -> read) implemented. Windows swift 6.3.3 `swift test --scratch-path .build/t0251 --filter
  ScenicAPIClientTests`: Executed 31 tests, with 0 failures. CI image (WSL docker swift:6.1-noble@sha256:98ee3a84..., the
  linux-core digest, apt libsqlite3-dev, a tar COPY of the worktree, own volume t0251-scratch, same filter): Executed 31
  tests, with 0 failures (PlanClientRequestTests 11, PlanClientResponseTests 20). Two corrections after RED, both in
  tests: the URLSession no-reply test used http://127.0.0.1:9, which took 60.03 s to fail on Windows - now a scheme
  URLSession has no protocol for (fails in 0.2 s, no socket); testCountingFakeCountsEveryPlanThroughIt now also asserts
  peakInFlight == 1. PRE-REVIEW MUTANT PASS (.build/mutants.py, scratch, full ScenicAPIClientTests per mutant), 9/9
  CAUGHT by name: M0 an extra fixture 418-teapot.json -> testEveryRecordedReplyHasATest (the meta test seen red);
  M1 atTwoDecimals *100 -> *1000 -> testRefusesAThreeDecimalLatitude/Longitude; M2 lat -90...90 -> -90..<90 ->
  testTwoDecimalOriginsAtEveryEdgeAreSent; M3 budget 0... -> 1... -> testBudgetIsSentInsideZeroTo180AndRefusedOutside;
  M4 503 planning_unavailable -> .planningPaused -> test503RecordedPlanningUnavailableIsRoutingOffline; M5 5xx fallback
  500... -> 501... -> test500UncaughtNonJSONLiteralIsRoutingOffline; M6 drop `inFlight -= 1` ->
  testCountingFakeCountsEveryPlanThroughIt; M7 route [lon,lat] read as [lat,lon] -> both 200 full-equality decodes;
  M8 drop .sortedKeys -> testSendsExactlyTheBodyT0248Ruled, testDepartsAtIsSent... Gates on this tree: check-line-cap
  exit 0 (largest new file 169 lines); check-mutate-population exit 0 ("13 added by this branch ... every added module
  is covered or allowlisted; the floor of 46 holds"); queue-check exit 0 (QUEUE OK, 246 tasks); `npx vitest run
  test/planWire.test.ts` 12/12.
- 2026-10-05T14:11:50Z ACCEPTANCE re-quoted on the MERGED head (agent/claude-opus-5): `git fetch origin` (main checkout) and `git merge
  origin/main` at c8b2d1e (PR #146; main brought /loop, retrace, upstream budget param - /plan wire unchanged).
  (1) RULED R1-R3 12:00:20Z before the RED commit f6cac97. Sources/ScenicAPIClient imports Foundation, ScenicKit and
      FoundationNetworking behind canImport only. testSendsExactlyTheBodyT0248Ruled and
      testDepartsAtIsSentAsAUTCInstantInWholeSeconds assert the whole PlanHTTPRequest by exact equality to a typed literal;
      testRefusesAThreeDecimalLatitude / Longitude / TheT0221FourDecimalOrigin refuse with ZERO requests; a second
      coordinate has no parameter to arrive through (destination is the Int64 place_id) and
      testBodyCarriesOneCoordinateAndAnIntegerPlace holds the key whitelist at every level.
  (2) R6 table: one test per status by name over the 11 Worker-recorded fixtures (200 x2, 400, 404 x2, 405, 422, 429, 502,
      503 x2) plus literal rows for 500 x3, wrong-status codes, an undecodable 200 and no reply;
      testEveryRecordedReplyHasATest holds the fixture directory to the tested set. `npx vitest run` on the merged tree:
      Test Files 18 passed (18), Tests 221 passed (221) - planWire.test.ts holds the Worker to the fixture bytes.
  (3) CountingPlanTransport counts one request per plan (testCountingFakeCountsOneRequestPerPlan: count 1, peak 1;
      three plans through one fake: count 3, peak 1); RED by name at f6cac97 (31 tests, 30 failed). swift test count:
      Windows `swift test --scratch-path .build/t0251 --filter ScenicAPIClientTests` -> Executed 31 tests, with 0
      failures; CI image swift:6.1-noble@sha256:98ee3a84... same filter -> Executed 31 tests, with 0 failures.
  Gates on the merged tree: check-line-cap exit 0 (172 Swift files, none over 300); check-mutate-population exit 0 (13
  added, every added module covered or allowlisted, floor 46 holds); queue-check exit 0 (QUEUE OK, 250 tasks). Local
  ops/check-pins --source-only was started on the pre-merge tree and had not finished; CI pins-source-only is the run of
  record. The package-swift lock is NOT released here - the reviewer sign-off deletes queue/LOCKS/package-swift.lock.
- 2026-10-05T14:53:16Z PRE-REVIEW SURVIVORS CLOSED (agent/claude-opus-5). The fable pass ran on e5ca131 and left three
  survivors, each alone, `swift test --scratch-path .build/fm-t0251 --filter ScenicAPIClient` -> 31 tests, 0 failures:
  MA PlanResponseReader `case (502, "no_route"?)` -> `case (502, _)`; MB PlanResponse `usedBudget:` decode -> `false`;
  MC URLSessionPlanTransport `httpBody = request.body` -> `nil`. Ruled: all three are real holes, none equivalent.
  MA: no test sent a 502 without the no_route body. MB: both recorded 200s carry used_budget false / eta_is_estimate
  true, so a hard-coded flag decodes equal. MC: no test read what the PRODUCTION transport hands URLSession - every
  request assertion ran through CountingPlanTransport. Closed on the entry point (PlanClient.plan):
  - test502WithoutNoRouteIsRoutingOffline: 502 "error code: 502" and 502 {"error":"planning_paused"} -> .routingOffline.
  - test200UsedBudgetTrueAndEtaNotEstimateDecodeAsSent: the 200-plan-hazards fixture text with used_budget true and
    eta_is_estimate false, full equality to the whole PlanResponse; test200MissingUsedBudgetOrEtaIsEstimateIsUnexpected
    Response: either key removed -> .unexpectedResponse(status: 200).
  - URLSessionPlanTransport gains `session: URLSession = .shared` (production unchanged: the default is the session
    it used). URLSessionPlanTransportTests.testURLSessionCarriesTheWholeRequestAndReturnsTheWholeReply drives
    PlanClient over URLSessionPlanTransport(timeout: 12, session:) whose configuration registers StubPlanURLProtocol;
    the stub captures the URLRequest URLSession was handed and the test asserts the WHOLE PlanHTTPRequest (url, method,
    headers, body bytes) by exact equality to the T-0248 literal, the timeout == [12], and that the recorded
    502-no-route reply comes back as .noRoute (status and body both crossed URLSession). Measured on first run: corelibs
    hands header names on as "Content-Type"; the stub compares names lowercased (HTTP field names are case-insensitive;
    uniqueKeysWithValues traps on two spellings of one name). On Darwin the body arrives as httpBodyStream; both read.
  GREEN, Windows swift 6.3.3 `swift test --scratch-path .build/t0251 --filter ScenicAPIClientTests`: Executed 35 tests,
  with 0 failures (Request 11, Response 23, URLSessionPlanTransport 1). RED by name, each mutant ALONE on this tree
  (.build/rv-mutants.py, scratch, same command), 7/7 CAUGHT:
    MA  502 any body -> noRoute            -> test502WithoutNoRouteIsRoutingOffline
    MB  usedBudget: false                  -> test200UsedBudgetTrueAndEtaNotEstimateDecodeAsSent, test200Missing...
    MB2 etaIsEstimate: true                -> test200UsedBudgetTrueAndEtaNotEstimateDecodeAsSent, test200Missing...
    MC  httpBody = nil                     -> testURLSessionCarriesTheWholeRequestAndReturnsTheWholeReply
    MC2 httpMethod = "GET"                 -> testURLSessionCarriesTheWholeRequestAndReturnsTheWholeReply
    MC3 header loop sets nothing           -> testURLSessionCarriesTheWholeRequestAndReturnsTheWholeReply
    MC4 timeoutInterval: 30 (not timeout)  -> testURLSessionCarriesTheWholeRequestAndReturnsTheWholeReply
  Each run: Executed 35 tests, the named tests the only failures. Line counts: PlanClientResponseTests 208,
  StubPlanURLProtocol 78, URLSessionPlanTransportTests 26, URLSessionPlanTransport 46.
- 2026-10-05T15:20:16Z MERGED HEAD (agent/claude-opus-5). CI image (WSL docker swift:6.1-noble@sha256:98ee3a84..., a tar COPY of 7373240,
  volume t0251-scratch, `swift test --scratch-path /scratch --filter ScenicAPIClientTests`): Executed 35 tests, with 0
  failures (11 / 23 / 1) - the stub URLProtocol path holds on Linux corelibs too. `git fetch origin` (main checkout),
  `git merge origin/main` -> ce066fd (main brought ScenicKit/Surprise, T-0260/T-0261 filed; nothing under
  ScenicAPIClient). On the merged head: Windows swift 6.3.3 same filter -> Executed 35 tests, with 0 failures;
  check-mutate-population.py exit 0 ("every added module is covered or allowlisted; the floor of 55 holds");
  queue-check exit 0 (QUEUE OK, 252 tasks); 300-line cap measured over git ls-files (Sources, Tests, apps/ios): 187
  files, none over 300 (ops/lib/check-line-cap did not finish in 13 min on the contended box and was stopped; CI's
  pins-source-only is the run of record for P-SRC-02 and the rest of check-pins).
- 2026-10-05T15:54:14Z rv1 B1 CLOSED AS A CLASS (agent/claude-opus-5). rv1-t0251 FAIL on b16f72e: `budgetSeconds: 1500`
  in PlanResponse.init(from:) left 35/35 green - both recorded 200s share budget_s 1500, lambda 7.75, evaluations 6,
  and MB had been closed one field (used_budget/eta_is_estimate) at a time. Ruled: the hole is every decoded field
  whose value the two recordings share, plus any required key read with decodeIfPresent/try? and a default. Closed in
  the new Tests/ScenicAPIClientTests/PlanResponseDecodeTests.swift (136 lines), every plan through PlanClient.plan
  over the counting fake (count == 1 asserted on each):
  - test200EveryFieldDistinctFromTheRecordedPlansDecodesWhole: a literal 200 body carrying only the keys PlanResponse
    reads (route.coordinates, route.distance_m, eta_s, fastest_eta_s, ceiling_s, budget_s 900, lambda 3.5,
    evaluations 11, used_budget true, eta_is_estimate false, one hazard surface/dirt [0,2), one waypoint,
    apple_maps_url), whole-PlanResponse equality to a typed literal.
  - testTheDistinctBodySharesNoFieldWithARecordedPlan: holds that premise - for 200-plan and 200-plan-hazards,
    decoded through the entry point, the list of the 13 PlanResponse fields equal to the literal's is [].
  - test200MissingAnyRequiredKeyIsUnexpectedResponse: the body's key paths, enumerated from the parsed body, must equal
    the typed 20-key table (route, route.coordinates, route.distance_m, eta_s, fastest_eta_s, ceiling_s, budget_s,
    lambda, evaluations, used_budget, eta_is_estimate, hazards, hazards.0.{kind,value,from_index,to_index},
    waypoints, waypoints.0.{lat,lon}, apple_maps_url); a control row decodes the re-serialized unedited body to the
    literal; then each key removed in turn -> .unexpectedResponse(status: 200), the message naming the key.
  - test200WrongTypedAnyRequiredKeyIsUnexpectedResponse: each of the 20 set to 7 (string keys) or "x" (all others),
    plus evaluations = 11.5 and route.coordinates.0 = a 3-number point -> .unexpectedResponse(status: 200) by name.
  RUN (.build/rv2-mutants.py, scratch: each mutant ALONE on PlanResponse.swift, restored after, one background
  script; `swift test --scratch-path .build/t0251 --filter ScenicAPIClientTests`, Windows swift 6.3.3):
    GREEN  ('39', '0')  Executed 39 tests, with 0 failures (Request 11, Response 23, Decode 4, URLSession 1)
    B1  budgetSeconds: 1500   ('39', '4') failed: test200EveryFieldDistinct..., test200MissingAnyRequiredKey...,
        test200WrongTypedAnyRequiredKey...; rows: 'budget_s = x', 'removed budget_s', 'the re-serialized body, unedited'
    ML  lambda: 7.75          ('39', '4') same three tests; rows: 'lambda = x', 'removed lambda', 'the re-serialized...'
    ME  evaluations: 6        ('39', '5') same three tests; rows: 'evaluations = 11.5', 'evaluations = x',
        'removed evaluations', 'the re-serialized body, unedited'
    MLD lambda: (try? top.decode(Double.self, forKey: .lambda)) ?? 3.5   ('39', '2') - the whole-equality test stays
        green (the default IS the literal's value); caught by test200MissingAnyRequiredKey... ('removed lambda') and
        test200WrongTypedAnyRequiredKey... ('lambda = x')
    MED evaluations: try top.decodeIfPresent(Int.self, forKey: .evaluations) ?? 11   ('39', '1') - caught only by
        test200MissingAnyRequiredKeyIsUnexpectedResponse ('removed evaluations'), as designed
  5/5 RED by name, then GREEN; `git status` after the run shows PlanResponse.swift unchanged. No source change: the
  decoder was right, the tests could not see it. Line counts: PlanResponseDecodeTests 136, PlanClientResponseTests 208.
- 2026-10-05T16:23:25Z REVIEW round 2 PASS by agent/rv2-t0251 (reviewer, not the owner) on PR #148, head 542b6e7.
  rv1 B1 is closed as a class. Touched rows only, re-run: three mutants, each applied ALONE to
  Sources/ScenicAPIClient/PlanResponse.swift by one background script (.build/rv2-mutants.py, detached worktree
  .worktrees/rv2-t0251), `swift test --scratch-path .build/rv2-t0251 --filter ScenicAPIClientTests`, Windows swift 6.3.3:
    B1  budgetSeconds: 1500            exit=1  Executed 39 tests, with 4 failures - test200EveryFieldDistinct...
        (budgetSeconds 1500.0 vs 900.0), test200MissingAnyRequiredKey... ('removed budget_s', 'the re-serialized
        body, unedited'), test200WrongTypedAnyRequiredKey... ('budget_s = x')
    MEI etaIsEstimate: true            exit=1  Executed 39 tests, with 6 failures - PlanClientResponseTests
        .test200UsedBudgetTrueAndEtaNotEstimateDecodeAsSent, .test200MissingUsedBudgetOrEtaIsEstimateIsUnexpectedResponse,
        PlanResponseDecodeTests: EveryFieldDistinct, MissingAnyRequiredKey ('removed eta_is_estimate'),
        WrongTypedAnyRequiredKey ('eta_is_estimate = x')
    MCD ceilingSeconds: try top.decodeIfPresent(Double.self, forKey: .ceilingSeconds) ?? 0
                                       exit=1  Executed 39 tests, with 1 failure - test200MissingAnyRequiredKey
        IsUnexpectedResponse ('removed ceiling_s')
    GREEN restored                     exit=0  Executed 39 tests, with 0 failures; `git status --porcelain` empty.
  3/3 RED by name, then GREEN. `bash ops/queue-check`: QUEUE OK (253 tasks). `gh pr checks 148`: core pass,
  pins-source-only pass. `git merge-base --is-ancestor origin/main origin/task/T-0251`: exit 0.
  Non-blocking (owner's stillOpen 3): apple_maps_url values that are strings but not valid URLs have no table row;
  URL(string:) accepts almost any string, so this is a gap in the tests, not a decode defect.
  Signed off: queue/claimed/ -> queue/done/, package-swift lock released.
