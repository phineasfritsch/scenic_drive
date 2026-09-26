import Foundation
import Testing
import Handoff
import ScenicKit
@testable import ScenicPlanCLI

/// T-0221: `ops/plan` over the whole-LA graph - the three drives handed to the owner.
///
/// Each fixture under Tests/Fixtures/t0221/<pair> was recorded in-process by the committed recorder against
/// T-0209's whole-LA graph (GRAPH_DIGEST eb43090a...18eb) with the models `ops/plan --emit-model` prints, and
/// keeps fastest.json plus exactly the lambdas the bisection visits (a missing one refuses by name).
///
/// Every test drives `PlanCommand.run(PlanArguments.parse(...))` - the call main.swift makes for `ops/plan` -
/// with the arguments the Log's runs were given, and checks what it printed against numbers it did NOT make:
/// the raw `paths[0].time` of the recorded files read through JSONSerialization (not RoutePath's decoder),
/// the budget as the literal 25 minutes the owner typed, and the URL, LAMBDA and ETA lines as the literals the
/// T-0221 Log quotes and hands to the owner.
@Suite("ops/plan over the whole-LA graph (T-0221)")
struct PlanCLILARecordingTests {

    /// One recorded pair and what the Log quotes for it.
    struct Pair: Sendable, CustomTestStringConvertible {
        let name: String
        let origin: Coordinate
        let destination: Coordinate
        let typedOrigin: String
        let typedDestination: String
        let chosenFile: String
        let lambdaLine: String
        let etaLine: String
        let url: String
        var testDescription: String { name }
    }

    /// The fixture recorded for a pair's chosen route or the fastest route could not be read as GraphHopper's
    /// envelope - a fixture problem, never a pass.
    struct UnreadableRecording: Error {
        let file: String
    }

    /// 25 minutes, as typed on the command line, in seconds - written here, not read from PlanArguments.
    static let budgetSeconds: TimeInterval = 25 * 60

    static let root = URL(fileURLWithPath: #filePath)   // Tests/ScenicPlanCLITests/<this file>
        .deletingLastPathComponent()                    // Tests/ScenicPlanCLITests
        .deletingLastPathComponent()                    // Tests
        .appendingPathComponent("Fixtures/t0221")

    static let pairs: [Pair] = [
        Pair(name: "westwood-malibu",
             origin: Coordinate(latitude: 34.0669, longitude: -118.4399),
             destination: Coordinate(latitude: 34.0356, longitude: -118.6894),
             typedOrigin: "34.0669,-118.4399", typedDestination: "34.0356,-118.6894",
             chosenFile: "lambda-3.25.json",
             lambdaLine: "LAMBDA 3.25 evaluations=6 used-budget=false monotonicity-violated=false",
             etaLine: "ETA fastest=27m47s returned=31m44s ceiling=52m47s distance=29214.7m",
             url: "https://maps.apple.com/directions?source=34.06690,-118.43990&destination=34.03560,-118.68940"
                + "&waypoint=34.05041,-118.48215&waypoint=34.05287,-118.50255&waypoint=34.04804,-118.54339"
                + "&waypoint=34.04207,-118.56917&waypoint=34.03946,-118.58947&waypoint=34.03721,-118.60854"
                + "&waypoint=34.03719,-118.63819&waypoint=34.03818,-118.65069&waypoint=34.03942,-118.66089"
                + "&mode=driving"),
        Pair(name: "westwood-woodland-hills",
             origin: Coordinate(latitude: 34.0669, longitude: -118.4399),
             destination: Coordinate(latitude: 34.1684, longitude: -118.6058),
             typedOrigin: "34.0669,-118.4399", typedDestination: "34.1684,-118.6058",
             chosenFile: "lambda-7.75.json",
             lambdaLine: "LAMBDA 7.75 evaluations=6 used-budget=true monotonicity-violated=false",
             etaLine: "ETA fastest=20m09s returned=38m26s ceiling=45m09s distance=30333.0m",
             url: "https://maps.apple.com/directions?source=34.06690,-118.43990&destination=34.16840,-118.60580"
                + "&waypoint=34.08536,-118.43525&waypoint=34.09972,-118.44349&waypoint=34.10963,-118.44655"
                + "&waypoint=34.13142,-118.44889&waypoint=34.13770,-118.49706&waypoint=34.16322,-118.53754"
                + "&waypoint=34.16262,-118.57024&waypoint=34.15881,-118.58836&waypoint=34.15692,-118.60583"
                + "&mode=driving"),
        Pair(name: "santa-monica-topanga",
             origin: Coordinate(latitude: 34.0195, longitude: -118.4912),
             destination: Coordinate(latitude: 34.0676, longitude: -118.5957),
             typedOrigin: "34.0195,-118.4912", typedDestination: "34.0676,-118.5957",
             chosenFile: "lambda-7.75.json",
             lambdaLine: "LAMBDA 7.75 evaluations=6 used-budget=false monotonicity-violated=false",
             etaLine: "ETA fastest=20m14s returned=22m26s ceiling=45m14s distance=20358.6m",
             url: "https://maps.apple.com/directions?source=34.01950,-118.49120&destination=34.06760,-118.59570"
                + "&waypoint=34.02238,-118.49476&waypoint=34.02453,-118.50465&waypoint=34.03142,-118.52540"
                + "&waypoint=34.04207,-118.56917&waypoint=34.04067,-118.57915&waypoint=34.04700,-118.57722"
                + "&waypoint=34.06436,-118.58704&waypoint=34.08350,-118.60162&waypoint=34.07941,-118.60288"
                + "&mode=driving"),
    ]

    static func directory(_ pair: Pair) -> URL {
        root.appendingPathComponent(pair.name)
    }

    /// Exactly what `ops/plan <O> <D> 25 --recorded Tests/Fixtures/t0221/<pair>` hands the CLI.
    static func printed(_ pair: Pair) throws -> [String] {
        try PlanCommand.run(PlanArguments.parse([pair.typedOrigin, pair.typedDestination, "25",
                                                 "--recorded", directory(pair).path]))
    }

    /// The plan recomputed here from the pieces, with the budget as the literal above.
    static func plan(_ pair: Pair) throws -> ScenicPlan {
        try ScenicPlanner(source: RecordedRouteSource(directory: directory(pair)))
            .plan(from: pair.origin, to: pair.destination, budget: budgetSeconds)
    }

    /// `paths[0].time` of a recorded file, in seconds, read by JSONSerialization - independent of RoutePath.
    static func recordedSeconds(_ pair: Pair, _ file: String) throws -> TimeInterval {
        let data = try Data(contentsOf: directory(pair).appendingPathComponent(file))
        guard let object = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let paths = object["paths"] as? [[String: Any]],
              let time = paths.first?["time"] else {
            throw UnreadableRecording(file: file)
        }
        if let milliseconds = time as? Int { return Double(milliseconds) / 1000 }
        if let milliseconds = time as? NSNumber { return milliseconds.doubleValue / 1000 }
        throw UnreadableRecording(file: file)
    }

    @Test("the route ops/plan returns is inside fastest + 25 min on the recorded graph (P-SAFE-04)",
          arguments: pairs)
    func theReturnedRouteIsInsideTheCeiling(pair: Pair) throws {
        let lines = try Self.printed(pair)
        let plan = try Self.plan(pair)
        let fastest = try Self.recordedSeconds(pair, "fastest.json")
        let returned = try Self.recordedSeconds(pair, pair.chosenFile)

        // What the terminal showed is this plan, line for line, between the ROUTER and URL lines.
        #expect(lines.first == "ROUTER recorded \(pair.name)")
        #expect(Array(lines.dropFirst().dropLast()) == plan.report())
        #expect(lines.contains(pair.lambdaLine))
        #expect(lines.contains(pair.etaLine))

        // Its durations are the recorded GraphHopper numbers, exactly, and the ceiling holds over them.
        #expect(plan.fastestDuration == fastest)
        #expect(plan.outcome.duration == returned)
        #expect(plan.outcome.duration <= fastest + Self.budgetSeconds)
        #expect(returned <= fastest + Self.budgetSeconds)
    }

    @Test("the URL ops/plan prints IS the Apple Maps handoff of the plan's decision points", arguments: pairs)
    func thePrintedURLIsTheHandoffOfThePlan(pair: Pair) throws {
        let lines = try Self.printed(pair)
        let plan = try Self.plan(pair)
        let url = try AppleMapsDirections(source: pair.origin, destination: pair.destination,
                                          waypoints: plan.waypoints).url()

        #expect(lines.last == "URL \(url.absoluteString)")
        #expect(lines.last == "URL \(pair.url)")
        #expect(plan.waypoints.count <= 9)
        #expect(pair.url.components(separatedBy: "&waypoint=").count - 1 == plan.waypoints.count)
    }
}
