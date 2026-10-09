import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0334 A4-A6 through the shipping path the sheet's view runs: the gate's ticket -> `ClientPlanner.plan` ->
/// `PlanClient.plan` over the counting transport -> `finish`. The request bytes are compared WHOLE to the sorted-keys
/// body recomputed here; the 422's offers reach the sheet as `PlanOffer`, compared whole.
@Suite("PlanOfferClientTests")
struct PlanOfferClientTests {
    static func nothingPretty(_ budget: String, more: String, back: String, minutes: String) -> CountingPlanTransport {
        let body = #"{"error":"nothing_pretty","budget_minutes":\#(budget),"more_time_minutes":\#(more),"#
            + #""back_roads_eta_s":\#(back),"back_roads_budget_minutes":\#(minutes)}"#
        return CountingPlanTransport(reply: PlanHTTPReply(status: 422, body: Data(body.utf8)))
    }

    static func expectedBody(budget: Int, backRoads: Bool) -> Data {
        let head = backRoads ? #"{"back_roads":true,"# : "{"
        return Data((head + #""budget_minutes":\#(budget),"destination":{"place":"42"},"#
            + #""origin":{"lat":34.01,"lon":-118.5},"vehicle":"standard"}"#).utf8)
    }

    @Test("a 422 nothing_pretty reaches the sheet as .offered, whole; then each offer is ONE request, bytes whole")
    func offerThenEachPlan() async throws {
        for backRoads in [false, true] {
            let first = Self.nothingPretty("25", more: "65", back: "3578.87", minutes: "32")
            var sheet = PlanSheetGateTests.ready(accepted: true, budget: 25)
            await PlanSheetGateTests.drive(&sheet, PlanSheetGateTests.planner(first))
            let offer = PlanOffer(budgetMinutes: 25, moreTimeMinutes: 65, backRoadsEtaSeconds: 3578.87,
                                  backRoadsBudgetMinutes: 32)
            guard case .offered(_, let held) = sheet.state else {
                Issue.record("the 422 left the sheet at \(sheet.state)")
                return
            }
            #expect(held == offer)
            #expect(await first.requests.map(\.body) == [Self.expectedBody(budget: 25, backRoads: false)])

            let second = CountingPlanTransport(reply: try PlanWire.recordedReply("200-plan"))
            let ticket = try #require(backRoads ? sheet.takeBackRoads() : sheet.takeMoreTime())
            sheet.finish(ticket, with: await PlanSheetGateTests.planner(second).plan(ticket))
            let budget = backRoads ? 32 : 65
            #expect(await second.requests.map(\.body) == [Self.expectedBody(budget: budget, backRoads: backRoads)])
        }
    }

    @Test("an offer that does not echo the ticket's budget, or is not whole minutes, is unexpectedResponse",
          arguments: [("30", "70", "null", "null"), ("25.5", "65.5", "null", "null")])
    func offerMustBeThisPlans(_ budget: String, _ more: String, _ back: String, _ minutes: String) async {
        var sheet = PlanSheetGateTests.ready(accepted: true, budget: 25)
        await PlanSheetGateTests.drive(&sheet, PlanSheetGateTests.planner(
            Self.nothingPretty(budget, more: more, back: back, minutes: minutes)))
        guard case .failed(_, .unexpectedResponse) = sheet.state else {
            Issue.record("budget \(budget) left the sheet at \(sheet.state)")
            return
        }
    }

    /// (name, back_roads_budget_minutes literal, back_roads_eta_s literal) -> accepted minutes, or nil = refused.
    static let minuteRows: [(String, String, String, Double??)] = [
        ("null accepted", "null", "3578.87", .some(nil)),
        ("0 accepted", "0", "3578.87", .some(0)),
        ("32 accepted", "32", "3578.87", .some(32)),
        ("180 accepted", "180", "3578.87", .some(180)),
        ("missing", "", "3578.87", nil),
        ("-1", "-1", "3578.87", nil),
        ("the next double below 0", "\((0.0).nextDown)", "3578.87", nil),
        ("the next double above 180", "\((180.0).nextUp)", "3578.87", nil),
        ("181", "181", "3578.87", nil),
        ("32.5", "32.5", "3578.87", nil),
        ("a string", #""32""#, "3578.87", nil),
        ("a bool", "true", "3578.87", nil),
        ("a budget beside no ETA", "32", "null", nil),
    ]

    @Test("A4: back_roads_budget_minutes is read fail-closed at every bound, through PlanResponseReader")
    func minutesBounds() async {
        for (name, minutes, back, accepted) in Self.minuteRows {
            let tail = minutes.isEmpty ? "" : #","back_roads_budget_minutes":\#(minutes)"#
            let body = #"{"error":"nothing_pretty","budget_minutes":25,"more_time_minutes":65,"#
                + #""back_roads_eta_s":\#(back)\#(tail)}"#
            let error = PlanWire.error(await PlanWire.plan(answering: PlanHTTPReply(status: 422,
                                                                                      body: Data(body.utf8))).outcome)
            let expected: PlanError = accepted.map {
                .nothingPretty(NothingPrettyOffer(budgetMinutes: 25, moreTimeMinutes: 65,
                                                  backRoadsEtaSeconds: back == "null" ? nil : 3578.87,
                                                  backRoadsBudgetMinutes: $0))
            } ?? .unexpectedResponse(status: 422)
            #expect(error == expected, "\(name)")
        }
    }
}
