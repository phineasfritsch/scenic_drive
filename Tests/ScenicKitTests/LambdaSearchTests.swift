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
        // The headline invariant test, and it was self-referential: `out.duration <= out.ceiling` takes
        // BOTH sides from the code under test, so mutating `ceiling` to `fastest + budget + 1` left it
        // untouched. A reviewer found that. The whole ceiling guarantee rested on one other fixture that
        // happened to recompute the constant independently.
        //
        // The expected bound is now computed in the test, from the inputs the test chose.
        for slopeTenths in 0...40 {
            let slope = Double(slopeTenths) / 40.0          // 0 ... 1.0 extra per unit lambda
            for budgetMinutes in [0, 1, 5, 10, 25, 60, 240] {
                let budget = TimeInterval(budgetMinutes * 60)
                let expectedCeiling = Self.fastest + budget            // independent of the code under test
                let search = try LambdaSearch(fastest: Self.fastest, budget: budget)
                let out = try search.search(Self.monotone(slope))
                #expect(out.ceiling == expectedCeiling,
                        "slope \(slope) budget \(budget): ceiling \(out.ceiling) != \(expectedCeiling)")
                #expect(out.duration <= expectedCeiling,
                        "slope \(slope) budget \(budget): \(out.duration) > \(expectedCeiling)")
            }
        }
    }

    @Test("the search's own constants are pinned")
    func constantsArePinned() {
        // Every other test reaches these through their symbols, so their values had no witness. A reviewer
        // demonstrated all three:
        //   minBudgetUse 0.5 -> 0.05  green, and a route buying 90 s of a 1500 s budget reports usedBudget
        //   maxLambda    8 -> 16      green, and 4 of 6 router requests land in an infeasible region
        //   lambdaTolerance 0.05 -> 0.75  green, and the search gives back one of the twelve requests the
        //                                 plan pays for
        // The suite constrained minBudgetUse only to 0 < m <= 0.93, because its fixtures buy 1395 s and 0 s
        // of a 1500 s budget - nothing in between.
        #expect(LambdaSearch.maxLambda == 8.0)
        #expect(LambdaSearch.lambdaTolerance == 0.05)
        #expect(LambdaSearch.minBudgetUse == 0.5)
    }

    @Test("a route that buys well under half the budget has not used it")
    func partialBudgetIsNotUsed() throws {
        // The fixture the suite was missing. Existing tests buy either 93% of the budget or none of it, so
        // any threshold in between passed. This one buys about 40%: over zero, under half.
        //
        // usedBudget's own doc comment says a user offered 25 minutes and handed 90 seconds "has been told
        // yes and given no" - and with minBudgetUse at 0.05 that user was being told yes.
        let budget = Self.budget                                    // 1500 s
        let target = Self.fastest + 0.4 * budget                    // 40% of it
        let plateau: (Double) -> TimeInterval = { $0 < 1.0 ? Self.fastest : target }
        let search = try LambdaSearch(fastest: Self.fastest, budget: budget)
        let out = try search.search(plateau)
        #expect(out.duration == target)
        #expect(!out.usedBudget, "40% of the budget is not half of it")

        // And just over half is used, so the assertion pins a boundary rather than a direction.
        let justOver = Self.fastest + 0.55 * budget
        let plateau2: (Double) -> TimeInterval = { $0 < 1.0 ? Self.fastest : justOver }
        let out2 = try LambdaSearch(fastest: Self.fastest, budget: budget).search(plateau2)
        #expect(out2.duration == justOver)
        #expect(out2.usedBudget)
    }

    @Test("among equally fast feasible routes, the most scenic one wins")
    func tieBreaksTowardTheHigherLambda() throws {
        // A router whose duration does not depend on lambda at all: every candidate costs the same. Lambda
        // penalises dull edges, so the LARGEST feasible lambda is the route that avoided the most dull road
        // for that identical time - strictly better, for free.
        //
        // The original code kept whichever equal-duration candidate it saw first, which on this curve is
        // lambda 0: the least scenic of a set of equally fast options. Nothing objected when a mutation
        // flipped the comparison, because nothing had an opinion. Now it does.
        let flat: (Double) -> TimeInterval = { _ in Self.fastest }
        let search = try LambdaSearch(fastest: Self.fastest, budget: Self.budget)
        let out = try search.search(flat)
        #expect(out.duration == Self.fastest)
        #expect(out.lambda > 0, "an equally fast but more scenic option was available and was not taken")

        // And the winner must still be a lambda that was actually measured.
        //
        // Written out as LITERALS, because the previous form asked the object under test what it had done and
        // then checked it against itself: `rec.asked.contains(out2.lambda)` and
        // `out2.lambda == rec.asked.max()` hold for any search that returns something it asked for, including
        // one that asks for entirely the wrong things. reviewer-pr71 measured the consequence - the mutation
        // "return the bracket instead of a measured candidate" was caught by ONE unrelated test, and slipped
        // straight through the test written against it, because on a flat curve the bracket `lo` IS the
        // largest lambda asked.
        //
        // Derived by hand from the constants: seed at 0, then bisect [0, maxLambda = 8] with every candidate
        // feasible, for maxEvaluations = 6 total. 4, 6, 7, 7.5, 7.75 - stopping on the evaluation cap, not on
        // lambdaTolerance = 0.05, since 8 - 7.75 is still above it. This sequence pins maxLambda's USE, which
        // its value being pinned elsewhere did not: at maxLambda 16 the search would ask 0, 8, 12, 14, 15, 15.5.
        final class Recorder: @unchecked Sendable { var asked: [Double] = [] }
        let rec = Recorder()
        let out2 = try LambdaSearch(fastest: Self.fastest, budget: Self.budget)
            .search { rec.asked.append($0); return Self.fastest }
        #expect(rec.asked == [0, 4, 6, 7, 7.5, 7.75])
        #expect(out2.lambda == 7.75)
    }

    @Test("the default search spends exactly the evaluations it is configured for")
    func evaluationCountIsPinned() throws {
        // boundedEvaluations asserts only `<= cap`, and returnsMeasuredValues asserts
        // `rec.asked.count == out.evaluations`, which stays self-consistent when the search silently does
        // fewer. Widening lambdaTolerance from 0.05 to 0.75 cut the search from 6 evaluations to 5 with the
        // whole suite green - one of the twelve router requests per plan, given back for nothing.
        let search = try LambdaSearch(fastest: Self.fastest, budget: Self.budget)
        let out = try search.search(Self.monotone(0.2))
        #expect(out.evaluations == 6, "the default cap is 6 and this curve exhausts it")
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
        // not because the curve behaved. Bound computed here, not read off the result - the mechanical
        // check found three more of these after the headline one was fixed, which is a fair argument that a
        // person cannot be trusted to spot the last of them by eye.
        #expect(out.duration <= Self.fastest + Self.budget)

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
        #expect(out.duration <= fastest + 1500)          // the bound this test chose, not the one it got

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
        #expect(out.duration <= ceiling)                 // the local constant, computed above
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
}
