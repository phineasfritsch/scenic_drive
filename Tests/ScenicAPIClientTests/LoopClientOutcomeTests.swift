import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0314 R2: every Worker answer through the shipping entry point, `LoopClient.loop`, mapped to ONE typed outcome by
/// full equality, each from exactly one request (no retries); and every error to the sheet's failure.
@Suite("LoopClientOutcomeTests")
struct LoopClientOutcomeTests {
    static let resetsAt = Date(timeIntervalSince1970: 1_791_504_000)
    static let ninePins = Array(repeating: Coordinate(latitude: 34.04, longitude: -118.49), count: 9)

    static let rows: [(String, Int, String, Result<LoopResponse, LoopError>)] = [
        ("200 a square loop", 200, LoopWire.squareBody, .success(LoopWire.response())),
        ("200 an out-and-back", 200, LoopWire.outAndBackBody,
         .success(LoopWire.response(route: LoopWire.outAndBack, distance: 6_700,
                                    waypoints: [Coordinate(latitude: 34.05, longitude: -118.49)]))),
        ("200 no waypoints", 200, LoopWire.pinsBody(0), .success(LoopWire.response(waypoints: []))),
        ("200 nine waypoints", 200, LoopWire.pinsBody(9), .success(LoopWire.response(waypoints: ninePins))),
        ("200 ten waypoints", 200, LoopWire.pinsBody(10), .failure(.unexpectedResponse(status: 200))),
        ("200 not json", 200, "<html>", .failure(.unexpectedResponse(status: 200))),
        ("200 a three-number point", 200, LoopWire.squareBody.replacingOccurrences(of: "[-118.49,34.04]",
                                                                                   with: "[-118.49,34.04,0]"),
         .failure(.unexpectedResponse(status: 200))),
        ("200 a waypoint without lon", 200, LoopWire.squareBody.replacingOccurrences(of: #"{"lat":34.04,"lon":-118.46}"#,
                                                                                     with: #"{"lat":34.04}"#),
         .failure(.unexpectedResponse(status: 200))),
        ("400 invalid_request", 400, #"{"error":"invalid_request","detail":"minutes must be a number"}"#,
         .failure(.invalidRequest(detail: "minutes must be a number"))),
        ("404 not found", 404, #"{"error":"not_found"}"#, .failure(.unexpectedResponse(status: 404))),
        ("405 POST only", 405, #"{"error":"POST only"}"#, .failure(.unexpectedResponse(status: 405))),
        ("422 region_unsupported", 422, #"{"error":"region_unsupported"}"#, .failure(.regionUnsupported)),
        ("422 no_clean_loop", 422, #"{"error":"no_clean_loop","retrace_fraction":0.31}"#, .failure(.noCleanLoop)),
        ("422 another error", 422, #"{"error":"ceiling_breached"}"#, .failure(.unexpectedResponse(status: 422))),
        ("429 quota_exhausted", 429, #"{"error":"quota_exhausted","resets_at":"2026-10-09T00:00:00Z"}"#,
         .failure(.quotaExhausted(resetsAt: resetsAt))),
        ("429 without resets_at", 429, #"{"error":"quota_exhausted"}"#, .failure(.unexpectedResponse(status: 429))),
        ("500 an error page", 500, "<html>", .failure(.routingOffline)),
        ("502 no_route", 502, #"{"error":"no_route","detail":"router answered 500"}"#, .failure(.noRoute)),
        ("503 planning_paused", 503, #"{"error":"planning_paused"}"#, .failure(.planningPaused)),
        ("503 planning_unavailable", 503, #"{"error":"planning_unavailable"}"#, .failure(.routingOffline)),
        ("504 a gateway page", 504, "<html>", .failure(.routingOffline)),
        ("418 anything else", 418, "{}", .failure(.unexpectedResponse(status: 418))),
    ]

    @Test("every Worker answer is one typed outcome from one request", arguments: rows.map(\.0))
    func outcome(_ label: String) async {
        guard let (_, status, body, expected) = Self.rows.first(where: { $0.0 == label }) else { return }
        let fake = CountingPlanTransport(reply: LoopWire.reply(status, body))
        #expect(await LoopWire.loop(through: fake) == expected, "\(label)")
        #expect(await fake.count == 1, "\(label)")
    }

    @Test("an unreachable Worker is routingOffline after exactly one attempt")
    func offline() async {
        let fake = CountingPlanTransport.offline()
        #expect(await LoopWire.loop(through: fake) == .failure(.routingOffline))
        #expect(await fake.count == 1)
    }

    @Test("every loop error is the sheet's failure of the same name", arguments: [
        (LoopError.quotaExhausted(resetsAt: LoopClientOutcomeTests.resetsAt), LoopFailure.quotaExhausted),
        (.planningPaused, .planningPaused), (.routingOffline, .routingOffline), (.noRoute, .noRoute),
        (.noCleanLoop, .noCleanLoop), (.regionUnsupported, .regionUnsupported),
        (.invalidRequest(detail: "x"), .invalidRequest), (.refusedOnDevice(.minutesOutOfRange), .refusedOnDevice),
        (.unexpectedResponse(status: 418), .unexpectedResponse),
    ])
    func failureMapping(_ error: LoopError, _ failure: LoopFailure) {
        #expect(error.failure == failure)
    }
}
