import Foundation

/// The shipping entry point of the scenic plan: the symbol `ops/plan` runs, and the one the meta-tests
/// bind to.
///
/// It owns exactly two assertions, and they are the two the plan calls meta-tests, because they are the
/// two failures a green routing stack produces while looking correct:
///
///   1. **The ceiling.** CLAUDE.md: *the extra-time budget is a ceiling; returned ETA <= fastest + budget.
///      Always.* A solver that answers lambda 8 without measuring it breaks this and nothing downstream
///      would notice - the route exists, the ETA is a real number, and it is 20 minutes over what the user
///      agreed to.
///   2. **Actually different.** A solver that answers lambda 0 hands back the fastest route and calls it
///      scenic. Every number on the screen is true and the product did not happen.
///
/// Both are checked against values this type computes from what it measured, never against values the
/// solver reported: `ceiling` is `fastest.duration + budget` recomputed here, and the duration checked is
/// the CHOSEN PATH's, re-read from the route itself. A solver that reports one duration and returns a
/// route with another is exactly the case these guards are for.
public struct ScenicPlanner {

    /// The budget solver, injected so the meta-tests can hand in a stub that answers a fixed lambda.
    /// The production value is `LambdaSearch`, and there is only ever one bisection in this repository.
    public typealias BudgetSolving = (
        _ fastest: TimeInterval,
        _ budget: TimeInterval,
        _ maxEvaluations: Int,
        _ measure: (Double) throws -> TimeInterval
    ) throws -> BudgetOutcome

    /// A function rather than a stored closure: a `static let` of function type is global mutable state
    /// under Swift 6 and would have to be `@Sendable`, which would then demand a `@Sendable` `measure` -
    /// and `measure` deliberately captures the routes it measured.
    public static func lambdaSearch(fastest: TimeInterval, budget: TimeInterval, maxEvaluations: Int,
                                    measure: (Double) throws -> TimeInterval) throws -> BudgetOutcome {
        try LambdaSearch(fastest: fastest, budget: budget, maxEvaluations: maxEvaluations).search(measure)
    }

    public let source: RouteSource
    public let solve: BudgetSolving
    public let maxEvaluations: Int

    public init(source: RouteSource, maxEvaluations: Int = 6,
                solve: @escaping BudgetSolving = ScenicPlanner.lambdaSearch) {
        self.source = source
        self.maxEvaluations = maxEvaluations
        self.solve = solve
    }

    /// Plan, or refuse. `budget` is seconds of EXTRA time over the fastest route.
    public func plan(from origin: Coordinate, to destination: Coordinate,
                     budget: TimeInterval) throws -> ScenicPlan {
        let fastest = try source.fastest(from: origin, to: destination)
        let ceiling = fastest.duration + budget

        // Every scenic route the search measures is kept, because the plan is built from the ROUTE at the
        // winning lambda and not from the duration the search remembered for it.
        var measured: [String: RoutePath] = [:]
        let outcome = try solve(fastest.duration, budget, maxEvaluations) { lambda in
            let path = try source.scenic(from: origin, to: destination, lambda: lambda)
            measured[Self.key(lambda)] = path
            return path.duration
        }

        guard let chosen = measured[Self.key(outcome.lambda)] else {
            throw PlanFailure.noRecordedResponse(lambda: outcome.lambda)
        }

        // 1. The ceiling, over the chosen route's own duration.
        guard chosen.duration <= ceiling else {
            throw PlanFailure.budgetCeilingBreached(returned: chosen.duration, ceiling: ceiling)
        }

        // 2. Actually different, over the two way-id sets.
        let overlap = RouteDifference.overlap(RouteDifference.wayIds(of: chosen),
                                              RouteDifference.wayIds(of: fastest))
        guard overlap < RouteDifference.maximumOverlap else {
            throw PlanFailure.notActuallyDifferent(overlap: overlap,
                                                   maximum: RouteDifference.maximumOverlap)
        }

        let table = PlanTable(path: chosen)
        return ScenicPlan(
            origin: origin,
            destination: destination,
            budget: budget,
            fastestDuration: fastest.duration,
            outcome: outcome,
            distanceMeters: chosen.distanceMeters,
            table: table,
            waypoints: PlanWaypoints.decisionPoints(table: table, path: chosen),
            overlapWithFastest: overlap
        )
    }

    /// A lambda's key in the measured map. `Double` is a poor dictionary key when the value is produced by
    /// arithmetic in one place and read back in another; the six-decimal spelling the rest of the tool
    /// uses for a lambda is stable and is the one the recording's file name uses too.
    static func key(_ lambda: Double) -> String {
        LambdaCustomModel.multiplier(lambda)
    }
}
