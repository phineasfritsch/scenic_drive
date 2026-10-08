import Foundation
import Handoff
import ScenicKit
import Testing

/// T-0313 R6: a road-trip day's pins and its split into Apple Maps URLs, each compared by FULL equality to URLs built
/// here from hand-listed pins.
@Suite("TripDayHandoffTests")
struct TripDayHandoffTests {
    /// Points up a meridian, `step` degrees of latitude apart (0.1 deg is 11,119.5 m; 0.2 deg is 22,239 m).
    static func meridian(_ step: Double, _ count: Int) -> [Coordinate] {
        (0..<count).map { Coordinate(latitude: 30 + Double($0) * step, longitude: -118) }
    }

    static func parts(_ path: [Coordinate], _ legs: [(Int, [Int], Int)]) -> [AppleMapsDirections] {
        legs.map { leg in
            AppleMapsDirections(source: path[leg.0], destination: path[leg.2], waypoints: leg.1.map { index in path[index] })
        }
    }

    static let splits: [(Int, [(Int, [Int], Int)])] = [
        (2, [(0, [], 1)]),
        (11, [(0, Array(1...9), 10)]),
        (12, [(0, Array(1...9), 10), (10, [], 11)]),
        (21, [(0, Array(1...9), 10), (10, Array(11...19), 20)]),
        (22, [(0, Array(1...9), 10), (10, Array(11...19), 20), (20, [], 21)]),
    ]

    @Test("a pin at the first vertex at or past each 20 km, never the ends")
    func pinsEveryTwentyKilometres() {
        let path = Self.meridian(0.1, 12)
        #expect(TripDayHandoff.pins(along: path) == [2, 4, 6, 8, 9].map { path[$0] })
        #expect(TripDayHandoff.pins(along: Self.meridian(0.1, 2)) == [])
        #expect(TripDayHandoff.pins(along: Self.meridian(0.1, 1)) == [])
    }

    @Test("one long step past two multiples is one pin, and the next pin waits for the next multiple")
    func longStep() {
        let path = [30.0, 30.5, 30.52, 30.6].map { Coordinate(latitude: $0, longitude: -118) }
        #expect(TripDayHandoff.pins(along: path) == [path[1]])
    }

    @Test("a day splits into URLs of at most nine waypoints, chained end to start", arguments: splits)
    func split(_ count: Int, _ legs: [(Int, [Int], Int)]) throws {
        let path = Self.meridian(0.2, count)
        let expected = Self.parts(path, legs)
        #expect(TripDayHandoff.parts(along: path) == expected)
        #expect(try TripDayHandoff.urls(along: path) == expected.map { try $0.url() })
        #expect(TripDayHandoff.parts(along: path).allSatisfy { $0.waypoints.count <= AppleMapsDirections.maxWaypoints })
    }

    @Test("a path of fewer than two points has no handoff")
    func tooShort() throws {
        #expect(TripDayHandoff.parts(along: []) == [])
        #expect(TripDayHandoff.parts(along: Self.meridian(0.2, 1)) == [])
        #expect(try TripDayHandoff.urls(along: []) == [])
    }
}
