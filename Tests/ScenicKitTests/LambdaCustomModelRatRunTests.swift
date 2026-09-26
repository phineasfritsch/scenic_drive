import Foundation
import Testing
@testable import ScenicKit

/// T-0244: the per-request model over LA. Every test here reads `LambdaCustomModel.json(for:)` - the bytes
/// GraphHopperRouteSource sends and `ops/plan --emit-model` prints - through `CustomModelChain`, so what is
/// asserted is what the router is asked, not how the model was assembled.
///
/// The defect (T-0209 V4): the anti-rat-run clause was a constant x0.5 while the bands fall as 1/(1+lambda),
/// so at lambda 8 a score-4 residential edge cost 10 against 9 for a score-0 arterial and Santa Monica ->
/// Topanga drove 813.9 m of 7th Street.
@Suite("Lambda custom model: rat-runs, monotone T, the band ladder")
struct LambdaCustomModelRatRunTests {

    static let minorClasses = ["residential", "living_street", "service"]

    static func chain(_ lambda: Double) throws -> CustomModelChain {
        try CustomModelChain(json: LambdaCustomModel.json(for: lambda))
    }

    @Test("residential at lambda 8: a minor road below 7 costs 1 + 2 lambda, and its ratio to the dullest arterial rises with lambda")
    func minorRoadPenaltyScalesWithLambda() throws {
        let eight = try Self.chain(8)
        // 7th Street's own ways: 121941230 (score 4) and 384819177 (score 2).
        #expect(try eight.cost(roadClass: "residential", score: 4) == 1 / 0.058824)
        #expect(try eight.cost(roadClass: "residential", score: 2) == 1 / 0.058824)
        var previous = 0.0
        for tenths in 1...80 {
            let chain = try Self.chain(Double(tenths) / 10)
            let dullest = try chain.cost(roadClass: "primary", score: 0)
            for roadClass in Self.minorClasses {
                for score in 0...6 {
                    let ratio = try chain.cost(roadClass: roadClass, score: score) / dullest
                    #expect(ratio > 1, "\(roadClass) score \(score) at lambda \(Double(tenths) / 10)")
                    #expect(ratio >= previous - 1e-6, "\(roadClass) score \(score) ratio fell at lambda \(Double(tenths) / 10)")
                }
            }
            previous = try chain.cost(roadClass: "residential", score: 4) / dullest
        }
        #expect(previous >= 1.8)
        // A minor road the scorer rates 7 or more is a scenic road, not a rat-run: never penalised.
        #expect(try eight.cost(roadClass: "residential", score: 7) == 1)
    }

    @Test("the request model sets distance_influence 0 and is the identity at lambda 0")
    func distanceInfluenceIsZeroSoTIsWhatLambdaZeroMinimises() throws {
        for tenths in 0...80 {
            #expect(try Self.chain(Double(tenths) / 10).distanceInfluence == 0)
        }
        let zero = try Self.chain(0)
        for roadClass in Self.minorClasses + ["primary", "secondary", "tertiary", "motorway", "unclassified"] {
            for score in 0...10 {
                #expect(try zero.multiplier(roadClass: roadClass, score: score) == 1, "\(roadClass) \(score)")
            }
        }
    }

    @Test("the band ladder: one band per integer score below 7, each priority 1 / (1 + lambda (7 - s) / 7)")
    func oneBandPerScoreBelowSeven() throws {
        let seven = try Self.chain(7)
        #expect(seven.scoreThresholds == [7, 6, 5, 4, 3, 2, 1])
        for score in 0...10 {
            // At lambda 7 the slope (7 - s) / 7 makes the cost exactly 1 + (7 - s): 8 for score 0, 2 for score 6.
            let expected = score >= 7 ? 1.0 : 1 + Double(7 - score)
            let cost = try seven.cost(roadClass: "secondary", score: score)
            #expect(abs(cost - expected) < 1e-4 * expected, "score \(score): cost \(cost), expected \(expected)")
        }
    }

    // MARK: - the recorded route

    static let fixtures = URL(fileURLWithPath: #filePath)
        .deletingLastPathComponent().deletingLastPathComponent()
        .appendingPathComponent("Fixtures/t0244")

    @Test("Santa Monica -> Topanga at lambda 8, as routed over the whole-LA graph, has no rat-run over 800 m")
    func santaMonicaTopangaAtLambdaEightHasNoRatRun() throws {
        let model = try String(contentsOf: Self.fixtures.appendingPathComponent("santa-monica-topanga-lambda-8.model.json"),
                               encoding: .utf8)
        // The recording is bound to the shipping model: a model change makes this fixture stale, by name.
        #expect(model == (try LambdaCustomModel.json(for: 8)) + "\n", "the recorded route was not routed with today's model")
        let rows = try String(contentsOf: Self.fixtures.appendingPathComponent("santa-monica-topanga-lambda-8.edges.tsv"),
                              encoding: .utf8)
            .split(separator: "\n").dropFirst().map { $0.split(separator: "\t").map(String.init) }
        #expect(rows.count > 100, "the recording is a whole route, not a stub")
        var run = 0.0
        var longest = 0.0
        for row in rows {
            let minor = Self.minorClasses.contains(row[1])
            if minor, let score = Int(row[4]), score < 7, let metres = Double(row[3]) {
                run += metres
                longest = max(longest, run)
            } else {
                run = 0
            }
        }
        #expect(longest <= 800, "a \(longest) m run of minor roads scored below 7")
    }
}
