import Foundation
import Testing
import ScenicKit
@testable import ScenicPlanCLI

/// T-0327: `ops/route-autopsy` over one recorded LA plan (T-0221's westwood-malibu, lambda 3.25, 166 rows).
///
/// Every test drives `AutopsyCommand.run(AutopsyArguments.parse(...))` - the call main.swift makes for
/// `ops/route-autopsy` - with the arguments a person types. The golden is FULL equality, line for line, over
/// the whole report; the other tests recompute what they can from inputs the tool did not make (the raw
/// `paths[0].time` of each recording, read through JSONSerialization; M and E from the terms file with the
/// plan's weights written out here as literals) so the golden is not the only witness.
@Suite("ops/route-autopsy golden (T-0327)")
struct RouteAutopsyGoldenTests {

    static let tests = URL(fileURLWithPath: #filePath)   // Tests/ScenicPlanCLITests/<this file>
        .deletingLastPathComponent()                     // Tests/ScenicPlanCLITests
        .deletingLastPathComponent()                     // Tests
    static let recording = tests.appendingPathComponent("Fixtures/t0221/westwood-malibu")
    static let termsFile = tests.appendingPathComponent("Fixtures/t0327/westwood-malibu-terms.json")
    static let goldenFile = tests.appendingPathComponent("Fixtures/t0327/westwood-malibu.autopsy.txt")

    /// What the T-0327 Log's runs typed.
    static let typed = ["34.0669,-118.4399", "34.0356,-118.6894", "25",
                        "--recorded", recording.path, "--terms", termsFile.path]

    struct Unreadable: Error { let what: String }

    static func run() throws -> [String] {
        try AutopsyCommand.run(AutopsyArguments.parse(typed))
    }

    static func golden() throws -> [String] {
        guard let data = FileManager.default.contents(atPath: goldenFile.path),
              let text = String(data: data, encoding: .utf8) else { throw Unreadable(what: goldenFile.path) }
        return text.split(separator: "\n", omittingEmptySubsequences: false).dropLast().map(String.init)
    }

    /// The cells of a row line, split on runs of spaces.
    static func cells(_ line: String) -> [String] {
        line.split(separator: " ", omittingEmptySubsequences: true).map(String.init)
    }

    @Test("the autopsy of westwood-malibu equals its golden, every line")
    func theAutopsyEqualsItsGolden() throws {
        let printed = try Self.run()
        let golden = try Self.golden()
        #expect(printed.count == golden.count)
        for (index, pair) in zip(printed, golden).enumerated() where pair.0 != pair.1 {
            Issue.record("line \(index + 1): printed `\(pair.0)`, golden `\(pair.1)`")
            break
        }
        #expect(printed == golden)
    }

    @Test("every trace step is a lambda the search measured, at the raw time of its recording")
    func everyTraceStepIsTheRawRecordedTime() throws {
        let printed = try Self.run()
        let steps = printed.filter { $0.hasPrefix("STEP ") }
        // `LAMBDA 3.25 evaluations=6 ...` - the count the plan line prints beside the trace.
        #expect(printed.contains { $0.hasPrefix("LAMBDA 3.25 evaluations=6 ") })
        #expect(printed.contains("TRACE steps=6 ceiling=52m47s"))
        #expect(steps.count == 6)
        // The ceiling from the raw fastest recording plus the 25 minutes typed, not from the tool.
        let fastestData = try #require(FileManager.default.contents(
            atPath: Self.recording.appendingPathComponent("fastest.json").path))
        let fastestRoot = try #require(try JSONSerialization.jsonObject(with: fastestData) as? [String: Any])
        let fastestTime = try #require((fastestRoot["paths"] as? [[String: Any]])?.first?["time"] as? Int)
        let ceiling = Double(fastestTime) / 1000 + 25 * 60
        var lambdas: [String] = []
        for line in steps {
            let c = Self.cells(line)
            guard c.count == 5 else { Issue.record("not a step row: \(line)"); continue }
            lambdas.append(c[2])
            let url = Self.recording.appendingPathComponent("lambda-\(c[2]).json")
            guard let data = FileManager.default.contents(atPath: url.path),
                  let root = try JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let paths = root["paths"] as? [[String: Any]], let time = paths.first?["time"] as? Int
            else { throw Unreadable(what: url.path) }
            #expect(c[3] == ScenicPlan.fixed(Double(time) / 1000, 3), "\(line)")
            #expect(c[4] == (Double(time) / 1000 <= ceiling ? "yes" : "no"), "\(line)")
        }
        #expect(lambdas == ["0", "4", "2", "3", "3.5", "3.25"])
    }

    /// M and E recomputed from the terms file with the plan's weights as literals, the gate from the tags by
    /// hand: 1073769540 carries access=private, every other way in the file is allowed.
    @Test("each way in the terms file prints its gate, M, E and score from ScenicKit")
    func termsRowsCarryGateAndAxes() throws {
        let printed = try Self.run()
        let data = try #require(FileManager.default.contents(atPath: Self.termsFile.path))
        let root = try #require(try JSONSerialization.jsonObject(with: data) as? [String: Any])
        let ways = try #require(root["ways"] as? [String: [String: Any]])
        #expect(ways.count == 4)
        for (id, way) in ways {
            let t = try #require(way["terms"] as? [String: Any])
            func n(_ key: String) -> Double { (t[key] as? Double) ?? .nan }
            let m = 0.45 * n("curvature") + 0.20 * n("elevationGain") + 0.20 * n("speedFit")
                + 0.15 * n("sinuosity")
            let bonus = ["none": 0.0, "eligible": 0.06, "designated": 0.15][t["bywayTier"] as? String ?? ""] ?? .nan
            var e = 0.24 * n("canopy") + 0.22 * n("relief") + 0.16 * (1 - n("impervious"))
                + 0.14 * n("pointsOfInterest") + 0.12 * n("water") + 0.12 * (1 - n("furniture"))
            if bonus > 0 { e = min(1, e + bonus) }
            let rows = printed.filter { Self.cells($0).first == id && Self.cells($0).count == 9 }
            #expect(!rows.isEmpty, "way \(id) has no row")
            for row in rows {
                let c = Self.cells(row)
                #expect(c[3] == (id == "1073769540" ? "refused:noAccess" : "allowed"), "\(row)")
                #expect(c[4] == ScenicPlan.fixed(m, 3), "\(row)")
                #expect(c[5] == ScenicPlan.fixed(e, 3), "\(row)")
            }
        }
    }

    @Test("a way the terms file does not carry prints dashes, never a default")
    func waysWithoutTermsPrintDashes() throws {
        let printed = try Self.run()
        #expect(printed.contains("EDGES rows=166 columns=way,highway,scenic_score,gate,M,E,score,metres,seconds"))
        let header = try #require(printed.firstIndex { $0.hasPrefix("WAY ") })
        let rows = Array(printed[(header + 1)...]).filter { Self.cells($0).count == 9 }
        #expect(rows.count == 166)
        let dashed = rows.filter { Array(Self.cells($0)[3...6]) == ["-", "-", "-", "-"] }
        #expect(dashed.count == 166 - 4)
    }
}
