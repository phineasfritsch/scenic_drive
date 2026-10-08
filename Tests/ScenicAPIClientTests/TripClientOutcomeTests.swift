import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0313 R3: every Worker answer through the shipping entry point, `TripClient.trip`, mapped to ONE typed outcome
/// by full equality, each from exactly one request (no retries); and every error to the sheet's failure.
@Suite("TripClientOutcomeTests")
struct TripClientOutcomeTests {
    static let resetsAt = Date(timeIntervalSince1970: 1_791_504_000)

    static let rows: [(String, Int, String, Result<TripResponse, TripError>)] = [
        ("200 preview", 200, TripWire.previewBody, .success(TripWire.preview)),
        ("200 full", 200, TripWire.fullBody, .success(TripWire.full)),
        ("200 not json", 200, "<html>", .failure(.unexpectedResponse(status: 200))),
        ("200 an unknown view", 200, TripWire.previewBody.replacingOccurrences(of: #""view":"preview""#,
                                                                                with: #""view":"paid""#),
         .failure(.unexpectedResponse(status: 200))),
        ("200 a three-number point", 200, TripWire.previewBody.replacingOccurrences(of: "[-119.2,34.4]",
                                                                                     with: "[-119.2,34.4,0]"),
         .failure(.unexpectedResponse(status: 200))),
        ("400 invalid_request", 400, #"{"error":"invalid_request","detail":"days must be a whole number"}"#,
         .failure(.invalidRequest(detail: "days must be a whole number"))),
        ("404 unknown_place", 404, #"{"error":"unknown_place"}"#, .failure(.unknownPlace)),
        ("404 another error", 404, #"{"error":"not_found"}"#, .failure(.unexpectedResponse(status: 404))),
        ("405 POST only", 405, #"{"error":"POST only"}"#, .failure(.unexpectedResponse(status: 405))),
        ("422 region_unsupported", 422, #"{"error":"region_unsupported"}"#, .failure(.regionUnsupported)),
        ("422 too_few_days", 422, #"{"error":"too_few_days","days":1,"max_drive_s":21600,"max_distance_m":482803}"#,
         .failure(.tooFewDays)),
        ("422 ceiling_breached", 422, #"{"error":"ceiling_breached","detail":"over"}"#, .failure(.ceilingBreached)),
        ("422 another error", 422, #"{"error":"no_scenic_alternative"}"#, .failure(.unexpectedResponse(status: 422))),
        ("429 quota_exhausted", 429, #"{"error":"quota_exhausted","resets_at":"2026-10-09T00:00:00Z"}"#,
         .failure(.quotaExhausted(resetsAt: resetsAt))),
        ("429 without resets_at", 429, #"{"error":"quota_exhausted"}"#, .failure(.unexpectedResponse(status: 429))),
        ("500 no_recorded_lambda", 500, #"{"error":"no_recorded_lambda"}"#,
         .failure(.planRefused(reason: "no_recorded_lambda"))),
        ("502 no_route", 502, #"{"error":"no_route","detail":"router answered 500"}"#, .failure(.noRoute)),
        ("503 planning_paused", 503, #"{"error":"planning_paused"}"#, .failure(.planningPaused)),
        ("503 planning_unavailable", 503, #"{"error":"planning_unavailable"}"#, .failure(.routingOffline)),
        ("504 a gateway page", 504, "<html>", .failure(.routingOffline)),
        ("418 anything else", 418, "{}", .failure(.unexpectedResponse(status: 418))),
    ]

    @Test("every Worker answer is one typed outcome from one request", arguments: rows.map(\.0))
    func outcome(_ label: String) async {
        guard let (_, status, body, expected) = Self.rows.first(where: { $0.0 == label }) else { return }
        let fake = CountingPlanTransport(reply: TripWire.reply(status, body))
        #expect(await TripWire.trip(through: fake) == expected, "\(label)")
        #expect(await fake.count == 1, "\(label)")
    }

    @Test("an unreachable Worker is routingOffline after exactly one attempt")
    func offline() async {
        let fake = CountingPlanTransport.offline()
        #expect(await TripWire.trip(through: fake) == .failure(.routingOffline))
        #expect(await fake.count == 1)
    }

    @Test("every trip error is the sheet's failure of the same name", arguments: [
        (TripError.quotaExhausted(resetsAt: TripClientOutcomeTests.resetsAt), TripFailure.quotaExhausted),
        (.planningPaused, .planningPaused), (.routingOffline, .routingOffline), (.noRoute, .noRoute),
        (.regionUnsupported, .regionUnsupported), (.unknownPlace, .unknownPlace), (.tooFewDays, .tooFewDays),
        (.ceilingBreached, .ceilingBreached), (.planRefused(reason: "x"), .planRefused),
        (.invalidRequest(detail: "x"), .invalidRequest), (.refusedOnDevice(.daysOutOfRange), .refusedOnDevice),
        (.unexpectedResponse(status: 418), .unexpectedResponse),
    ])
    func failureMapping(_ error: TripError, _ failure: TripFailure) {
        #expect(error.failure == failure)
    }
}
