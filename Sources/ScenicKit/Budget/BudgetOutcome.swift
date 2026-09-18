import Foundation

/// The result of a budget search: a scenic penalty and the duration that was **measured** at it.
///
/// `duration` is always a value the router actually returned for this exact `lambda`. It is never
/// interpolated, never the bisection midpoint's estimate, and never the ceiling itself. That is the whole
/// discipline of this type: the number shown to the user as "your drive takes 43 minutes" has to be a number
/// somebody computed for the route being shown, not a bound that route was assumed to satisfy.
public struct BudgetOutcome: Equatable, Sendable {
    /// The scenic penalty to re-issue the route request with. Always one of the values that was evaluated.
    public let lambda: Double

    /// The duration the router returned at `lambda`, in seconds. Guaranteed `<= ceiling`.
    public let duration: TimeInterval

    /// `fastest + budget`. The invariant, from CLAUDE.md: *the extra-time budget is a ceiling; returned ETA
    /// <= fastest + budget. Always.*
    public let ceiling: TimeInterval

    /// How many times the caller's `measure` closure ran. Each one is a request to our router, and the plan
    /// caps a plan at twelve, so this is a cost the caller has to be able to see.
    public let evaluations: Int

    /// Whether at least half the offered budget was actually spent.
    ///
    /// A user who asks for 25 extra minutes and is handed a route 90 seconds longer than the fastest one has
    /// been told "yes" and given "no". The plan makes this a visible product state - *"couldNotUseBudget"* -
    /// rather than something the ETA quietly conceals.
    public let usedBudget: Bool

    /// True when, **among the lambdas this search actually sampled**, a larger one measured a shorter
    /// duration than a smaller one.
    ///
    /// The plan states duration is monotone in lambda on a graph we own, and the search is a bisection,
    /// which is only correct if that holds. It is an assumption about a routing engine, not a theorem: ties,
    /// alternative-route selection and contraction-hierarchy shortcuts can all break it at the margins. So
    /// the search does not trust it - it detects a violation, records it here, and still returns a measured
    /// feasible answer.
    ///
    /// **`false` does not mean the router is monotone.** A bisection visits six points out of a continuum,
    /// and a curve can dip and recover entirely between two of them - that case exists in the test suite and
    /// is where this wording came from. `true` is evidence of a violation; `false` is only the absence of
    /// evidence, over six samples. Read it as "nothing contradicted the assumption here", never as a proof,
    /// and do not build a check on top of `false` that would be vacuous whenever the dip goes unsampled.
    ///
    /// The invariant does not depend on any of this: `duration <= ceiling` holds because it was measured,
    /// not because the curve was assumed to behave.
    public let monotonicityViolated: Bool

    public init(lambda: Double, duration: TimeInterval, ceiling: TimeInterval,
                evaluations: Int, usedBudget: Bool, monotonicityViolated: Bool) {
        self.lambda = lambda
        self.duration = duration
        self.ceiling = ceiling
        self.evaluations = evaluations
        self.usedBudget = usedBudget
        self.monotonicityViolated = monotonicityViolated
    }

    /// Seconds of extra travel bought over the fastest route.
    public func extraTime(overFastest fastest: TimeInterval) -> TimeInterval {
        duration - fastest
    }
}
