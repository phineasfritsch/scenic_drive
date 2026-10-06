import Foundation
import Testing
@testable import ScenicKit

/// The Swift half of the shared road-trip fixture (T-0268 R6): Tests/Fixtures/t0268/trips.json is read by this
/// suite AND by services/api/test/roadTripParity.test.ts, and both compare every case's WHOLE outcome to the same
/// recorded answer by full equality. Two green suites over one file are the proof that the Worker's port and this
/// original give identical day plans.
@Suite("Road trip parity")
struct RoadTripParityTests {

    struct Fixture: Decodable {
        let route: [Edge]
        let places: [Place]
        let cases: [Case]
        let synthetic: [Synthetic]
    }

    struct Synthetic: Decodable {
        let name: String
        let route: [Edge]
        let places: [Place]
        let days: Int
        let max_drive_s: Int
        let max_m: Int
        let fastest_s: Int
        let expected: Expected
    }

    struct Edge: Decodable {
        let start: [Double]
        let end: [Double]
        let seconds: Int
        let meters: Int
    }

    struct Place: Decodable {
        let name: String
        let kind: String
        let score: Int
        let coordinate: [Double]
    }

    struct Case: Decodable {
        let name: String
        let days: Int
        let max_drive_s: Int
        let max_m: Int
        let fastest_s: Int
        let expected: Expected
    }

    struct Expected: Decodable, Equatable {
        let plan: [Day]?
        let over_budget: OverBudget?
        let too_few_days: TooFewDays?
    }

    struct OverBudget: Decodable, Equatable {
        let route_s: Int
        let ceiling_s: Int
    }

    struct TooFewDays: Decodable, Equatable {
        let days: Int
        let reached_vertex: Int
    }

    struct Day: Decodable, Equatable {
        let day: Int
        let start_vertex: Int
        let end_vertex: Int
        let seconds: Int
        let meters: Int
        let stops: [String]
        let overnight: Night?
    }

    struct Lodging: Decodable, Equatable {
        let name: String
        let meters: Int
    }

    /// The fixture's overnight: null (the last day), "no_lodging", or {lodging: {name, meters}}. Anything else is a
    /// decoding error, never a silent nil.
    enum Night: Decodable, Equatable {
        case lodging(Lodging)
        case noLodging

        init(from decoder: Decoder) throws {
            let container = try decoder.singleValueContainer()
            if let word = try? container.decode(String.self) {
                guard word == "no_lodging" else {
                    throw DecodingError.dataCorruptedError(in: container, debugDescription: "overnight \(word)")
                }
                self = .noLodging
                return
            }
            let wrapped = try container.decode([String: Lodging].self)
            guard wrapped.count == 1, let lodging = wrapped["lodging"] else {
                throw DecodingError.dataCorruptedError(in: container, debugDescription: "overnight is not {lodging}")
            }
            self = .lodging(lodging)
        }
    }

    static let file = URL(fileURLWithPath: #filePath)   // Tests/ScenicKitTests/<this file>
        .deletingLastPathComponent()                    // Tests/ScenicKitTests
        .deletingLastPathComponent()                    // Tests
        .appendingPathComponent("Fixtures/t0268/trips.json")

    static func fixture() throws -> Fixture {
        guard let data = FileManager.default.contents(atPath: file.path) else {
            throw PlanFailure.malformedResponse("the shared fixture is missing at \(file.path)")
        }
        return try JSONDecoder().decode(Fixture.self, from: data)
    }

    static func coordinate(_ pair: [Double]) -> Coordinate {
        Coordinate(latitude: pair[0], longitude: pair[1])
    }

    static func render(_ outcome: RoadTrip.Outcome) -> Expected {
        switch outcome {
        case let .overBudget(route, ceiling):
            return Expected(plan: nil, over_budget: OverBudget(route_s: route, ceiling_s: ceiling), too_few_days: nil)
        case let .tooFewDays(days, reached):
            return Expected(plan: nil, over_budget: nil, too_few_days: TooFewDays(days: days, reached_vertex: reached))
        case let .plan(days):
            return Expected(plan: days.map { d in
                let night: Night?
                switch d.overnight {
                case nil: night = nil
                case .noLodging?: night = .noLodging
                case let .lodging(name, meters)?: night = .lodging(Lodging(name: name, meters: meters))
                }
                return Day(day: d.day, start_vertex: d.startVertex, end_vertex: d.endVertex, seconds: d.seconds,
                           meters: d.meters, stops: d.stops, overnight: night)
            }, over_budget: nil, too_few_days: nil)
        }
    }

    @Test("the shared fixture carries the T-0249 route, its places and every outcome kind")
    func theFixtureIsWhole() throws {
        let fixture = try Self.fixture()
        let counts: [Int] = [fixture.route.count, fixture.places.count, fixture.cases.count, fixture.synthetic.count]
        #expect(counts == [21, 20, 9, 2])
        #expect(fixture.cases.contains { $0.expected.plan != nil })
        #expect(fixture.cases.contains { $0.expected.over_budget != nil })
        #expect(fixture.cases.contains { $0.expected.too_few_days != nil })
    }

    static func edges(_ route: [Edge]) -> [RoadTripEdge] {
        route.map {
            RoadTripEdge(start: coordinate($0.start), end: coordinate($0.end), seconds: $0.seconds, meters: $0.meters)
        }
    }

    static func places(_ list: [Place]) -> [RoadTripPlace] {
        list.map {
            RoadTripPlace(name: $0.name, kind: RoadTripPlace.Kind(rawValue: $0.kind)!, score: $0.score,
                          coordinate: coordinate($0.coordinate))
        }
    }

    @Test("every synthetic case gives the recorded day plan, whole, from the Swift original")
    func everySyntheticCaseMatches() throws {
        for shared in try Self.fixture().synthetic {
            let outcome = RoadTrip.plan(edges: Self.edges(shared.route), places: Self.places(shared.places),
                                        fastestSeconds: shared.fastest_s,
                                        limits: RoadTripLimits(days: shared.days, maxDriveSeconds: shared.max_drive_s,
                                                               maxMeters: shared.max_m))
            #expect(Self.render(outcome) == shared.expected, "\(shared.name)")
        }
    }

    @Test("every shared case gives the recorded day plan, whole, from the Swift original")
    func everyCaseMatches() throws {
        let fixture = try Self.fixture()
        let edges = Self.edges(fixture.route)
        let places = Self.places(fixture.places)
        for shared in fixture.cases {
            let outcome = RoadTrip.plan(edges: edges, places: places, fastestSeconds: shared.fastest_s,
                                        limits: RoadTripLimits(days: shared.days, maxDriveSeconds: shared.max_drive_s,
                                                               maxMeters: shared.max_m))
            #expect(Self.render(outcome) == shared.expected, "\(shared.name)")
        }
    }
}
