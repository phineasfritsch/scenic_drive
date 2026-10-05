import Foundation
@testable import ScenicKit

/// T-0249 R7's synthetic, ruled LA -> Big Sur route (Tests/Fixtures/roadtrip/route.tsv) and its 20 candidate
/// places (places.tsv), plus the one rendering every road-trip test compares by exact equality.
///
/// The rendering reads each produced day's PROPERTIES into a string and the tests compare those strings to
/// literals, never a produced `RoadTripDay` to one built through the same init: an init that swapped two
/// fields would otherwise move both sides at once.
enum RoadTripFixture {
    static func file(_ name: String) throws -> [[String]] {
        let url = URL(fileURLWithPath: #filePath)   // Tests/ScenicKitTests/RoadTrip/<this file>
            .deletingLastPathComponent()             // Tests/ScenicKitTests/RoadTrip
            .deletingLastPathComponent()             // Tests/ScenicKitTests
            .deletingLastPathComponent()             // Tests
            .appendingPathComponent("Fixtures/roadtrip/\(name)")
        return try String(contentsOf: url, encoding: .utf8)
            .split(separator: "\n").map { String($0) }
            .filter { !$0.hasPrefix("#") && !$0.isEmpty }
            .map { $0.split(separator: "\t", omittingEmptySubsequences: false).map { String($0) } }
    }

    static func edges() throws -> [RoadTripEdge] {
        try file("route.tsv").map { f in
            RoadTripEdge(start: Coordinate(latitude: Double(f[2])!, longitude: Double(f[3])!),
                         end: Coordinate(latitude: Double(f[4])!, longitude: Double(f[5])!),
                         seconds: Int(f[6])!, meters: Int(f[7])!)
        }
    }

    /// Vertex names in route order: vertex i is row i's `from`, the last vertex the last row's `to`.
    static func vertexNames() throws -> [String] {
        let rows = try file("route.tsv")
        return rows.map { $0[0] } + [rows[rows.count - 1][1]]
    }

    static func places() throws -> [RoadTripPlace] {
        try file("places.tsv").map { f in
            RoadTripPlace(name: f[0], kind: RoadTripPlace.Kind(rawValue: f[1])!, score: Int(f[2])!,
                          coordinate: Coordinate(latitude: Double(f[3])!, longitude: Double(f[4])!))
        }
    }

    /// Fastest LA -> Big Sur, ruled in R8 so that the fixture route sits exactly on the +40% ceiling.
    static let fastestSeconds = 20_411

    static func run(_ limits: RoadTripLimits, fastest: Int = fastestSeconds) throws -> [String] {
        render(RoadTrip.plan(edges: try edges(), places: try places(), fastestSeconds: fastest, limits: limits),
               names: try vertexNames())
    }

    static func render(_ outcome: RoadTrip.Outcome, names: [String]) -> [String] {
        switch outcome {
        case let .overBudget(route, ceiling):
            return ["overBudget route=\(route) ceiling=\(ceiling)"]
        case let .tooFewDays(days, reached):
            return ["tooFewDays days=\(days) reached=v\(reached)"]
        case let .plan(days):
            return days.map { d in
                let night: String
                switch d.overnight {
                case nil: night = "arrive"
                case .noLodging?: night = "noLodging"
                case let .lodging(name, meters)?: night = "\(name) \(meters)m"
                }
                let from = d.startVertex < names.count ? names[d.startVertex] : "?"
                let to = d.endVertex < names.count ? names[d.endVertex] : "?"
                return "day \(d.day) v\(d.startVertex) \(from) -> v\(d.endVertex) \(to) \(d.seconds)s \(d.meters)m "
                    + "[\(d.stops.joined(separator: ", "))] \(night)"
            }
        }
    }
}
