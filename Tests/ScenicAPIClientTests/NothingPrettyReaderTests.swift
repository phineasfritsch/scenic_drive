import Foundation
import ScenicAPIClient
import ScenicKit
import XCTest

/// T-0332 A6: a 422 `nothing_pretty` reaches the app as `PlanError.nothingPretty` carrying the Worker's offers, read
/// through the shipping client path (`PlanWire.plan(answering:)` -> PlanResponseReader) and compared WHOLE. Every
/// field at each bound, and each field missing, mistyped or out of range, answers `unexpectedResponse(status: 422)`.
final class NothingPrettyReaderTests: XCTestCase {
    private func literal(_ status: Int, _ body: String) async -> PlanError? {
        PlanWire.error(await PlanWire.plan(answering: PlanHTTPReply(status: status, body: Data(body.utf8))).outcome)
    }

    private static func body(_ budget: String, _ more: String?, _ back: String?) -> String {
        var fields = [#""error":"nothing_pretty""#, #""budget_minutes":\#(budget)"#]
        if let more { fields.append(#""more_time_minutes":\#(more)"#) }
        if let back { fields.append(#""back_roads_eta_s":\#(back)"#) }
        return "{" + fields.joined(separator: ",") + "}"
    }

    private static let below0 = (0.0).nextDown
    private static let above180 = (180.0).nextUp

    /// (name, budget, more, back) -> the offer, or nil for "refused: unexpectedResponse(422)".
    private static let rows: [(String, String, String?, String?, NothingPrettyOffer?)] = [
        ("westwood-malibu +25", "25", "65", "1909.81",
         NothingPrettyOffer(budgetMinutes: 25, moreTimeMinutes: 65, backRoadsEtaSeconds: 1909.81)),
        ("budget 0 accepted", "0", "40", "null",
         NothingPrettyOffer(budgetMinutes: 0, moreTimeMinutes: 40, backRoadsEtaSeconds: nil)),
        ("budget 140, more exactly 180", "140", "180", "null",
         NothingPrettyOffer(budgetMinutes: 140, moreTimeMinutes: 180, backRoadsEtaSeconds: nil)),
        ("budget 180, no more time", "180", "null", "600",
         NothingPrettyOffer(budgetMinutes: 180, moreTimeMinutes: nil, backRoadsEtaSeconds: 600)),
        ("budget below 0", "\(below0)", "null", "null", nil),
        ("budget above 180", "\(above180)", "null", "null", nil),
        ("budget a string", #""25""#, "65", "null", nil),
        ("budget a bool", "true", "null", "null", nil),
        ("budget null", "null", "null", "null", nil),
        ("more time missing", "25", nil, "null", nil),
        ("more time a string", "25", #""65""#, "null", nil),
        ("more time not budget + 40", "25", "66", "null", nil),
        ("more time past 180", "141", "181", "null", nil),
        ("back roads missing", "25", "65", nil, nil),
        ("back roads a string", "25", "65", #""600""#, nil),
        ("back roads 0", "25", "65", "0", nil),
        ("back roads negative", "25", "65", "-1", nil),
        ("back roads a bool", "25", "65", "false", nil),
    ]

    func testEveryRowWhole() async {
        for (name, budget, more, back, offer) in Self.rows {
            let expected: PlanError = offer.map { .nothingPretty($0) } ?? .unexpectedResponse(status: 422)
            let error = await literal(422, Self.body(budget, more, back))
            XCTAssertEqual(error, expected, name)
        }
    }

    func testBudgetMissingIsRefused() async {
        let error = await literal(422, #"{"error":"nothing_pretty","more_time_minutes":65,"back_roads_eta_s":null}"#)
        XCTAssertEqual(error, .unexpectedResponse(status: 422))
    }

    func testNothingPrettyAtAnotherStatusIsNotTrusted() async {
        let body = Self.body("25", "65", "null")
        for status in [400, 404, 409, 429] {
            let error = await literal(status, body)
            XCTAssertEqual(error, .unexpectedResponse(status: status), "\(status)")
        }
        let server = await literal(500, body)
        XCTAssertEqual(server, .routingOffline)
    }

    func testTheSheetShowsTheHonestFailure() {
        let offer = NothingPrettyOffer(budgetMinutes: 25, moreTimeMinutes: 65, backRoadsEtaSeconds: nil)
        XCTAssertEqual(PlanError.nothingPretty(offer).failure, .nothingPretty)
        XCTAssertEqual(PlanFailureCopy.of(.nothingPretty), PlanFailureCopy(
            line: "Not much pretty within reach of this drive. More time might find some.", action: .chooseAnotherPlace))
    }
}
