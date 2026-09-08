import Foundation

/// Finds the scenic penalty that spends the user's extra minutes without ever exceeding them.
///
/// The product's whole promise is one sentence: *"I have 25 extra minutes, keep me off the freeway, make it
/// pretty."* `lambda` is the single knob that trades time for scenery in the router's cost function - at 0
/// the scenic score is ignored and the answer is the fastest route; as it rises, dull edges are penalised
/// harder and the route wanders toward pretty ones and takes longer.
///
/// So the search is: find the largest lambda whose route still fits inside `fastest + budget`.
///
/// ## The invariant, and why it is enforced rather than derived
///
/// CLAUDE.md: *"The extra-time budget is a **ceiling**: returned ETA <= fastest + budget. Always."* The
/// plan's method is a bisection, which is correct only if duration is monotone in lambda. That monotonicity
/// is an assumption about a routing engine - reasonable on a graph we own, and not a theorem. Ties,
/// alternative-route selection and contraction-hierarchy shortcuts can each break it near the margins.
///
/// A bisection that trusts monotonicity concludes "everything below the bracket is feasible" and can return
/// a lambda it never measured. That is the failure this type refuses: **only measured, verified-feasible
/// candidates are eligible to be returned**, so a non-monotone router costs accuracy and never costs the
/// invariant. Violations are detected and reported in `BudgetOutcome.monotonicityViolated` instead of being
/// silently relied upon.
///
/// ## Cost
///
/// Every evaluation is a request to our router. The plan caps a plan at twelve requests total, of which this
/// search is only one part, so `maxEvaluations` defaults to 6 and the count is reported back.
public struct LambdaSearch: Sendable {
    /// The top of the search range. Beyond this the penalty is so heavy the route stops resembling a drive.
    public static let maxLambda = 8.0

    /// Below this, two lambdas produce the same route and another request buys nothing.
    public static let lambdaTolerance = 0.05

    /// The share of the budget that must be spent before the result counts as having used it.
    public static let minBudgetUse = 0.5

    public let fastest: TimeInterval
    public let budget: TimeInterval
    public let maxEvaluations: Int

    public init(fastest: TimeInterval, budget: TimeInterval, maxEvaluations: Int = 6) throws {
        guard fastest.isFinite, fastest > 0 else { throw BudgetError.notADuration(fastest) }
        guard budget.isFinite, budget >= 0 else { throw BudgetError.notABudget(budget) }
        self.fastest = fastest
        self.budget = budget
        self.maxEvaluations = max(1, maxEvaluations)
    }

    public var ceiling: TimeInterval { fastest + budget }

    /// Search, calling `measure` to get the route duration at a lambda.
    ///
    /// `measure` is the router. It is injected so this can be tested against exact, adversarial duration
    /// curves - including non-monotone ones - without a network, a graph, or a container.
    public func search(_ measure: (Double) throws -> TimeInterval) throws -> BudgetOutcome {
        var evaluations = 0
        var best: (lambda: Double, duration: TimeInterval)?
        var seen: [(lambda: Double, duration: TimeInterval)] = []

        func evaluate(_ lambda: Double) throws -> TimeInterval {
            let d = try measure(lambda)
            evaluations += 1
            guard d.isFinite, d >= 0 else {
                throw BudgetError.routerReturnedNonsense(lambda: lambda, duration: d)
            }
            seen.append((lambda, d))
            // Feasible AND better than what we have. "Better" is longer, not shorter: the point is to SPEND
            // the budget, so among routes that fit, the slowest one is the most scenic one we can afford.
            //
            // The tie is not arbitrary and used to be. Lambda is a penalty on dull edges, so two lambdas
            // producing the SAME duration means the larger one avoided more dull road at no cost in time -
            // strictly the better route, for free. The first version kept whichever was found first, which
            // on a flat curve is lambda 0: the least scenic of a set of equally fast options. A mutation
            // that flipped the comparison went uncaught, which is what prompted looking at it properly.
            if d <= ceiling, best == nil || d > best!.duration
                || (d == best!.duration && lambda > best!.lambda) {
                best = (lambda, d)
            }
            return d
        }

        // lambda = 0 is the fastest route by construction, so it is the guaranteed-feasible floor and the
        // fallback if every scenic candidate overshoots. Measured, not assumed: if the router disagrees with
        // `fastest` here, that disagreement is exactly what we need to find out about.
        _ = try evaluate(0)

        var lo = 0.0
        var hi = Self.maxLambda
        while evaluations < maxEvaluations, hi - lo > Self.lambdaTolerance {
            let mid = lo + (hi - lo) / 2
            let d = try evaluate(mid)
            if d <= ceiling {
                lo = mid          // fits: we can afford to be pickier
            } else {
                hi = mid          // overshoots: back off
            }
        }

        guard let winner = best else {
            let shortest = seen.map(\.duration).min() ?? .infinity
            throw BudgetError.noFeasibleLambda(ceiling: ceiling, best: shortest, evaluations: evaluations)
        }

        return BudgetOutcome(
            lambda: winner.lambda,
            duration: winner.duration,
            ceiling: ceiling,
            evaluations: evaluations,
            usedBudget: budget == 0 || winner.duration >= fastest + Self.minBudgetUse * budget,
            monotonicityViolated: Self.violatesMonotonicity(seen)
        )
    }

    /// True if any measured pair has a larger lambda with a strictly shorter duration.
    ///
    /// Compares every pair rather than consecutive samples: the bisection visits lambdas out of order, so
    /// "consecutive in time" is not "adjacent in lambda", and a violation between two non-adjacent samples is
    /// just as much a violation.
    static func violatesMonotonicity(_ samples: [(lambda: Double, duration: TimeInterval)]) -> Bool {
        for a in samples {
            for b in samples where b.lambda > a.lambda {
                if b.duration < a.duration { return true }
            }
        }
        return false
    }
}
