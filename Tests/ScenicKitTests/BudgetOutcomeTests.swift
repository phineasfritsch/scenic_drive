import Foundation
import Testing
@testable import ScenicKit

/// What `BudgetOutcome` does with the numbers it is HANDED, as opposed to what the search puts in it.
///
/// The four `LambdaSearch*` suites all reach this type through `search`, which only ever constructs an
/// outcome from a measured, verified-feasible sample. So every fixture they own arrives with
/// `duration <= ceiling` and, until the sixth review, at a whole number of seconds - and that left the
/// initializer's own discipline with no witness at all. Two mutations survived all 53 tests there:
/// `self.duration = min(duration, ceiling)`, which launders an out-of-budget ETA into an in-budget-looking
/// one, and `(duration - fastest).rounded()`, which throws away the fraction of a second the route was
/// bought at.
///
/// `init` is `public`. Anything in the app may build one of these - a decoder, a cache, a test double, a
/// future planner that measures a route by some other route than this bisection - and the type's doc comment
/// makes a promise to all of them: `duration` "is never interpolated, never the bisection midpoint's
/// estimate, and never the ceiling itself". This suite is that promise, asserted where it is made rather
/// than only where this one caller happens to satisfy it.
///
/// Listed in `TEST_FILES` (ops/mutate/budget_tree.py) like every other suite that can see these types: a
/// suite the vacuity proof does not know to empty is how that proof was false once.
@Suite("BudgetOutcome - the numbers it is handed")
struct BudgetOutcomeTests {

    @Test("the outcome stores the duration it was given, never the ceiling")
    func durationIsNotLaundered() {
        // F-R6-1. `min(duration, ceiling)` is what a well-meaning edit writes to "enforce" the CLAUDE.md
        // ceiling here, and it is precisely wrong: the invariant is enforced by only ever RETURNING a
        // measured feasible sample, so a clamp in the initializer cannot make an over-budget route fit - it
        // can only make one look as though it did. 5000 s against a 3300 s ceiling is the case the search
        // itself never produces and the initializer must not rewrite.
        let overCeiling = BudgetOutcome(lambda: 3, duration: 5000, ceiling: 3300,
                                        evaluations: 4, usedBudget: false, monotonicityViolated: false)
        #expect(overCeiling.duration == 5000,
                "the initializer stores what it was handed; it does not clamp an ETA down to the ceiling")
        #expect(overCeiling.ceiling == 3300)

        // And not rounded, and not moved by the smallest step a Double has. 1800.5 and 0.5 are both exact in
        // binary - 1800.4 is not, and a fixture spelled that way is red against the pristine source.
        let fractional = BudgetOutcome(lambda: 2, duration: 1800.5, ceiling: 3300,
                                       evaluations: 5, usedBudget: true, monotonicityViolated: false)
        #expect(fractional.duration == 1800.5,
                "a duration the router returned to a half second is stored to a half second")
    }

    @Test("extraTime keeps the fraction of a second the route was bought at")
    func extraTimeKeepsTheFraction() {
        // F-R6-2. `extraTime` is one of the two numbers this type hands a user, and every fixture that saw
        // it - through the search - was a whole number of seconds: 1440 and -60. `.rounded()` therefore
        // survived all 53 tests. The ceiling gained a fractional witness in the fifth round (N-SG5, a 0.4 s
        // budget); this is the same witness for the other number, ten lines down the same 64-line file.
        let bought = BudgetOutcome(lambda: 3, duration: 1800.5, ceiling: 3300,
                                   evaluations: 4, usedBudget: false, monotonicityViolated: false)
        #expect(bought.extraTime(overFastest: 1800) == 0.5,
                "half a second bought is half a second reported, not a whole one")

        // The sign and the fraction together. A later request coming back quicker than the recorded
        // `fastest` is ordinary - `fastest` was measured on an earlier one - and `-0.5` rounds to `-1`.
        let quicker = BudgetOutcome(lambda: 0, duration: 1799.5, ceiling: 3300,
                                    evaluations: 1, usedBudget: true, monotonicityViolated: false)
        #expect(quicker.extraTime(overFastest: 1800) == -0.5,
                "half a second saved is half a second reported, with its sign")
    }
}
