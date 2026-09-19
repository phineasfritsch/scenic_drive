import Foundation

/// Why a plan is not a plan. Every case here is a refusal to print something that would be false.
public enum PlanFailure: Error, Equatable, Sendable {
    /// The router's body could not be read as a route.
    case malformedResponse(String)

    /// The router answered with an error message instead of a path.
    case routerRefused(String)

    /// The returned route takes longer than `fastest + budget`.
    ///
    /// CLAUDE.md: *"The extra-time budget is a **ceiling**: returned ETA <= fastest + budget. Always."*
    /// `LambdaSearch` already refuses to RETURN an infeasible lambda, so this fires when something between
    /// the search and the plan disagrees - a solver that reports one duration and a route that has another,
    /// a re-issued request that came back slower, a caller wiring in its own solver. The plan is thrown
    /// away rather than shown with the breach in small print.
    case budgetCeilingBreached(returned: TimeInterval, ceiling: TimeInterval)

    /// The route the search chose is the fastest route wearing a lambda.
    ///
    /// The product promise is "keep me off the freeway, make it pretty", so handing back the same edges the
    /// fastest route uses and calling it scenic is the failure that looks most like success. The measure is
    /// the Jaccard overlap of the two way-id sets and the requirement is `< maximumOverlap`; a solver that
    /// answers lambda 0 scores 1.0 and is refused here.
    case notActuallyDifferent(overlap: Double, maximum: Double)

    /// The recorded router has no response for this lambda, and inventing one would make the fixture a stub.
    case noRecordedResponse(lambda: Double)

    /// Lambda is outside the bisection's bracket. Never clamped - the same rule the Worker's
    /// `buildCustomModel` states: a clamp turns "the caller has a bug" into "the route is quietly not the
    /// one that was asked for".
    case lambdaOutOfRange(Double)
}

extension PlanFailure: CustomStringConvertible {
    public var description: String {
        switch self {
        case let .malformedResponse(what):
            return "the router's response could not be read: \(what)"
        case let .routerRefused(message):
            return "the router refused the request: \(message)"
        case let .budgetCeilingBreached(returned, ceiling):
            return "the returned route takes \(returned) s, over the \(ceiling) s ceiling"
        case let .notActuallyDifferent(overlap, maximum):
            return "the chosen route overlaps the fastest route by \(overlap) of its ways, "
                + "and a scenic route must overlap by less than \(maximum)"
        case let .noRecordedResponse(lambda):
            return "no recorded response at lambda \(lambda)"
        case let .lambdaOutOfRange(lambda):
            return "lambda \(lambda) is outside [0, \(LambdaSearch.maxLambda)]"
        }
    }
}
