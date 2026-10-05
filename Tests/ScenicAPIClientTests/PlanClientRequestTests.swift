import Foundation
import ScenicAPIClient
import ScenicKit
import XCTest

/// T-0251 acceptance 1 and 3: the exact POST /plan request T-0248 ruled, the device-side refusals of P-PRIV-05
/// (a refused plan makes ZERO requests), and the counting fake counting one request per plan. Every case drives
/// `PlanClient.plan`, the entry point the app calls, and reads what reached the transport.
final class PlanClientRequestTests: XCTestCase {
    private let ok = PlanHTTPReply(status: 200, body: Data())

    private func request(_ body: String) -> PlanHTTPRequest {
        PlanHTTPRequest(url: URL(string: "https://scenic-api.test/plan")!, method: "POST",
                        headers: ["content-type": "application/json"], body: Data(body.utf8))
    }

    func testSendsExactlyTheBodyT0248Ruled() async {
        let (_, fake) = await PlanWire.plan(answering: ok, to: 1_234_567_890_123, budgetMinutes: 25)
        let sent = await fake.requests
        XCTAssertEqual(sent, [request(
            #"{"budget_minutes":25,"destination":{"place":"1234567890123"},"origin":{"lat":34.02,"lon":-118.49}}"#)])
    }

    func testDepartsAtIsSentAsAUTCInstantInWholeSeconds() async {
        let departs = Date(timeIntervalSince1970: 1_791_217_800.75)   // 2026-10-05T16:30:00.75Z
        let (_, fake) = await PlanWire.plan(answering: ok, to: 7, budgetMinutes: 0, departsAt: departs)
        let sent = await fake.requests
        XCTAssertEqual(sent, [request(#"{"budget_minutes":0,"departs_at":"2026-10-05T16:30:00Z","#
            + #""destination":{"place":"7"},"origin":{"lat":34.02,"lon":-118.49}}"#)])
    }

    func testBodyCarriesOneCoordinateAndAnIntegerPlace() async throws {
        let (_, fake) = await PlanWire.plan(answering: ok, to: 9_000_000_000_000_000_001)
        let first = await fake.requests.first
        let body = try XCTUnwrap(first?.body)
        let json = try XCTUnwrap(try JSONSerialization.jsonObject(with: body) as? [String: Any])
        XCTAssertEqual(Set(json.keys), ["origin", "destination", "budget_minutes"])
        let origin = try XCTUnwrap(json["origin"] as? [String: Any])
        XCTAssertEqual(Set(origin.keys), ["lat", "lon"])
        let destination = try XCTUnwrap(json["destination"] as? [String: Any])
        XCTAssertEqual(destination as? [String: String], ["place": "9000000000000000001"])
    }

    func testRefusesAThreeDecimalLatitudeAndSendsNothing() async {
        let (outcome, fake) = await PlanWire.plan(answering: ok,
                                                  from: Coordinate(latitude: 34.021, longitude: -118.49))
        XCTAssertEqual(PlanWire.error(outcome), .refusedOnDevice(.originMoreThanTwoDecimals))
        let count = await fake.count
        XCTAssertEqual(count, 0)
    }

    func testRefusesAThreeDecimalLongitudeAndSendsNothing() async {
        let (outcome, fake) = await PlanWire.plan(answering: ok,
                                                  from: Coordinate(latitude: 34.02, longitude: -118.491))
        XCTAssertEqual(PlanWire.error(outcome), .refusedOnDevice(.originMoreThanTwoDecimals))
        let count = await fake.count
        XCTAssertEqual(count, 0)
    }

    func testRefusesTheT0221FourDecimalOriginAndSendsNothing() async {
        let (outcome, fake) = await PlanWire.plan(answering: ok,
                                                  from: Coordinate(latitude: 34.0195, longitude: -118.4912))
        XCTAssertEqual(PlanWire.error(outcome), .refusedOnDevice(.originMoreThanTwoDecimals))
        let count = await fake.count
        XCTAssertEqual(count, 0)
    }

    func testTwoDecimalOriginsAtEveryEdgeAreSent() async {
        let edges = [Coordinate(latitude: 90, longitude: 180), Coordinate(latitude: -90, longitude: -180),
                     Coordinate(latitude: 0.01, longitude: -0.01), Coordinate(latitude: -33.87, longitude: 151.21)]
        for origin in edges {
            let (outcome, fake) = await PlanWire.plan(answering: ok, from: origin)
            XCTAssertNotEqual(PlanWire.error(outcome), .refusedOnDevice(.originMoreThanTwoDecimals), "\(origin)")
            XCTAssertNotEqual(PlanWire.error(outcome), .refusedOnDevice(.originOutOfRange), "\(origin)")
            let count = await fake.count
            XCTAssertEqual(count, 1, "\(origin)")
        }
    }

    func testRefusesAnOriginOutOfRangeOrNotFiniteAndSendsNothing() async {
        let outside = [Coordinate(latitude: 90.01, longitude: 0), Coordinate(latitude: -90.01, longitude: 0),
                       Coordinate(latitude: 0, longitude: 180.01), Coordinate(latitude: 0, longitude: -180.01),
                       Coordinate(latitude: .nan, longitude: 0), Coordinate(latitude: 0, longitude: .infinity)]
        for origin in outside {
            let (outcome, fake) = await PlanWire.plan(answering: ok, from: origin)
            XCTAssertEqual(PlanWire.error(outcome), .refusedOnDevice(.originOutOfRange), "\(origin)")
            let count = await fake.count
            XCTAssertEqual(count, 0, "\(origin)")
        }
    }

    func testBudgetIsSentInsideZeroTo180AndRefusedOutside() async {
        for minutes in [0, 180] {
            let (_, fake) = await PlanWire.plan(answering: ok, budgetMinutes: minutes)
            let count = await fake.count
            XCTAssertEqual(count, 1, "\(minutes)")
        }
        for minutes in [-1, 181] {
            let (outcome, fake) = await PlanWire.plan(answering: ok, budgetMinutes: minutes)
            XCTAssertEqual(PlanWire.error(outcome), .refusedOnDevice(.budgetOutOfRange), "\(minutes)")
            let count = await fake.count
            XCTAssertEqual(count, 0, "\(minutes)")
        }
    }

    func testCountingFakeCountsOneRequestPerPlan() async throws {
        let (outcome, fake) = await PlanWire.plan(answering: try PlanWire.recordedReply("200-plan"))
        XCTAssertNil(PlanWire.error(outcome))
        let count = await fake.count
        let peak = await fake.peakInFlight
        XCTAssertEqual(count, 1)
        XCTAssertEqual(peak, 1)
    }

    func testCountingFakeCountsEveryPlanThroughIt() async {
        let fake = CountingPlanTransport(reply: ok)
        for _ in 0..<3 {
            _ = await PlanWire.plan(through: fake)
        }
        let count = await fake.count
        let peak = await fake.peakInFlight
        XCTAssertEqual(count, 3)
        XCTAssertEqual(peak, 1)
    }
}
