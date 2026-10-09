import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0342 R4: a 200's `time_runs` - GraphHopper's per-edge free-flow times over the drawn route, whole ms - reach the
/// preview whole. Absent reads nil (the estimate badge stays on); present must tile the decoded route by the shipping
/// rule, CorridorRoute(route:timeRuns:), or the whole answer is refused. Every plan goes through `PlanClient.plan`.
@Suite struct PlanTimeRunsTests {
    enum Outcome: Equatable {
        case decoded([CorridorTimeRun]?)
        case refused
    }

    /// PlanResponseDecodeTests' distinct body (a three-vertex route), with `time_runs` appended when given.
    static func body(_ timeRuns: String?) -> Data {
        var text = PlanResponseDecodeTests.body
        if let timeRuns {
            text.removeLast()
            text += #","time_runs":"# + timeRuns + "}"
        }
        return Data(text.utf8)
    }

    /// The distinct body's PlanResponse, field by field, with `runs`.
    static func expected(_ runs: [CorridorTimeRun]?) -> PlanResponse {
        let e = PlanResponseDecodeTests.expected
        return PlanResponse(route: e.route, distanceMeters: e.distanceMeters, etaSeconds: e.etaSeconds,
                            fastestEtaSeconds: e.fastestEtaSeconds, ceilingSeconds: e.ceilingSeconds,
                            budgetSeconds: e.budgetSeconds, lambda: e.lambda, evaluations: e.evaluations,
                            usedBudget: e.usedBudget, etaIsEstimate: e.etaIsEstimate, hazards: e.hazards,
                            waypoints: e.waypoints, appleMapsURL: e.appleMapsURL, planToken: e.planToken,
                            continued: e.continued, timeRuns: runs)
    }

    static func run(_ from: Int, _ to: Int, _ ms: Int) -> CorridorTimeRun {
        CorridorTimeRun(from: from, to: to, milliseconds: ms)
    }

    static func json(_ runs: [(Int, Int, Int)]) -> String {
        "[" + runs.map { #"{"from":\#($0.0),"to":\#($0.1),"ms":\#($0.2)}"# }.joined(separator: ",") + "]"
    }

    /// The route's vertices are 0, 1 and 2: every bound of the tiling, every wrong type, each key missing.
    static let rows: [(String, String?, Outcome)] = [
        ("absent", nil, .decoded(nil)),
        ("one run per edge", json([(0, 1, 61000), (1, 2, 59000)]), .decoded([run(0, 1, 61000), run(1, 2, 59000)])),
        ("one run over the route", json([(0, 2, 120_000)]), .decoded([run(0, 2, 120_000)])),
        ("a zero run beside a positive one", json([(0, 1, 0), (1, 2, 1)]), .decoded([run(0, 1, 0), run(1, 2, 1)])),
        ("empty", "[]", .refused),
        ("null", "null", .refused),
        ("the first from 1", json([(1, 2, 5)]), .refused),
        ("an overlap", json([(0, 1, 5), (0, 2, 5)]), .refused),
        ("a gap", json([(0, 1, 5), (2, 2, 5)]), .refused),
        ("to equal to from", json([(0, 0, 5), (0, 2, 5)]), .refused),
        ("ends one vertex short", json([(0, 1, 5)]), .refused),
        ("ends one vertex past", json([(0, 3, 5)]), .refused),
        ("a negative ms", json([(0, 1, 5), (1, 2, -1)]), .refused),
        ("every ms zero", json([(0, 1, 0), (1, 2, 0)]), .refused),
        ("a fractional ms", #"[{"from":0,"to":2,"ms":1000.5}]"#, .refused),
        ("a string ms", #"[{"from":0,"to":2,"ms":"1000"}]"#, .refused),
        ("ms missing", #"[{"from":0,"to":2}]"#, .refused),
        ("from missing", #"[{"to":2,"ms":5}]"#, .refused),
        ("to missing", #"[{"from":0,"ms":5}]"#, .refused),
        ("an object, not a list", #"{"from":0,"to":2,"ms":5}"#, .refused),
        ("a run as a triple", "[[0,2,5]]", .refused),
    ]

    @Test("a 200's time_runs decode whole when they tile the route; absent is nil; every bound refused")
    func decodeTable() async throws {
        for (name, fragment, outcome) in Self.rows {
            let (result, fake) = await PlanWire.plan(answering: PlanHTTPReply(status: 200, body: Self.body(fragment)))
            #expect(await fake.count == 1, "\(name)")
            switch outcome {
            case .decoded(let runs):
                #expect((try? result.get()) == Self.expected(runs), "\(name)")
            case .refused:
                #expect(PlanWire.error(result) == .unexpectedResponse(status: 200), "\(name)")
            }
        }
    }

    struct FreeFlow: TrafficProvider {
        func retime(_ edges: [CorridorEdge], departsAt: Date) -> RetimedRoute {
            RetimedRoute(edgeSeconds: edges.map(\.freeFlowSeconds), isEstimate: false)
        }
    }

    @Test("a response's runs reach the preview whole, and a retime keeps them")
    func previewCarriesRuns() {
        let e = PlanResponseDecodeTests.expected
        for runs in [nil, [Self.run(0, 1, 61000), Self.run(1, 2, 59000)]] as [[CorridorTimeRun]?] {
            let preview = ClientPlanner.preview(of: Self.expected(runs), place: 42, budgetMinutes: 25)
            let whole = PlanPreview(route: e.route, etaSeconds: e.etaSeconds, fastestEtaSeconds: e.fastestEtaSeconds,
                                    etaIsEstimate: e.etaIsEstimate,
                                    hazards: [PlanHazardRun(kind: "surface", value: "dirt", fromIndex: 0, toIndex: 2)],
                                    waypoints: e.waypoints, lambda: e.lambda, continuation: nil, timeRuns: runs)
            #expect(preview == whole, "\(String(describing: runs))")
            let retimed = RetimedPreview.of(preview, timeRuns: runs ?? [], by: FreeFlow(), departsAt: Date(timeIntervalSince1970: 0))
            let free = runs.map { _ in 120.0 } ?? e.etaSeconds
            let again = PlanPreview(route: e.route, etaSeconds: free, fastestEtaSeconds: e.fastestEtaSeconds,
                                    etaIsEstimate: runs == nil ? e.etaIsEstimate : false, hazards: whole.hazards,
                                    waypoints: e.waypoints, lambda: e.lambda, continuation: nil, timeRuns: runs)
            #expect(retimed == again, "\(String(describing: runs))")
        }
    }
}
