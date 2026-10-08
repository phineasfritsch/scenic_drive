import Foundation
import Testing
import ScenicKit
@testable import ScenicPlanCLI

/// T-0327 rv1: the values the autopsy prints that ScenicKit owns. That covers RouteScore over an unscored
/// stretch, FITS at the ceiling and its neighbours, and the cells of terms SegmentScore refuses. Each one is
/// tested over an input that holds the case. The only recorded fixture holds none of them.
@Suite("ops/route-autopsy boundaries (T-0327 rv1)")
struct RouteAutopsyBoundaryTests {

    typealias Golden = RouteAutopsyGoldenTests

    static let recordings = ["fastest.json", "lambda-0.json", "lambda-4.json", "lambda-2.json", "lambda-3.json",
                             "lambda-3.5.json", "lambda-3.25.json"]

    /// westwood-malibu copied byte for byte, except that the chosen route's scenic_score details lose the
    /// interval over points 13..21. A real router answer with a stretch it did not score.
    static func unscoredVariant() throws -> URL {
        let dir = FileManager.default.temporaryDirectory.appendingPathComponent("t0327-unscored-\(UUID())")
        try FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        for name in recordings {
            let data = try #require(FileManager.default.contents(
                atPath: Golden.recording.appendingPathComponent(name).path))
            var text = String(decoding: data, as: UTF8.self)
            if name == "lambda-3.25.json" {
                #expect(text.components(separatedBy: "[13, 21, 4], ").count == 2)
                text = text.replacingOccurrences(of: "[13, 21, 4], ", with: "")
            }
            try Data(text.utf8).write(to: dir.appendingPathComponent(name))
        }
        return dir
    }

    static func plan(recorded dir: URL) throws -> ScenicPlan {
        let typed = try AutopsyArguments.parse(["34.0669,-118.4399", "34.0356,-118.6894", "25",
                                                "--recorded", dir.path]).plan
        return try ScenicPlanner(source: RecordedRouteSource(directory: dir), maxEvaluations: typed.maxEvaluations)
            .plan(from: typed.origin, to: typed.destination, budget: typed.budget)
    }

    static func routeScoreLine(_ edges: [ScoredEdge], unscored: Double) -> String {
        let tail = " unscored=\(ScenicPlan.fixed(unscored, 1))m"
        guard let r = RouteScore(edges: edges) else { return "ROUTESCORE none" + tail }
        return "ROUTESCORE value=\(ScenicPlan.fixed(r.value, 3)) mean=\(ScenicPlan.fixed(r.mean, 3)) "
            + "p90=\(ScenicPlan.fixed(r.p90, 3)) dud=\(ScenicPlan.fixed(r.dudFraction, 3)) "
            + "episodes=\(r.episodeCount) honest-failure=\(r.isHonestFailure) "
            + "scored=\(ScenicPlan.fixed(r.totalLength, 1))m" + tail
    }

    @Test("an unscored stretch is left out of RouteScore and printed as unscored metres, never scored 0")
    func unscoredStretchIsNotADullOne() throws {
        let dir = try Self.unscoredVariant()
        defer { try? FileManager.default.removeItem(at: dir) }
        let printed = try AutopsyCommand.run(AutopsyArguments.parse(
            ["34.0669,-118.4399", "34.0356,-118.6894", "25", "--recorded", dir.path,
             "--terms", Golden.termsFile.path]))
        let plan = try Self.plan(recorded: dir)
        #expect(plan.outcome.lambda == 3.25)
        let rows = plan.table.rows.filter { $0.meters > 0 }
        let scored = rows.compactMap { row in
            row.scenicScore.map { ScoredEdge(length: row.meters, score: Double($0) / 10) } }
        let unscored = rows.filter { $0.scenicScore == nil }.map(\.meters).reduce(0, +)
        #expect(unscored > 0)
        let expected = Self.routeScoreLine(scored, unscored: unscored)
        let zeroed = Self.routeScoreLine(rows.map { ScoredEdge(length: $0.meters,
                                                                score: Double($0.scenicScore ?? 0) / 10) },
                                         unscored: 0)
        #expect(expected != zeroed)
        #expect(printed.filter { $0.hasPrefix("ROUTESCORE ") } == [expected])
    }

    /// The step durations, as offsets around the plan's own ceiling, and the FITS each must print: the
    /// ceiling is a ceiling, so exactly on it fits and one ulp over does not.
    static func fitTable(_ plan: ScenicPlan) -> [(duration: TimeInterval, fits: String)] {
        [(plan.ceiling, "yes"), (plan.ceiling.nextUp, "no"), (plan.ceiling.nextDown, "yes"), (0, "yes"),
         (plan.fastestDuration, "yes"), (plan.ceiling + 1, "no")]
    }

    @Test("FITS is LambdaSearch's verdict: exactly the ceiling fits, one ulp over does not, one under does")
    func fitsIsTheBudgetCeiling() throws {
        let plan = try Self.plan(recorded: Golden.recording)
        let table = Self.fitTable(plan)
        let steps = table.enumerated().map { TracingRouteSource.Step(lambda: Double($0.offset), duration: $0.element.duration) }
        let printed = AutopsyReport(plan: plan, steps: steps, terms: nil).lines()
        let fits = printed.filter { $0.hasPrefix("STEP ") }.map { Golden.cells($0).last ?? "" }
        #expect(fits == table.map(\.fits))
        // LambdaSearch itself, on the same numbers: the ceiling it searches under is the plan's ceiling.
        let search = try LambdaSearch(fastest: plan.fastestDuration, budget: plan.budget)
        #expect(search.ceiling == plan.ceiling)
    }

    /// The SegmentScore refusals: every unit term outside 0...1 on each side, including one ulp out, plus a
    /// negative tunnel and a negative motorway distance. The scored bounds are the same table's other half.
    static func termCases() -> [(name: String, terms: [String: Any], refused: Bool)] {
        var base: [String: Any] = ["bywayTier": "none", "tunnelMeters": 0.0, "metersToNearestMotorway": NSNull()]
        for name in AutopsyTerms.unitTermNames { base[name] = 0.5 }
        func with(_ key: String, _ value: Any) -> [String: Any] { var t = base; t[key] = value; return t }
        var cases: [(name: String, terms: [String: Any], refused: Bool)] = []
        for name in AutopsyTerms.unitTermNames {
            for v in [1.5, -0.5, (1.0).nextUp, (0.0).nextDown] { cases.append(("\(name)=\(v)", with(name, v), true)) }
            for v in [0.0, 1.0] { cases.append(("\(name)=\(v)", with(name, v), false)) }
        }
        cases.append(("tunnelMeters=-1", with("tunnelMeters", -1.0), true))
        cases.append(("metersToNearestMotorway=-1", with("metersToNearestMotorway", -1.0), true))
        cases.append(("metersToNearestMotorway=0", with("metersToNearestMotorway", 0.0), false))
        cases.append(("base", base, false))
        return cases
    }

    @Test("terms SegmentScore refuses print invalid in M, E and SCORE, never a number")
    func refusedTermsPrintInvalid() throws {
        let cases = Self.termCases()
        #expect(cases.filter(\.refused).count == AutopsyTerms.unitTermNames.count * 4 + 2)
        var ids: [Int] = []
        for line in try Golden.run() {
            let c = Golden.cells(line)
            if c.count == 9, let id = Int(c[0]), !ids.contains(id) { ids.append(id) }
        }
        #expect(ids.count >= 9)
        var printedCases = Set<String>()
        var start = 0
        while start < cases.count {
            let chunk = Array(cases[start..<min(start + ids.count, cases.count)])
            start += chunk.count
            var ways: [String: Any] = [:]
            for (index, c) in chunk.enumerated() {
                ways[String(ids[index])] = ["tags": ["highway": "tertiary"], "terms": c.terms]
            }
            let file = FileManager.default.temporaryDirectory.appendingPathComponent("t0327-refusals-\(UUID()).json")
            defer { try? FileManager.default.removeItem(at: file) }
            try JSONSerialization.data(withJSONObject: ["source": "T-0327 refusal table", "ways": ways]).write(to: file)
            let decoded = try AutopsyTerms.load(file)
            var expectedById: [String: [String]] = [:]
            for (index, c) in chunk.enumerated() {
                let terms = try #require(decoded.ways[ids[index]]?.terms)
                #expect((SegmentScore.score(for: terms) == nil) == c.refused, "\(c.name)")
                if let score = SegmentScore.score(for: terms) {
                    let axes = SegmentScore.axes(for: terms)
                    expectedById[String(ids[index])] = [ScenicPlan.fixed(axes.drive, 3),
                                                        ScenicPlan.fixed(axes.scenery, 3), ScenicPlan.fixed(score, 3)]
                } else {
                    expectedById[String(ids[index])] = ["invalid", "invalid", "invalid"]
                }
            }
            var typed = Golden.typed
            typed[typed.count - 1] = file.path
            let lines = try AutopsyCommand.run(AutopsyArguments.parse(typed))
            let header = try #require(lines.firstIndex { $0.hasPrefix("WAY ") })
            let rows = lines[(header + 1)...].map(Golden.cells).filter { $0.count == 9 }
            #expect(rows.count == 166)
            #expect(rows.map { Array($0[4...6]) } == rows.map { expectedById[$0[0]] ?? ["-", "-", "-"] })
            for (index, c) in chunk.enumerated() where rows.contains(where: { $0[0] == String(ids[index]) }) {
                printedCases.insert(c.name)
            }
        }
        #expect(printedCases == Set(cases.map(\.name)))
    }
}
