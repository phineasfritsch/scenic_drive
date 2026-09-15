import Foundation
import Testing
@testable import ScenicKit

/// The other half of the budget promise: that the search actually SPENDS the extra minutes, and that it
/// costs a bounded number of router requests while doing it.
///
/// Split out of `LambdaSearchTests` at the 300-line cap, and split again for the same reason when the
/// refusals grew payload assertions - they are now `LambdaSearchRefusalTests`. Both cuts follow a section
/// boundary this suite already had rather than a line number: `LambdaSearchTests` asks whether the ceiling
/// holds, this asks whether the budget is used, and the third asks what happens when it cannot be.
///
/// A split is also the one edit that has silently broken the mutation harness before (a suite the vacuity
/// proof did not know to empty), so `TEST_FILES` in ops/mutate/budget_mutations.py lists all three and
/// `--prove-vacuity` fails loudly if one is missing.
@Suite("Lambda search - budget use and cost")
struct LambdaSearchBudgetUseTests {

    static let fastest: TimeInterval = 1800
    static let budget: TimeInterval = 1500

    static func monotone(_ slope: Double) -> (Double) -> TimeInterval {
        { lambda in fastest * (1 + slope * lambda) }
    }

    // MARK: - spending the budget, which is the other half of the promise

    @Test("the search climbs: it does not just return the fastest route and call it scenic")
    func actuallyUsesTheBudget() throws {
        // The meta-test the plan asks for. A "solver" that always answered lambda = 0 would satisfy the
        // ceiling on every single test above - the ceiling alone cannot tell a good search from a stub.
        let search = try LambdaSearch(fastest: Self.fastest, budget: Self.budget)
        let out = try search.search(Self.monotone(0.1))
        #expect(out.lambda > 0)
        #expect(out.duration > Self.fastest)
        #expect(out.usedBudget)
    }

    @Test("when nothing scenic fits, it says so instead of pretending")
    func reportsUnusedBudget() throws {
        // Any penalty at all sends the route somewhere far too slow, so the only feasible answer is lambda 0.
        let cliff: (Double) -> TimeInterval = { $0 == 0 ? Self.fastest : Self.fastest + 100_000 }
        let search = try LambdaSearch(fastest: Self.fastest, budget: Self.budget)
        let out = try search.search(cliff)
        #expect(out.lambda == 0)
        #expect(out.duration == Self.fastest)
        #expect(!out.usedBudget, "a route 0 seconds longer than the fastest has not used 25 minutes")
    }

    @Test("a zero budget returns the fastest route and counts as used, not as a failure")
    func zeroBudget() throws {
        let search = try LambdaSearch(fastest: Self.fastest, budget: 0)
        let out = try search.search(Self.monotone(0.5))
        #expect(out.lambda == 0)
        #expect(out.duration == Self.fastest)
        #expect(out.usedBudget, "there was no budget to leave unspent")
    }

    // MARK: - cost

    @Test("evaluations never exceed the cap, because each one is a request to our router")
    func boundedEvaluations() throws {
        for cap in 1...12 {
            let search = try LambdaSearch(fastest: Self.fastest, budget: Self.budget, maxEvaluations: cap)
            let out = try search.search(Self.monotone(0.2))
            #expect(out.evaluations <= cap)
        }
    }

    @Test("a cap of one still measures lambda = 0, so there is always a feasible answer")
    func capOfOne() throws {
        let search = try LambdaSearch(fastest: Self.fastest, budget: Self.budget, maxEvaluations: 1)
        let out = try search.search(Self.monotone(0.2))
        #expect(out.evaluations == 1)
        #expect(out.lambda == 0)
    }

    @Test("a cap below one is clamped to one, and a legal cap is left alone")
    func capIsClampedToAtLeastOne() throws {
        // F-E. Recorded in the harness as a KNOWN GAP reasoned "No behaviour to assert; the clamp is
        // defensive" - a gap booked as permanent that one assertion closes. Half right: the clamp cannot
        // change `evaluations`, because the seed runs before the loop. But `maxEvaluations` is PUBLIC and is
        // what a caller reads to see how many router requests this may cost; unclamped it reads -5.
        #expect(try LambdaSearch(fastest: Self.fastest, budget: Self.budget, maxEvaluations: 0)
                    .maxEvaluations == 1)
        #expect(try LambdaSearch(fastest: Self.fastest, budget: Self.budget, maxEvaluations: -5)
                    .maxEvaluations == 1)
        #expect(try LambdaSearch(fastest: Self.fastest, budget: Self.budget, maxEvaluations: 3)
                    .maxEvaluations == 3, "3 is a legal cap and must survive the clamp unchanged")
    }

    @Test("extraTime reports what was bought, with the sign it was bought at")
    func extraTime() throws {
        // The assertion here was `out.extraTime(...) == out.duration - Self.fastest`: the expected value
        // recomputed from the result being checked, which is true of any implementation that combines those
        // two numbers - including one that returns the magnitude and throws the sign away. Derived instead:
        // monotone(0.2) is 1800 * (1 + 0.2 * lambda) against a 3300 s ceiling, so lambda 4 measures 3240 and
        // is the slowest sample that still fits.
        let out = try LambdaSearch(fastest: Self.fastest, budget: Self.budget).search(Self.monotone(0.2))
        #expect(out.duration == 3240)
        #expect(out.extraTime(overFastest: Self.fastest) == 1440)
        #expect(out.extraTime(overFastest: Self.fastest) <= Self.budget)

        // F-H: every fixture in the suite had duration > fastest, so the SIGN had no witness and
        // `abs(duration - fastest)` survived - the difference between "you saved a minute" and "you spent a
        // minute". A later request coming back quicker than the recorded `fastest` is ordinary: `fastest`
        // was measured on an earlier one.
        let quicker = try LambdaSearch(fastest: Self.fastest, budget: 0).search { _ in Self.fastest - 60 }
        #expect(quicker.duration == 1740)
        #expect(quicker.extraTime(overFastest: Self.fastest) == -60)
    }

    // MARK: - the boundaries (reviewer-pr71, finding F3; the errors are in LambdaSearchRefusalTests)

    @Test("usedBudget is true at exactly half the budget and false just under it")
    func usedBudgetBoundaryIsExact() throws {
        // F3: the documented "at least half" boundary had no witness. partialBudgetIsNotUsed pinned the
        // interval (0.4, 0.55], which holds for any threshold in that range, and its own comment claimed it
        // "pins a boundary rather than a direction". These are the two sides of the actual boundary.
        //
        // fastest 1800 s, budget 1500 s, so half the budget is 750 s and the boundary duration is 2550 s.
        // Written out rather than computed from minBudgetUse, which is the constant under test.
        let atTheBoundary = try LambdaSearch(fastest: Self.fastest, budget: Self.budget)
            .search { _ in 2550 }
        #expect(atTheBoundary.usedBudget, "2550 s is exactly fastest + half the budget; the rule is >=")

        let justUnder = try LambdaSearch(fastest: Self.fastest, budget: Self.budget)
            .search { _ in 2549 }
        #expect(!justUnder.usedBudget, "one second under the half-budget boundary is not using the budget")

        let wellOver = try LambdaSearch(fastest: Self.fastest, budget: Self.budget)
            .search { _ in 3000 }
        #expect(wellOver.usedBudget)
    }

    @Test("a zero budget counts as used, because there was none to spend")
    func zeroBudgetIsAlwaysUsed() throws {
        let out = try LambdaSearch(fastest: Self.fastest, budget: 0).search { _ in Self.fastest }
        #expect(out.usedBudget, "asking for no extra time and getting none is not a failure to use it")

        // The `budget == 0` short-circuit only earns its place when the router BEATS the recorded fastest
        // duration - which it can, since `fastest` was measured on an earlier request. At exactly `fastest`
        // the arithmetic gives the same answer either way, so a fixture there pins nothing: removing the
        // short-circuit was MISSED until this case existed.
        let quicker = try LambdaSearch(fastest: Self.fastest, budget: 0).search { _ in Self.fastest - 60 }
        #expect(quicker.usedBudget, "a zero budget is spent by definition, whatever the router returned")

        // And the short-circuit is for ZERO, not for "small". Widening it to `budget <= 0.5` changed 638
        // cases in the standalone control - every one of them a budget being reported as spent when none of
        // it was - and no test objected. 0.4 s is an absurd budget and a legal one; half of it is 0.2 s, and
        // a route that buys 0 s has not bought that.
        let tiny = try LambdaSearch(fastest: Self.fastest, budget: 0.4).search { _ in Self.fastest }
        #expect(!tiny.usedBudget, "0.4 seconds is a budget, and none of it was spent")
    }

    @Test("the search stops on lambdaTolerance, not only on the evaluation cap")
    func toleranceTerminatesTheSearch() throws {
        // F2: reviewer-pr71 measured that the `hi - lo > lambdaTolerance` condition never fired in any test,
        // so deleting it was free - and widening it from 0.05 to 0.75 silently cut a search from 6 router
        // requests to 5 with the whole suite green. Every default-configured search stops on the evaluation
        // cap first, so the tolerance only becomes observable with the cap lifted out of the way.
        //
        // Derived by hand, and I got it wrong the first time: I wrote 10 and the answer is 9. The condition
        // is checked BEFORE each evaluation, so a midpoint is taken while the bracket is still wider than the
        // tolerance. Widths 8, 4, 2, 1, 0.5, 0.25, 0.125, 0.0625 are each > 0.05 and each buy a midpoint;
        // 0.03125 is not, and the loop stops. 1 seed + 8 midpoints = 9, well inside the cap of 30. The code
        // was right and the derivation was wrong, which is the only reason worth changing a test for.
        let search = try LambdaSearch(fastest: Self.fastest, budget: Self.budget, maxEvaluations: 30)
        let out = try search.search { _ in Self.fastest }
        #expect(out.evaluations == 9, "stopped after \(out.evaluations) evaluations, not on the tolerance")
    }
}
