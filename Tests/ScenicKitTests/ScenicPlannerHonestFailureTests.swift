import Foundation
import Testing
@testable import ScenicKit

/// T-0230: the plan's honest failure (Problem A step 3) and couldNotUseBudget (plan:214), through
/// `ScenicPlanner.plan` - the symbol `PlanCommand.run`, and so `ops/plan`, calls. Every expected value is a
/// function of the row's own input, computed here against literals (0.45, 0.5, 40 minutes), never read back
/// from the constants under test.
@Suite("T-0230: ops/plan's honest failure and couldNotUseBudget through ScenicPlanner.plan")
struct ScenicPlannerHonestFailureTests {

    static let origin = Coordinate(latitude: 34.0392, longitude: -118.5836)
    static let destination = Coordinate(latitude: 34.0944, longitude: -118.6019)
    static let fastestSeconds: TimeInterval = 1800
    static let budget: TimeInterval = 1500
    /// The floor, typed here: a mutant of RouteScore.honestFailureThreshold must disagree with it.
    static let floor = 0.45
    static let unrecordedEight = PlanFailure.noRecordedResponse(lambda: 8).description

    /// A router answering typed paths, and remembering which lambdas it was asked for.
    final class Router: RouteSource {
        let fastestPath: RoutePath
        var scenicPaths: [String: RoutePath] = [:]
        var refusals: [String: PlanFailure] = [:]
        private(set) var requested: [Double] = []
        var describedSource: String { "stub" }

        init(chosen: RoutePath, at lambda: Double = 4) {
            fastestPath = ScenicPlannerHonestFailureTests.path(ms: 1_800_000, legs: [(nil, 0.01), (nil, 0.01)],
                                                               wayBase: 1)
            scenicPaths[LambdaCustomModel.multiplier(lambda)] = chosen
        }

        func fastest(from origin: Coordinate, to destination: Coordinate) throws -> RoutePath { fastestPath }

        func scenic(from origin: Coordinate, to destination: Coordinate, lambda: Double) throws -> RoutePath {
            requested.append(lambda)
            let key = LambdaCustomModel.multiplier(lambda)
            if let refusal = refusals[key] { throw refusal }
            guard let path = scenicPaths[key] else { throw PlanFailure.noRecordedResponse(lambda: lambda) }
            return path
        }
    }

    /// A route north along one meridian: one way per leg, `degrees` of latitude each, scored when `score` is set.
    static func path(ms: Int, legs: [(score: Int?, degrees: Double)], wayBase: Int = 100) -> RoutePath {
        var coordinates = [Coordinate(latitude: 34.0, longitude: -118.5)]
        var ways: [RoutePath.DetailRun] = []
        var scores: [RoutePath.DetailRun] = []
        for (index, leg) in legs.enumerated() {
            coordinates.append(Coordinate(latitude: coordinates[index].latitude + leg.degrees, longitude: -118.5))
            ways.append(RoutePath.DetailRun(from: index, to: index + 1, value: .number(Double(wayBase + index))))
            if let score = leg.score {
                scores.append(RoutePath.DetailRun(from: index, to: index + 1, value: .number(Double(score))))
            }
        }
        var details = ["osm_way_id": ways]
        if !scores.isEmpty { details["scenic_score"] = scores }
        return RoutePath(durationMilliseconds: ms, distanceMeters: 1000, coordinates: coordinates, details: details)
    }

    static func score(_ path: RoutePath) -> Double? {
        RouteScore(edges: PlanTable(path: path).scoredEdges)?.value
    }

    /// A solver that measures `lambdas` in order and answers the last, claiming the budget was used.
    static func solver(measuring lambdas: [Double]) -> ScenicPlanner.BudgetSolving {
        { fastest, budget, _, measure in
            var duration = 0.0
            for lambda in lambdas { duration = try measure(lambda) }
            return BudgetOutcome(lambda: lambdas.last ?? 0, duration: duration, ceiling: fastest + budget,
                                 evaluations: lambdas.count, usedBudget: true, monotonicityViolated: false)
        }
    }

    static func plan(_ router: Router, measuring lambdas: [Double] = [4],
                     budget: TimeInterval = ScenicPlannerHonestFailureTests.budget) throws -> ScenicPlan {
        try ScenicPlanner(source: router, solve: solver(measuring: lambdas))
            .plan(from: origin, to: destination, budget: budget)
    }

    static func refusal(_ router: Router, measuring lambdas: [Double] = [4]) throws -> PlanNothingPretty? {
        do {
            _ = try plan(router, measuring: lambdas)
            return nil
        } catch PlanFailure.nothingPretty(let state) {
            return state
        }
    }

    /// A pretty route: two score-8 legs, one 2.2 km episode.
    static func pretty(ms: Int) -> RoutePath { path(ms: ms, legs: [(8, 0.01), (8, 0.01)]) }

    // MARK: - the floor, every bound

    /// Geometries landing on nextDown(0.45), 0.45 and nextUp(0.45) exactly, searched at run time because the
    /// last bits of a haversine are the platform libm's. [2, 8, 5] legs under 800 m (dud 1/3, no episode) and
    /// [4, 6] are 0.45 in exact arithmetic; their rounding scatters over the three neighbours (T-0230 M5).
    static func floorRows() -> [Double: RoutePath] {
        let targets = [floor.nextDown, floor, floor.nextUp]
        var found: [Double: RoutePath] = [:]
        for pattern in [[2, 8, 5], [4, 6]] {
            for step in 0..<20_000 where found.count < targets.count {
                let degrees = 0.004 + Double(step) * 1e-7
                let candidate = path(ms: 2_700_000, legs: pattern.map { ($0, degrees) })
                if let value = score(candidate), targets.contains(value), found[value] == nil {
                    found[value] = candidate
                }
            }
        }
        return found
    }

    @Test("the floor through ScenicPlanner.plan: nextDown(0.45) refused, exactly 0.45 and nextUp(0.45) planned")
    func theFloorIsStrictAtEveryBound() throws {
        let rows = Self.floorRows()
        for target in [Self.floor.nextDown, Self.floor, Self.floor.nextUp] {
            let chosen = try #require(rows[target], "no geometry lands on \(target)")
            let router = Router(chosen: chosen)
            if target < Self.floor {
                #expect(try Self.refusal(router) == PlanNothingPretty(
                    budget: 1500, fastestDuration: 1800, routeScore: target,
                    backRoads: .unmeasured(Self.unrecordedEight)), "at \(target)")
            } else {
                let plan = try Self.plan(router)
                #expect(plan.outcome.lambda == 4 && plan.table == PlanTable(path: chosen), "at \(target)")
            }
        }
    }

    @Test("a chosen route with no scored road is refused as nothingPretty, fail closed (the NaN/invalid row)")
    func anUnscoredRouteIsNothingPretty() throws {
        let chosen = Self.path(ms: 2_700_000, legs: [(nil, 0.01), (nil, 0.01)])
        #expect(Self.score(chosen) == nil)
        #expect(try Self.refusal(Router(chosen: chosen)) == PlanNothingPretty(
            budget: 1500, fastestDuration: 1800, routeScore: nil, backRoads: .unmeasured(Self.unrecordedEight)))
    }

    @Test("the motorway-shoulder route (RouteScore.swift's realistic fixture, integer image) is not much pretty")
    func motorwayShoulderRouteIsNothingPretty() throws {
        let metres = 1 / 111_195.0
        let chosen = Self.path(ms: 2_700_000, legs: [(0, 8000 * metres), (2, 1200 * metres), (8, 2400 * metres),
                                                     (8, 1800 * metres), (2, 900 * metres), (2, 1500 * metres)])
        let value = try #require(Self.score(chosen))
        try #require(value < Self.floor, "the fixture itself moved: \(value)")
        #expect(try Self.refusal(Router(chosen: chosen)) == PlanNothingPretty(
            budget: 1500, fastestDuration: 1800, routeScore: value, backRoads: .unmeasured(Self.unrecordedEight)))
    }

    // MARK: - the two offers

    static let dull = path(ms: 2_700_000, legs: [(2, 0.01), (2, 0.01)])

    @Test("all back roads reuses a lambda 8 the search measured: no extra request, its measured ETA, +40 printed")
    func backRoadsReusesTheMeasuredLambdaEight() throws {
        let router = Router(chosen: Self.dull)
        let eight = Self.pretty(ms: 3_600_000)
        router.scenicPaths[LambdaCustomModel.multiplier(8)] = eight
        let state = try #require(try Self.refusal(router, measuring: [8, 4]))
        #expect(router.requested == [8, 4])
        #expect(state == PlanNothingPretty(budget: 1500, fastestDuration: 1800, routeScore: Self.score(Self.dull),
                                           backRoads: .offered(duration: 3600, routeScore: try #require(Self.score(eight)))))
        #expect(state.moreTimeBudget == 3900)
        let lines = state.lines()
        #expect(lines.count == 3)
        #expect(lines.first?.hasPrefix("not much pretty within 25 minutes of this drive: RouteScore ") == true)
        #expect(lines.dropFirst().first == "OFFER more-time: plan again with 65 minutes of extra time (+40 minutes)")
        #expect(lines.last?.hasPrefix("OFFER all-back-roads: lambda 8, measured ETA 1h00m00s, RouteScore ") == true)
    }

    @Test("all back roads not measured by the search is requested exactly once, after the search")
    func backRoadsIsRequestedOnceWhenUnmeasured() throws {
        let router = Router(chosen: Self.dull)
        let eight = Self.pretty(ms: 3_600_000)
        router.scenicPaths[LambdaCustomModel.multiplier(8)] = eight
        let state = try #require(try Self.refusal(router))
        #expect(router.requested == [4, 8])
        #expect(state.backRoads == .offered(duration: 3600, routeScore: try #require(Self.score(eight))))
    }

    @Test("a dull or unscored back-roads route is not offered; a refused one is unmeasured; malformed propagates")
    func backRoadsIsOfferedOnlyWhenPretty() throws {
        let dullEight = Router(chosen: Self.dull)
        dullEight.scenicPaths[LambdaCustomModel.multiplier(8)] = Self.path(ms: 3_000_000, legs: [(3, 0.01)])
        let dullScore = try #require(Self.score(Self.path(ms: 3_000_000, legs: [(3, 0.01)])))
        try #require(dullScore < Self.floor)
        #expect(try Self.refusal(dullEight)?.backRoads == .dull(duration: 3000, routeScore: dullScore))

        let unscoredEight = Router(chosen: Self.dull)
        unscoredEight.scenicPaths[LambdaCustomModel.multiplier(8)] = Self.path(ms: 3_000_000, legs: [(nil, 0.01)])
        #expect(try Self.refusal(unscoredEight)?.backRoads == .dull(duration: 3000, routeScore: nil))

        let refused = Router(chosen: Self.dull)
        refused.refusals[LambdaCustomModel.multiplier(8)] = .routerRefused("no path")
        #expect(try Self.refusal(refused)?.backRoads == .unmeasured("the router refused the request: no path"))

        let malformed = Router(chosen: Self.dull)
        malformed.refusals[LambdaCustomModel.multiplier(8)] = .malformedResponse("x")
        #expect(throws: PlanFailure.malformedResponse("x")) { try Self.plan(malformed) }
    }

    @Test("notActuallyDifferent is not nothingPretty: a dull route equal to the fastest is refused as the former")
    func theTwoRefusalsStayApart() throws {
        let router = Router(chosen: Self.path(ms: 1_800_000, legs: [(1, 0.01), (1, 0.01)], wayBase: 1))
        #expect(throws: PlanFailure.notActuallyDifferent(overlap: 1, maximum: RouteDifference.maximumOverlap)) {
            try Self.plan(router)
        }
    }

    // MARK: - couldNotUseBudget

    @Test("couldNotUseBudget: fastest + 0.5B - 1 ms true, exact and + 1 ms false, budget 0 false, NaN refused")
    func couldNotUseBudgetAtEveryBound() throws {
        let rows: [(ms: Int, budget: TimeInterval)] = [(2_549_999, 1500), (2_550_000, 1500), (2_550_001, 1500),
                                                      (1_799_000, 0), (1_800_000, 0)]
        for row in rows {
            let plan = try Self.plan(Router(chosen: Self.pretty(ms: row.ms)), budget: row.budget)
            let expected = row.budget > 0 && Double(row.ms) / 1000 < 1800 + 0.5 * row.budget
            #expect(plan.outcome.usedBudget, "the stub solver claims the budget was used, always")
            #expect(plan.couldNotUseBudget == expected, "\(row)")
            let state = plan.report().filter { $0.hasPrefix("STATE couldNotUseBudget") }
            #expect(state == (expected ? ["STATE couldNotUseBudget returned=42m30s under fastest+half-the-budget=42m30s"]
                                       : []), "\(row)")
        }
        do {
            _ = try Self.plan(Router(chosen: Self.pretty(ms: 2_000_000)), budget: .nan)
            Issue.record("a NaN budget planned")
        } catch PlanFailure.budgetCeilingBreached {
        }
    }
}
