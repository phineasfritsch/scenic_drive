import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0362 A7 (R1, P-PRIV-05): planning to a searched row sends its place id and ONE coordinate - the origin, at 2 dp.
/// The request bodies of a plan and of its reroute through PlanClient (the shipped client) EQUAL the bytes written out
/// here, and a walk over every JSON object in them finds exactly one {lat, lon}, each value at no more than 2 dp.
@Suite("PlanClientSearchedPlaceTests") struct PlanClientSearchedPlaceTests {
    static let searched: Int64 = -4_503_599_627_370_496
    static let planBody = #"{"budget_minutes":25,"destination":{"place":"-4503599627370496"},"#
        + #""origin":{"lat":34.02,"lon":-118.49},"vehicle":"standard"}"#
    static let rerouteBody = #"{"budget_minutes":25,"destination":{"place":"-4503599627370496"},"#
        + #""origin":{"lat":34.02,"lon":-118.5},"reroute":{"first_pin":1,"token":"0f1e2d3c-4b5a-4968-8776-655443322110"},"#
        + #""vehicle":"standard"}"#

    static func client(_ fake: CountingPlanTransport) -> PlanClient {
        PlanClient(base: PlanWire.base, transport: fake, installID: PlanWire.install, accountToken: nil, session: nil)
    }

    /// Every {lat, lon}-keyed object anywhere in the body, and every number under those keys.
    static func coordinates(_ value: Any) -> [[Double]] {
        if let object = value as? [String: Any] {
            let here: [[Double]] = object["lat"] != nil || object["lon"] != nil
                ? [[object["lat"], object["lon"]].compactMap { ($0 as? NSNumber)?.doubleValue }] : []
            return here + object.values.flatMap(coordinates)
        }
        if let array = value as? [Any] { return array.flatMap(coordinates) }
        return []
    }

    static func oneCoordinateAtTwoDecimals(_ body: Data) -> Bool {
        guard let json = try? JSONSerialization.jsonObject(with: body) else { return false }
        let found = coordinates(json)
        return found.count == 1 && found[0].count == 2 && found[0].allSatisfy { ($0 * 100).rounded() / 100 == $0 }
    }

    @Test("a plan to a searched place: the id as the destination, the origin the one coordinate")
    func plan() async throws {
        let fake = CountingPlanTransport(reply: try PlanWire.recordedReply("200-plan"))
        _ = try? await Self.client(fake).plan(from: PlanWire.santaMonica, to: Self.searched, budgetMinutes: 25)
        let bodies = await fake.requests.map(\.body)
        #expect(bodies == [Data(Self.planBody.utf8)])
        #expect(bodies.map(Self.oneCoordinateAtTwoDecimals) == [true])
    }

    @Test("its reroute: the id, the token, and the fix rounded to 2 dp on the device - still one coordinate")
    func reroute() async throws {
        let fake = CountingPlanTransport(reply: try PlanWire.recordedReply("200-plan"))
        let fix = RerouteRequest(origin: Coordinate(latitude: 34.0212345, longitude: -118.4987654),
                                 remainingWaypoints: [Coordinate(latitude: 34.0412345, longitude: -118.5612345)],
                                 firstRemainingWaypoint: 1, destination: Coordinate(latitude: 34.0676, longitude: -118.5957),
                                 lambda: 7.75)
        _ = try? await Self.client(fake).reroute(fix, token: "0f1e2d3c-4b5a-4968-8776-655443322110", place: Self.searched,
                                                 budgetMinutes: 25)
        let bodies = await fake.requests.map(\.body)
        #expect(bodies == [Data(Self.rerouteBody.utf8)])
        #expect(bodies.map(Self.oneCoordinateAtTwoDecimals) == [true])
    }

    @Test("the walk sees a second coordinate and a third decimal - it is not vacuous")
    func walkSeesExtras() {
        let two = #"{"destination":{"lat":34.07,"lon":-118.6},"origin":{"lat":34.02,"lon":-118.49}}"#
        let three = #"{"origin":{"lat":34.021,"lon":-118.49}}"#
        #expect([two, three, Self.planBody].map { Self.oneCoordinateAtTwoDecimals(Data($0.utf8)) } == [false, false, true])
    }
}
