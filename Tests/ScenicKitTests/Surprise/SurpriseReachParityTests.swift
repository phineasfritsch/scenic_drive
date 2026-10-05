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
