import Foundation
@testable import ScenicKit
import Testing

/// T-0332 A1: ScenicKit's RouteScore, over `PlanTable(path:).scoredEdges`, equals a third, independent reading -
/// Tests/Fixtures/t0332/oracle.py's golden - on EVERY recorded router answer under Tests/Fixtures that carries
/// scenic_score. The Worker's routeScoreParity.test.ts reads the same golden, so the two ports are held to one file
/// neither of them wrote.
@Suite("RouteScoreParityTests")
struct RouteScoreParityTests {
    static let fixtures = URL(fileURLWithPath: #filePath)   // Tests/ScenicKitTests/<this file>
        .deletingLastPathComponent()
        .deletingLastPathComponent()
        .appendingPathComponent("Fixtures")
    static let tolerance = 1e-9

    struct Row: Decodable {
        let file: String
        let value: Double
        let mean: Double
        let p90: Double
        let dudFraction: Double
        let episodeCount: Int
        let totalLength: Double
    }

    struct Golden: Decodable {
        let threshold: Double
        let scores: [Row]
    }

    static func golden() throws -> Golden {
        let data = try Data(contentsOf: fixtures.appendingPathComponent("t0332/route-scores.json"))
        return try JSONDecoder().decode(Golden.self, from: data)
    }

    /// Every .json under Tests/Fixtures whose paths[0].details names scenic_score, relative, sorted.
    static func carrying() throws -> [String] {
        let root = fixtures.standardizedFileURL.path + "/"
        guard let walker = FileManager.default.enumerator(atPath: root) else { return [] }
        var names: [String] = []
        for case let name as String in walker where name.hasSuffix(".json") {
            guard let data = FileManager.default.contents(atPath: root + name),
                  let object = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let paths = object["paths"] as? [Any], let first = paths.first as? [String: Any],
                  let details = first["details"] as? [String: Any], details["scenic_score"] != nil else { continue }
            names.append(name.replacingOccurrences(of: "\\", with: "/"))
        }
        return names.sorted()
    }

    @Test("the golden lists exactly the recorded answers that carry scenic_score: 44, 24 below 0.45, 20 at or above")
    func goldenCoversThePopulation() throws {
        let golden = try Self.golden()
        #expect(golden.scores.map(\.file) == (try Self.carrying()))
        #expect(golden.threshold == RouteScore.honestFailureThreshold)
        #expect(golden.scores.count == 44)
        #expect(golden.scores.filter { $0.value < RouteScore.honestFailureThreshold }.count == 24)
        #expect(golden.scores.filter { $0.value >= RouteScore.honestFailureThreshold }.count == 20)
    }

    @Test("RouteScore over PlanTable.scoredEdges equals the golden on every file, field for field, to 1e-9")
    func everyFileMatches() throws {
        var misses: [String] = []
        for row in try Self.golden().scores {
            let data = try Data(contentsOf: Self.fixtures.appendingPathComponent(row.file))
            guard let score = RouteScore(edges: PlanTable(path: try RoutePath.decode(data)).scoredEdges) else {
                misses.append("\(row.file): nil")
                continue
            }
            let pairs = [(score.value, row.value), (score.mean, row.mean), (score.p90, row.p90),
                         (score.dudFraction, row.dudFraction), (score.totalLength, row.totalLength)]
            if pairs.contains(where: { !(abs($0.0 - $0.1) <= Self.tolerance) }) || score.episodeCount != row.episodeCount {
                misses.append("\(row.file): \(score)")
            }
        }
        #expect(misses == [])
    }

    @Test("scoredEdges leaves out unscored and zero-length rows and divides by 10")
    func scoredEdgesWhole() {
        let table = PlanTable(rows: [
            .init(wayId: 1, highway: "primary", scenicScore: 7, fromIndex: 0, toIndex: 1, meters: 900, seconds: 60),
            .init(wayId: 2, highway: "primary", scenicScore: nil, fromIndex: 1, toIndex: 2, meters: 500, seconds: 30),
            .init(wayId: 3, highway: "trunk", scenicScore: 0, fromIndex: 2, toIndex: 3, meters: 400, seconds: 20),
            .init(wayId: 4, highway: "trunk", scenicScore: 9, fromIndex: 3, toIndex: 3, meters: 0, seconds: 0),
        ])
        #expect(table.scoredEdges == [ScoredEdge(length: 900, score: 0.7), ScoredEdge(length: 400, score: 0)])
    }
}
