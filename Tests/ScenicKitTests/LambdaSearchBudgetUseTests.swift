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
}
