import Foundation
import Testing
@testable import ScenicKit

/// The one invariant these tests exist for, from CLAUDE.md:
/// *"The extra-time budget is a **ceiling**: returned ETA <= fastest + budget. Always."*
///
/// "Always" is the hard word. It has to hold for a router that is monotone, for one that is not, for a
/// budget of zero, for a router that answers the same number every time, and for one whose duration jumps.
/// A test suite that only exercises the well-behaved case is testing the happy path of a promise whose whole
/// value is that it has no exceptions.
@Suite("Lambda search")
struct LambdaSearchTests {

    /// A 30-minute commute with 25 extra minutes offered - the plan's own example.
    static let fastest: TimeInterval = 1800
    static let budget: TimeInterval = 1500

    /// Duration rises smoothly with lambda: the well-behaved router the plan assumes.
    static func monotone(_ slope: Double) -> (Double) -> TimeInterval {
        { lambda in fastest * (1 + slope * lambda) }
    }

    // MARK: - the invariant

    @Test("the ceiling holds across a wide sweep of slopes and budgets")
    func ceilingAlwaysHolds() throws {
        for slopeTenths in 0...40 {
            let slope = Double(slopeTenths) / 40.0          // 0 ... 1.0 extra per unit lambda
            for budgetMinutes in [0, 1, 5, 10, 25, 60, 240] {
                let budget = TimeInterval(budgetMinutes * 60)
                let search = try LambdaSearch(fastest: Self.fastest, budget: budget)
                let out = try search.search(Self.monotone(slope))
                #expect(out.duration <= out.ceiling,
                        "slope \(slope) budget \(budget): \(out.duration) > \(out.ceiling)")
            }
        }
    }

    @Test("the returned duration is the one the router gave for the returned lambda, not an estimate")
    func returnsMeasuredValues() throws {
        // Records what was asked, so the assertion can be "this pair was actually observed" rather than
        // "this pair looks plausible". Interpolating a midpoint is the failure being excluded.
        final class Recorder: @unchecked Sendable {
            var asked: [Double: TimeInterval] = [:]
        }
        let rec = Recorder()
        let search = try LambdaSearch(fastest: Self.fastest, budget: Self.budget)
        let out = try search.search { lambda in
            let d = Self.monotone(0.25)(lambda)
            rec.asked[lambda] = d
            return d
        }
        #expect(rec.asked[out.lambda] == out.duration)
        #expect(rec.asked.count == out.evaluations)
    }

    // MARK: - the assumption that is not a theorem

    @Test("a non-monotone router cannot breach the ceiling, even when the dip is never sampled")
    func nonMonotoneRouterIsSafe() throws {
        // A router that gets FASTER as the scenic penalty rises, over one stretch. Physically odd, entirely
        // possible from alternative-route selection: a heavier penalty can flip the engine onto a different
        // corridor that happens to be quicker. A bisection that trusts monotonicity concludes the whole
        // lower bracket is feasible and can return a lambda it never measured.
        let bumpy: (Double) -> TimeInterval = { lambda in
            switch lambda {
            case ..<1.0: return Self.fastest
            case ..<3.0: return Self.fastest + 4000        // way over any sane ceiling
            case ..<6.0: return Self.fastest + 100         // and back down again
            default:     return Self.fastest + 9000
            }
        }
        let search = try LambdaSearch(fastest: Self.fastest, budget: Self.budget)
        let out = try search.search(bumpy)

        // The invariant holds, and that is the point. It holds because the returned duration was MEASURED,
        // not because the curve behaved.
        #expect(out.duration <= out.ceiling)

        // Deliberately NOT asserted: that the violation was detected. This bisection samples
        // 0, 4, 6, 5, 5.5, 5.75 and every one of those lands outside the 1..3 spike, so the dip is invisible
        // to it and `monotonicityViolated` is false. Asserting true here is what the first draft of this
        // test did, and it failed - correctly. The flag reports observed violations, and an unsampled dip is
        // not an observed one. Detection is covered by the next test, on a curve the search does sample.
        #expect(!out.monotonicityViolated)
    }

    @Test("a violation among the sampled lambdas is reported")
    func detectsSampledViolation() throws {
        // fastest is 3000 here so that measure(0) agrees with it; the violation is that lambda 4 comes back
        // a thousand seconds QUICKER than lambda 0, which the bisection samples directly.
        let fastest: TimeInterval = 3000
        let dips: (Double) -> TimeInterval = { $0 >= 4.0 ? 2000 : 3000 }
        let search = try LambdaSearch(fastest: fastest, budget: 1500)
        let out = try search.search(dips)
        #expect(out.monotonicityViolated)
        #expect(out.duration <= out.ceiling)

        // This curve is also the one place where the bisection's final bracket and the correct answer come
        // apart, which makes it the fixture for two failures the rest of the suite could not see.
        //
        // The bracket `lo` climbs to about 7.5, because every lambda from 4 up is feasible. But the BEST
        // feasible route - the slowest one that still fits, which is the most scenic one affordable - is at
        // lambda 0 with 3000 s. So:
        //   * returning the bracket instead of the measured winner gives lambda 7.5, and
        //   * overwriting the winner with each new feasible sample gives 2000 s.
        // Both produce a believable lambda and a believable ETA. Only pinning the actual pair catches them.
        #expect(out.lambda == 0)
        #expect(out.duration == 3000)
    }

    @Test("a route one second over the ceiling is over the ceiling")
    func ceilingIsNotApproximate() throws {
        // The sweep in `ceilingAlwaysHolds` uses smooth curves, so no sample ever lands in the narrow band
        // just above the ceiling - which means a comparison loosened to `<= ceiling * 1.01` passes it. The
        // invariant says "always", so the boundary needs a fixture that sits exactly on the wrong side of it.
        let ceiling = Self.fastest + Self.budget            // 3300
        let barelyOver: (Double) -> TimeInterval = { $0 < 2.0 ? Self.fastest : ceiling + 1 }
        let search = try LambdaSearch(fastest: Self.fastest, budget: Self.budget)
        let out = try search.search(barelyOver)
        #expect(out.duration <= out.ceiling)
        #expect(out.duration == Self.fastest, "the only feasible route here is the fastest one")
    }

    @Test("a well-behaved router is not falsely accused of non-monotonicity")
    func monotoneIsNotFlagged() throws {
        let search = try LambdaSearch(fastest: Self.fastest, budget: Self.budget)
        let out = try search.search(Self.monotone(0.3))
        #expect(!out.monotonicityViolated)
    }

    @Test("monotonicity is judged across all pairs, not just consecutive samples")
    func monotonicityComparesAllPairs() {
        // Visited in bisection order: 0, 4, 2 - so by TIME the samples decrease then increase, but by LAMBDA
        // the violation is between the first and third. Comparing consecutive samples would miss it.
        let samples: [(lambda: Double, duration: TimeInterval)] = [(0, 100), (4, 300), (2, 50)]
        #expect(LambdaSearch.violatesMonotonicity(samples))
        #expect(!LambdaSearch.violatesMonotonicity([(0, 100), (4, 300), (2, 200)]))
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
                      (1800, -1), (1800, .nan), (1800, .infinity)])
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
