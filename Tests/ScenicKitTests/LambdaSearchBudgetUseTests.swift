import Foundation
import Testing
@testable import ScenicKit

/// The other half of the budget promise: that the search actually SPENDS the extra minutes, that it
/// costs a bounded number of router requests, and that it refuses rather than guesses.
///
/// Split out of `LambdaSearchTests` at the 300-line cap. The split is along the section boundary the
/// suite already had, not at an arbitrary line: `LambdaSearchTests` asks whether the ceiling holds,
/// this asks whether the budget is used. Cutting at a line number would have left half of one argument
/// in each file.
@Suite("Lambda search - budget use, cost and refusals")
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

    // MARK: - refusals

    @Test("a router that overshoots even at lambda zero is refused, not rounded down to a breach")
    func noFeasibleLambdaThrows() throws {
        let search = try LambdaSearch(fastest: Self.fastest, budget: 60)
        #expect(throws: BudgetError.self) {
            _ = try search.search { _ in Self.fastest + 99_999 }
        }
    }

    @Test("nonsense from the router is refused rather than compared",
          arguments: [TimeInterval.nan, .infinity, -1])
    func refusesNonsense(bad: TimeInterval) throws {
        let search = try LambdaSearch(fastest: Self.fastest, budget: Self.budget)
        #expect(throws: BudgetError.self) { _ = try search.search { _ in bad } }
    }

    @Test("invalid inputs are refused at construction",
          arguments: [(TimeInterval(0), TimeInterval(60)), (-1, 60), (.nan, 60),
                      (1800, -1), (1800, -0.5), (1800, -1e-9), (1800, .nan), (1800, .infinity)])
    func refusesBadInputs(fastest: TimeInterval, budget: TimeInterval) {
        #expect(throws: BudgetError.self) { _ = try LambdaSearch(fastest: fastest, budget: budget) }
    }

    @Test("the search propagates a router error rather than swallowing it")
    func propagatesRouterErrors() throws {
        struct Offline: Error {}
        let search = try LambdaSearch(fastest: Self.fastest, budget: Self.budget)
        #expect(throws: Offline.self) { _ = try search.search { _ in throw Offline() } }
    }

    @Test("extraTime reports what was actually bought")
    func extraTime() throws {
        let search = try LambdaSearch(fastest: Self.fastest, budget: Self.budget)
        let out = try search.search(Self.monotone(0.2))
        #expect(out.extraTime(overFastest: Self.fastest) == out.duration - Self.fastest)
        #expect(out.extraTime(overFastest: Self.fastest) <= Self.budget)
    }

    // MARK: - the boundaries and the errors (reviewer-pr71, findings F3 and F4)

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
    }

    @Test("every BudgetError says what happened, in a sentence with the numbers in it")
    func errorsDescribeThemselves() {
        // F4: every error assertion in this suite was type-only, so 41 lines of public API - including the
        // whole CustomStringConvertible conformance - had no behavioural coverage at all. These strings
        // reach a log and a bug report, so they are pinned as text.
        #expect(String(describing: BudgetError.notADuration(-1))
                == "fastest duration is not a positive finite number of seconds: -1.0")
        #expect(String(describing: BudgetError.notABudget(-5))
                == "budget is not a non-negative finite number of seconds: -5.0")
        #expect(String(describing: BudgetError.routerReturnedNonsense(lambda: 2.5, duration: -3))
                == "router returned -3.0 s at lambda 2.5")
        #expect(String(describing: BudgetError.noFeasibleLambda(ceiling: 3300, best: 4000, evaluations: 6))
                == "no lambda produced a route within the 3300.0 s ceiling in 6 evaluations; "
                + "the shortest seen was 4000.0 s")
    }

    @Test("the error carries the values, not just the case")
    func errorsCarryTheirNumbers() throws {
        // A typed throw whose payload is wrong is worse than an untyped one: it puts a plausible wrong number
        // in front of whoever reads it. Pinned by pattern-matching the payload, not by the case alone.
        do {
            _ = try LambdaSearch(fastest: -1, budget: Self.budget)
            Issue.record("a negative fastest duration must be refused")
        } catch let e as BudgetError {
            guard case let .notADuration(t) = e else {
                Issue.record("wrong case: \(e)"); return
            }
            #expect(t == -1)
        }

        do {
            _ = try LambdaSearch(fastest: Self.fastest, budget: -5)
            Issue.record("a negative budget must be refused")
        } catch let e as BudgetError {
            guard case let .notABudget(b) = e else {
                Issue.record("wrong case: \(e)"); return
            }
            #expect(b == -5)
        }

        do {
            _ = try LambdaSearch(fastest: Self.fastest, budget: Self.budget).search { l in
                l == 0 ? -7 : Self.fastest
            }
            Issue.record("a negative duration from the router must be refused")
        } catch let e as BudgetError {
            guard case let .routerReturnedNonsense(lambda, duration) = e else {
                Issue.record("wrong case: \(e)"); return
            }
            #expect(lambda == 0)
            #expect(duration == -7)
        }
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
