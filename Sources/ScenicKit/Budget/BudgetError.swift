import Foundation

/// Why a budget search could not run, or could not produce an honest answer.
public enum BudgetError: Error, Equatable, Sendable {
    /// `fastest` is not a positive, finite number of seconds.
    case notADuration(TimeInterval)

    /// The extra-time budget is negative or not finite. Zero is legal and means "the fastest route".
    case notABudget(TimeInterval)

    /// The router returned a duration that is NaN, infinite, or negative for some lambda.
    case routerReturnedNonsense(lambda: Double, duration: TimeInterval)

    /// Not one evaluation came back at or under the ceiling - **including lambda = 0**.
    ///
    /// This should be impossible: at lambda = 0 the scenic penalty is switched off entirely, so the router
    /// is solving the same problem `car_fast` already solved, and its answer cannot exceed
    /// `fastest + budget` for any budget >= 0. If it does, the two requests disagree about the same route,
    /// and the honest response is to refuse rather than to hand back the least-bad breach.
    ///
    /// Returning a route over the ceiling would violate the product invariant that this whole type exists to
    /// hold. Refusing surfaces as `PlanError.noRoute` and the user sees "couldn't reach that address" -
    /// which is a worse answer, and a true one.
    case noFeasibleLambda(ceiling: TimeInterval, best: TimeInterval, evaluations: Int)
}

extension BudgetError: CustomStringConvertible {
    public var description: String {
        switch self {
        case let .notADuration(t):
            return "fastest duration is not a positive finite number of seconds: \(t)"
        case let .notABudget(b):
            return "budget is not a non-negative finite number of seconds: \(b)"
        case let .routerReturnedNonsense(lambda, duration):
            return "router returned \(duration) s at lambda \(lambda)"
        case let .noFeasibleLambda(ceiling, best, evaluations):
            return "no lambda produced a route within the \(ceiling) s ceiling in \(evaluations) "
                + "evaluations; the shortest seen was \(best) s"
        }
    }
}
