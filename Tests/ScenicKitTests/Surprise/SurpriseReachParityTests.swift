import Foundation
import Testing
@testable import ScenicKit

/// The Swift half of T-0263's shared reach fixture (R5): Tests/Fixtures/t0263/isochrone.json (a body as /isochrone
/// emits it) and points.json are read by this suite AND by services/api/test/surpriseReachParity.test.ts, and both
/// compare the WHOLE answer array to the recorded one. The body goes through `SurpriseIsochrone.decode`, the entry
/// point the app calls on the Worker's bytes.
@Suite("Surprise reach parity")
struct SurpriseReachParityTests {

    struct Points: Decodable {
        let points: [Point]
    }

    struct Point: Decodable, Equatable {
        let name: String
        let lat: Double
        let lon: Double
        let round_trip_minutes: Int?
    }

    struct Answer: Equatable, CustomStringConvertible {
        let name: String
        let minutes: Int?
        var description: String { "\(name)=\(minutes.map(String.init) ?? "nil")" }
    }

    static func data(_ name: String) throws -> Data {
        let url = URL(fileURLWithPath: #filePath)   // Tests/ScenicKitTests/Surprise/<this file>
            .deletingLastPathComponent()             // Tests/ScenicKitTests/Surprise
            .deletingLastPathComponent()             // Tests/ScenicKitTests
            .deletingLastPathComponent()             // Tests
            .appendingPathComponent("Fixtures/t0263/\(name)")
        guard let data = FileManager.default.contents(atPath: url.path) else {
            throw PlanFailure.malformedResponse("the shared fixture is missing at \(url.path)")
        }
        return data
    }

    static func points() throws -> [Point] {
        try JSONDecoder().decode(Points.self, from: try data("points.json")).points
    }

    /// One candidate per shared point, its name as the id: what reach(for:) is handed on the device.
    static func candidates() throws -> [SurpriseCandidate] {
        try points().map { p in
            SurpriseCandidate(id: p.name, name: p.name, hook: "", category: .viewpoint, corridor: "", brand: nil,
                              coordinate: Coordinate(latitude: p.lat, longitude: p.lon), quality: 0, approachScore: 0,
                              dwellMinutes: 0, opensMinute: nil, closesMinute: nil, hoursExempt: true, lit: true,
                              unpaved: false, privateApproach: false)
        }
    }

    /// The recorded answers as the map reach(for:) builds: a point outside every bucket is absent.
    static func recorded() throws -> [String: Int] {
        Dictionary(uniqueKeysWithValues: try points().compactMap { p in p.round_trip_minutes.map { (p.name, $0) } })
    }

    static func permutations<T>(_ items: [T]) -> [[T]] {
        guard let first = items.first else { return [[]] }
        return permutations(Array(items.dropFirst())).flatMap { rest in
            (0...rest.count).map { i -> [T] in
                var order = rest
                order.insert(first, at: i)
                return order
            }
        }
    }

    /// The fixture body with its dial (the top-level `minutes`, 90) replaced; the bucket minutes are 15/30/45.
    static func body(dial: Int) throws -> Data {
        let text = String(decoding: try data("isochrone.json"), as: UTF8.self)
        let dialed = text.replacingOccurrences(of: #"{"minutes": 90, "buckets""#,
                                               with: #"{"minutes": \#(dial), "buckets""#)
        guard dialed != text || dial == 90 else { throw PlanFailure.malformedResponse("the fixture's dial moved") }
        return Data(dialed.utf8)
    }

    @Test("every bucket order gives the recorded reach: the parity body's three buckets in all six orders")
    func everyBucketOrderGivesTheRecord() throws {
        let body = try SurpriseIsochrone.decode(try Self.data("isochrone.json"))
        let candidates = try Self.candidates()
        let orders = Self.permutations(body.buckets)
        #expect(Set(orders.map { $0.map(\.roundTripMinutes) }).count == 6)
        let expected = SurpriseReach(budgetMinutes: 90, roundTripMinutes: try Self.recorded())
        for order in orders {
            let reach = SurpriseIsochrone(minutes: body.minutes, buckets: order).reach(for: candidates)
            #expect(reach == expected, "buckets \(order.map(\.roundTripMinutes))")
        }
    }

    @Test("the reach's budget is the body's dial, not its largest bucket: dials 45, 100 and 240 over buckets ending at 90")
    func theBudgetIsTheDial() throws {
        #expect(try SurpriseIsochrone.decode(try Self.body(dial: 90)).buckets.last?.roundTripMinutes == 90)
        let candidates = try Self.candidates()
        let recorded = try Self.recorded()
        for dial in [45, 100, 240] {
            let reach = try SurpriseIsochrone.decode(try Self.body(dial: dial)).reach(for: candidates)
            #expect(reach == SurpriseReach(budgetMinutes: dial, roundTripMinutes: recorded))
        }
    }

    @Test("the shared reach fixture carries at least 40 points over at least 3 buckets, a hole among them")
    func theFixtureIsBigEnough() throws {
        let reach = try SurpriseIsochrone.decode(try Self.data("isochrone.json"))
        let points = try Self.points()
        #expect(points.count >= 40)
        #expect(reach.buckets.count >= 3)
        #expect(reach.buckets.contains { $0.polygon.coordinates.count > 1 })
        #expect(Set(points.map(\.round_trip_minutes)) == Set(reach.buckets.map(\.roundTripMinutes) + [nil]))
    }

    @Test("every shared point gets the TS reference's recorded round-trip minutes from the decoded body")
    func everyPointMatchesTheRecord() throws {
        let reach = try SurpriseIsochrone.decode(try Self.data("isochrone.json"))
        let points = try Self.points()
        let actual = points.map { p in
            Answer(name: p.name, minutes: reach.roundTripMinutes(at: Coordinate(latitude: p.lat, longitude: p.lon)))
        }
        #expect(actual == points.map { Answer(name: $0.name, minutes: $0.round_trip_minutes) })
    }
}
