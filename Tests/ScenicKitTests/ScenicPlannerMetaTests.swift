import Foundation
import Testing
@testable import ScenicKit

/// The plan's META-TESTS: tests about whether the engine would notice that it had stopped working.
///
/// Both bind to `ScenicPlanner.plan`, the symbol `ops/plan` runs - not to `RouteDifference`, not to
/// `LambdaSearch`, not to a helper. A guard that is only exercised through the function that defines it is
/// a guard nothing in production has to call (CLAUDE.md: *a test named for a defect binds to the shipping
/// symbol - the entry point production runs*).
///
/// The stub in each is a SOLVER, not a router: the routes are real-shaped values and the thing that
/// misbehaves is the search, which is how both failures arrive in the field. A solver that answers
/// lambda 0 hands back the fastest route; a solver that answers lambda 8 without measuring it hands back a
/// route over the ceiling. Every number in both plans is true and the product did not happen.
@Suite("Scenic planner meta-tests")
struct ScenicPlannerMetaTests {

    static let origin = Coordinate(latitude: 34.0392, longitude: -118.5836)
    static let destination = Coordinate(latitude: 34.0944, longitude: -118.6019)

    /// 30 minutes fastest, 25 minutes of budget - the plan's own example.
    static let fastestSeconds: TimeInterval = 1800
    static let budget: TimeInterval = 1500

    /// A router that answers with routes typed here: the fastest route over ways 1-4, and a scenic route
    /// per lambda built by `scenic`. Nothing about it is clever; the misbehaviour under test is the
    /// solver's.
    struct StubRouter: RouteSource {
        var fastestPath: RoutePath
        var scenicPaths: [String: RoutePath]

        var describedSource: String { "stub" }

        func fastest(from origin: Coordinate, to destination: Coordinate) throws -> RoutePath {
            fastestPath
        }

        func scenic(from origin: Coordinate, to destination: Coordinate,
                    lambda: Double) throws -> RoutePath {
            guard let path = scenicPaths[LambdaCustomModel.multiplier(lambda)] else {
                throw PlanFailure.noRecordedResponse(lambda: lambda)
            }
            return path
        }
    }

    /// A route over `ways`, `seconds` long, with enough geometry for a table and pins.
    static func path(seconds: TimeInterval, ways: [Int]) -> RoutePath {
        var coordinates: [Coordinate] = []
        var runs: [RoutePath.DetailRun] = []
        var classes: [RoutePath.DetailRun] = []
        for (index, way) in ways.enumerated() {
            coordinates.append(Coordinate(latitude: 34.0 + Double(index) / 100,
                                          longitude: -118.6 + Double(index) / 100))
            runs.append(RoutePath.DetailRun(from: index, to: index + 1, value: .number(Double(way))))
            classes.append(RoutePath.DetailRun(from: index, to: index + 1, value: .text("secondary")))
        }
        coordinates.append(Coordinate(latitude: 34.0 + Double(ways.count) / 100,
                                      longitude: -118.6 + Double(ways.count) / 100))
        return RoutePath(durationMilliseconds: Int(seconds * 1000), distanceMeters: 8121.6,
                         coordinates: coordinates,
                         details: ["osm_way_id": runs, "road_class": classes])
    }

    /// A solver that always answers `lambda`, reporting whatever the router measured there.
    static func stubSolver(answering lambda: Double) -> ScenicPlanner.BudgetSolving {
        { fastest, budget, _, measure in
            let duration = try measure(lambda)
            return BudgetOutcome(lambda: lambda, duration: duration, ceiling: fastest + budget,
                                 evaluations: 1, usedBudget: true, monotonicityViolated: false)
        }
    }

    static func router(scenicAt lambda: Double, seconds: TimeInterval, ways: [Int]) -> StubRouter {
        StubRouter(
            fastestPath: path(seconds: fastestSeconds, ways: [1, 2, 3, 4]),
            scenicPaths: [LambdaCustomModel.multiplier(lambda): path(seconds: seconds, ways: ways)]
        )
    }

    // MARK: - the two meta-tests

    @Test("a solver that answers lambda 0 fails actually different")
    func lambdaZeroIsRefusedAsNotActuallyDifferent() throws {
        // lambda 0 IS the fastest route, so the route comes back over the fastest route's own ways.
        let planner = ScenicPlanner(
            source: Self.router(scenicAt: 0, seconds: Self.fastestSeconds, ways: [1, 2, 3, 4]),
            solve: Self.stubSolver(answering: 0)
        )
        #expect(throws: PlanFailure.notActuallyDifferent(overlap: 1.0,
                                                        maximum: RouteDifference.maximumOverlap)) {
            try planner.plan(from: Self.origin, to: Self.destination, budget: Self.budget)
        }
    }

    @Test("a solver that answers lambda 8 fails the budget ceiling")
    func lambdaEightOverTheCeilingIsRefused() throws {
        // 60 s past `fastest + budget`, on a genuinely different set of ways, so the ONLY thing wrong with
        // this plan is the ceiling - the other guard cannot be what refuses it.
        let over = Self.fastestSeconds + Self.budget + 60
        let planner = ScenicPlanner(
            source: Self.router(scenicAt: 8, seconds: over, ways: [7, 8, 9, 10]),
            solve: Self.stubSolver(answering: 8)
        )
        #expect(throws: PlanFailure.budgetCeilingBreached(returned: over,
                                                          ceiling: Self.fastestSeconds + Self.budget)) {
            try planner.plan(from: Self.origin, to: Self.destination, budget: Self.budget)
        }
    }

    @Test("a route with no way ids is refused, not waved through as different")
    func aRouteWithoutWayIdsIsRefused() throws {
        // A graph built without `osm_way_id` in graph.encoded_values answers with no such detail, and the
        // difference measure then has nothing to compare. Two empty sets score 1.0 - "the same ways" - so
        // the plan is refused. Scoring an unmeasurable pair 0.0 would make every route on such a graph
        // pass the actually-different guard, which is the vacuous green this suite exists to prevent.
        let bare = RoutePath(durationMilliseconds: 1_800_000, distanceMeters: 8000,
                             coordinates: [Coordinate(latitude: 34, longitude: -118),
                                           Coordinate(latitude: 34.1, longitude: -118.1)],
                             details: [:])
        let planner = ScenicPlanner(
            source: StubRouter(fastestPath: bare,
                               scenicPaths: [LambdaCustomModel.multiplier(0): bare]),
            solve: Self.stubSolver(answering: 0)
        )
        #expect(throws: PlanFailure.notActuallyDifferent(overlap: 1.0,
                                                        maximum: RouteDifference.maximumOverlap)) {
            try planner.plan(from: Self.origin, to: Self.destination, budget: Self.budget)
        }
    }

    // MARK: - the control, without which both tests above pass on a planner that refuses everything

    @Test("a different route inside the ceiling is planned, through the real bisection")
    func aFeasibleDifferentRouteIsPlanned() throws {
        var paths: [String: RoutePath] = [:]
        // A router whose scenic route is different and 10 minutes slower at every lambda the real
        // bisection visits, which is inside a 25-minute budget.
        for lambda in [0.0, 4, 6, 7, 7.5, 7.75] {
            paths[LambdaCustomModel.multiplier(lambda)] = Self.path(
                seconds: lambda == 0 ? Self.fastestSeconds : Self.fastestSeconds + 600,
                ways: lambda == 0 ? [1, 2, 3, 4] : [5, 6, 7, 8]
            )
        }
        let planner = ScenicPlanner(
            source: StubRouter(fastestPath: Self.path(seconds: Self.fastestSeconds, ways: [1, 2, 3, 4]),
                               scenicPaths: paths)
        )
        let plan = try planner.plan(from: Self.origin, to: Self.destination, budget: Self.budget)
        #expect(plan.outcome.duration <= Self.fastestSeconds + Self.budget)
        #expect(plan.overlapWithFastest == 0)
        #expect(plan.table.rows.count == 4)
        #expect(plan.waypoints.count == 3)
    }
}
