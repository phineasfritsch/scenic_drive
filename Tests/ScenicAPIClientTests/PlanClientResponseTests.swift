import Foundation
import ScenicAPIClient
import ScenicKit
import XCTest

/// T-0251 acceptance 2: every reply the Worker gives POST /plan maps to one outcome, a test per status by name.
/// The replies are the Worker's own bytes, recorded from its vitest pool into Tests/Fixtures/t0251 and held there
/// by services/api/test/planWire.test.ts (R7). The rows no driven Worker can produce are typed literally (R7).
final class PlanClientResponseTests: XCTestCase {
    /// Every fixture a test below reads. `testEveryRecordedReplyHasATest` holds it to the directory listing.
    static let covered: Set<String> = [
        "200-plan", "200-plan-hazards", "400-invalid-request", "404-unknown-place", "404-not-found",
        "405-post-only", "422-no-scenic-alternative", "429-quota-exhausted", "502-no-route",
        "503-planning-paused", "503-planning-unavailable",
    ]

    private func recorded(_ name: String) async throws -> Result<PlanResponse, PlanError> {
        XCTAssertTrue(Self.covered.contains(name), name)
        let (outcome, fake) = await PlanWire.plan(answering: try PlanWire.recordedReply(name))
        let count = await fake.count
        XCTAssertEqual(count, 1, name)
        return outcome
    }

    private func literal(_ status: Int, _ body: String) async -> PlanError? {
        PlanWire.error(await PlanWire.plan(answering: PlanHTTPReply(status: status, body: Data(body.utf8))).outcome)
    }

    func testEveryRecordedReplyHasATest() throws {
        let names = try FileManager.default.contentsOfDirectory(atPath: PlanWire.directory.path)
            .filter { $0.hasSuffix(".json") }
            .map { String($0.dropLast(".json".count)) }
        XCTAssertEqual(Set(names), Self.covered)
    }

    func test200RecordedSantaMonicaTopangaPlanDecodesWhole() async throws {
        let raw = try XCTUnwrap(try JSONSerialization.jsonObject(with: PlanWire.fixture("200-plan")) as? [String: Any])
        let pairs = try XCTUnwrap((raw["route"] as? [String: Any])?["coordinates"] as? [[Double]])
        let route = pairs.map { Coordinate(latitude: $0[1], longitude: $0[0]) }
        XCTAssertGreaterThan(route.count, 100)
        let waypoints = [(34.022381, -118.494759), (34.024532, -118.504645), (34.031417, -118.525402),
                         (34.042067, -118.569166), (34.040673, -118.579151), (34.046997, -118.577222),
                         (34.064359, -118.587044), (34.083495, -118.601615), (34.079413, -118.602877)]
            .map { Coordinate(latitude: $0.0, longitude: $0.1) }
        let url = "https://maps.apple.com/directions?source=34.02000,-118.49000&destination=34.06760,-118.59570"
            + "&waypoint=34.02238,-118.49476&waypoint=34.02453,-118.50465&waypoint=34.03142,-118.52540"
            + "&waypoint=34.04207,-118.56917&waypoint=34.04067,-118.57915&waypoint=34.04700,-118.57722"
            + "&waypoint=34.06436,-118.58704&waypoint=34.08350,-118.60162&waypoint=34.07941,-118.60288"
            + "&mode=driving"
        let expected = PlanResponse(
            route: route, distanceMeters: 20358.637, etaSeconds: 1346.01, fastestEtaSeconds: 1213.65,
            ceilingSeconds: 2713.65, budgetSeconds: 1500, lambda: 7.75, evaluations: 6, usedBudget: false,
            etaIsEstimate: true, hazards: [], waypoints: waypoints, appleMapsURL: URL(string: url)!)
        let decoded = try await recorded("200-plan").get()
        XCTAssertEqual(decoded, expected)
    }

    func test200RecordedPlanWithHazardsDecodesWhole() async throws {
        let decoded = try await recorded("200-plan-hazards").get()
        XCTAssertEqual(decoded, Self.hazardsPlan(usedBudget: false, etaIsEstimate: true))
    }

    /// The 200-plan-hazards fixture's plan, whole, with its two flags as given.
    private static func hazardsPlan(usedBudget: Bool, etaIsEstimate: Bool) -> PlanResponse {
        let route = [(34, -118.5), (34.005, -118.49), (34.01, -118.48), (34.015, -118.47), (34.02, -118.46),
                     (34.025, -118.45), (34.03, -118.44)].map { Coordinate(latitude: $0.0, longitude: $0.1) }
        let url = "https://maps.apple.com/directions?source=34.02000,-118.49000&destination=34.06760,-118.59570"
            + "&waypoint=34.00500,-118.49000&waypoint=34.01000,-118.48000&waypoint=34.01500,-118.47000"
            + "&waypoint=34.02000,-118.46000&waypoint=34.02500,-118.45000&mode=driving"
        return PlanResponse(
            route: route, distanceMeters: 6000, etaSeconds: 1100, fastestEtaSeconds: 1000, ceilingSeconds: 2500,
            budgetSeconds: 1500, lambda: 7.75, evaluations: 6, usedBudget: usedBudget, etaIsEstimate: etaIsEstimate,
            hazards: [PlanHazard(kind: "surface", value: "gravel", fromIndex: 2, toIndex: 3),
                      PlanHazard(kind: "surface", value: "compacted", fromIndex: 4, toIndex: 6),
                      PlanHazard(kind: "road_access", value: "destination", fromIndex: 1, toIndex: 2)],
            waypoints: Array(route[1...5]), appleMapsURL: URL(string: url)!)
    }

    /// The hazards fixture's text with `edit` applied, answered as a 200: the flags both recorded plans carry
    /// (used_budget false, eta_is_estimate true) cannot tell a decoded flag from a hard-coded one on their own.
    private func edited200(_ edit: (String) -> String) async throws -> Result<PlanResponse, PlanError> {
        let text = try XCTUnwrap(String(data: try PlanWire.fixture("200-plan-hazards"), encoding: .utf8))
        let changed = edit(text)
        XCTAssertNotEqual(changed, text)
        return await PlanWire.plan(answering: PlanHTTPReply(status: 200, body: Data(changed.utf8))).outcome
    }

    func test200UsedBudgetTrueAndEtaNotEstimateDecodeAsSent() async throws {
        let decoded = try await edited200 {
            $0.replacingOccurrences(of: #""used_budget":false"#, with: #""used_budget":true"#)
                .replacingOccurrences(of: #""eta_is_estimate":true"#, with: #""eta_is_estimate":false"#)
        }.get()
        XCTAssertEqual(decoded, Self.hazardsPlan(usedBudget: true, etaIsEstimate: false))
    }

    func test200MissingUsedBudgetOrEtaIsEstimateIsUnexpectedResponse() async throws {
        let noBudget = PlanWire.error(try await edited200 {
            $0.replacingOccurrences(of: #""used_budget":false,"#, with: "")
        })
        XCTAssertEqual(noBudget, .unexpectedResponse(status: 200))
        let noEstimate = PlanWire.error(try await edited200 {
            $0.replacingOccurrences(of: #""eta_is_estimate":true,"#, with: "")
        })
        XCTAssertEqual(noEstimate, .unexpectedResponse(status: 200))
    }

    func test400RecordedInvalidRequestCarriesTheWorkersDetail() async throws {
        let error = PlanWire.error(try await recorded("400-invalid-request"))
        XCTAssertEqual(error, .invalidRequest(detail: "origin.lat has more than 2 decimals; round it on the device"))
    }

    func test404RecordedUnknownPlaceIsUnknownPlace() async throws {
        let error = PlanWire.error(try await recorded("404-unknown-place"))
        XCTAssertEqual(error, .unknownPlace)
    }

    func test404RecordedNotFoundIsUnexpectedResponse() async throws {
        let error = PlanWire.error(try await recorded("404-not-found"))
        XCTAssertEqual(error, .unexpectedResponse(status: 404))
    }

    func test405RecordedPostOnlyIsUnexpectedResponse() async throws {
        let error = PlanWire.error(try await recorded("405-post-only"))
        XCTAssertEqual(error, .unexpectedResponse(status: 405))
    }

    func test422RecordedNoScenicAlternativeIsNoScenicAlternative() async throws {
        let error = PlanWire.error(try await recorded("422-no-scenic-alternative"))
        XCTAssertEqual(error, .noScenicAlternative)
    }

    func test429RecordedQuotaExhaustedCarriesResetsAt() async throws {
        let error = PlanWire.error(try await recorded("429-quota-exhausted"))
        XCTAssertEqual(error, .quotaExhausted(resetsAt: Date(timeIntervalSince1970: 1_791_244_800)))   // 2026-10-06T00:00Z
    }

    func test502RecordedNoRouteIsNoRoute() async throws {
        let error = PlanWire.error(try await recorded("502-no-route"))
        XCTAssertEqual(error, .noRoute)
    }

    func test503RecordedPlanningPausedIsPlanningPaused() async throws {
        let error = PlanWire.error(try await recorded("503-planning-paused"))
        XCTAssertEqual(error, .planningPaused)
    }

    func test503RecordedPlanningUnavailableIsRoutingOffline() async throws {
        let error = PlanWire.error(try await recorded("503-planning-unavailable"))
        XCTAssertEqual(error, .routingOffline)
    }

    func test500CeilingBreachedLiteralIsPlanRefused() async {
        let error = await literal(500, #"{"error":"ceiling_breached"}"#)
        XCTAssertEqual(error, .planRefused(reason: "ceiling_breached"))
    }

    func test500NoRecordedLambdaLiteralIsPlanRefused() async {
        let error = await literal(500, #"{"error":"no_recorded_lambda"}"#)
        XCTAssertEqual(error, .planRefused(reason: "no_recorded_lambda"))
    }

    func test500UncaughtNonJSONLiteralIsRoutingOffline() async {
        let error = await literal(500, "error code: 1101")
        XCTAssertEqual(error, .routingOffline)
    }

    func test429WithoutAReadableResetsAtIsUnexpectedResponse() async {
        let missing = await literal(429, #"{"error":"quota_exhausted"}"#)
        XCTAssertEqual(missing, .unexpectedResponse(status: 429))
        let garbled = await literal(429, #"{"error":"quota_exhausted","resets_at":"tomorrow"}"#)
        XCTAssertEqual(garbled, .unexpectedResponse(status: 429))
    }

    func testAKnownCodeAtAnotherStatusIsNotTrusted() async {
        let paused = await literal(400, #"{"error":"planning_paused"}"#)
        XCTAssertEqual(paused, .unexpectedResponse(status: 400))
        let route = await literal(503, #"{"error":"no_route"}"#)
        XCTAssertEqual(route, .routingOffline)
    }

    func test502WithoutNoRouteIsRoutingOffline() async {
        let gateway = await literal(502, "error code: 502")
        XCTAssertEqual(gateway, .routingOffline)
        let foreign = await literal(502, #"{"error":"planning_paused"}"#)
        XCTAssertEqual(foreign, .routingOffline)
    }

    func test200ThatDoesNotDecodeIsUnexpectedResponse() async {
        let error = await literal(200, #"{"error":"planning_paused"}"#)
        XCTAssertEqual(error, .unexpectedResponse(status: 200))
    }

    func testNoReplyThroughTheCountingFakeIsRoutingOffline() async {
        let fake = CountingPlanTransport.offline()
        let outcome = await PlanWire.plan(through: fake)
        XCTAssertEqual(PlanWire.error(outcome), .routingOffline)
        let count = await fake.count
        XCTAssertEqual(count, 1)
    }

    func testNoReplyThroughURLSessionIsRoutingOffline() async {
        // A scheme URLSession has no protocol for fails at once, on every host, with no reply: the production
        // transport's throw path, without a socket (a refused localhost port took 60 s to fail on Windows).
        let outcome = await PlanWire.plan(through: URLSessionPlanTransport(timeout: 10),
                                          base: URL(string: "scenic-unsupported://scenic-api.test")!)
        XCTAssertEqual(PlanWire.error(outcome), .routingOffline)
    }
}
