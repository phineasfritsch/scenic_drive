import Foundation
import Testing
@testable import ScenicKit

/// Where the bisection looks NEXT, and what steering it wrong costs the user.
///
/// `search` contains two `d <= ceiling` comparisons and they do different jobs. The one inside `evaluate`
/// decides whether a measured route is allowed to become `best`: that is the guard which ENFORCES the
/// invariant, and it is covered - measured, not assumed, by loosening it to `* 1.01` and reading the
/// failures out: `the ceiling holds across a wide sweep of slopes and budgets`, `a route one second over
/// the ceiling is over the ceiling`, `extraTime reports what was bought, with the sign it was bought at`,
/// and the first test below. The one in the bisection loop decides which half of the bracket to keep. This
/// suite is about the second one, which had a witness in neither direction for three rounds.
///
/// The claim that made that look acceptable was that the steering guard is a no-op - *"loosening the bracket
/// makes the search waste an evaluation exploring an infeasible region"*. It is not. Only lambdas that are
/// MEASURED can become `best`, so the bracket decides which routes are candidates at all: with
/// `d <= ceiling * 1.01` a user with 25 minutes to spend is handed the fastest route and `usedBudget` false
/// after paying for six router requests - measured below, where the mutant returns lambda 0 at 1800 s. The
/// reviewer's own sweep found a worse case on a curve whose seed is itself infeasible, where the same
/// mutation turns a plan into *"couldn't reach that address"*; that one is their measurement, not one this
/// suite reproduces. The ceiling is never breached either way -
/// which is exactly why nothing caught it - but the other half of the promise, that the extra minutes get
/// SPENT, is broken.
///
/// Both fixtures are derived from the constants by hand, in the comments, and neither reads a bound off the
/// result it is checking.
@Suite("Lambda search - steering the bracket")
struct LambdaSearchSteeringTests {

    static let fastest: TimeInterval = 1800
    static let budget: TimeInterval = 1500

    /// Records the lambdas the router was asked for, in order, which is what the steering guard decides.
    final class Recorder: @unchecked Sendable { var asked: [Double] = [] }

    @Test("a duration just over the ceiling must steer the bracket DOWN")
    func steersDownWhenTheSampleIsOverTheCeiling() throws {
        // Ceiling 3300. The infeasible samples here are 3310 s - ten seconds over, 0.3%, comfortably inside
        // the 1% a loosened bracket forgives. Every other fixture in the package that goes over the ceiling
        // goes far over it (4000, 5000, 100_000), which is why a 1% slip changed nothing anywhere.
        //
        // Derived by hand from maxLambda 8 and the cap of 6:
        //   0    -> 1800  fits  -> best = (0, 1800); bracket [0, 8]
        //   4    -> 3310  OVER  -> hi = 4
        //   2    -> 3200  fits  -> lo = 2, best = (2, 3200)
        //   3    -> 3200  fits  -> lo = 3, best = (3, 3200)   equal duration, larger lambda, so it wins
        //   3.5  -> 3310  OVER  -> hi = 3.5
        //   3.25 -> 3310  OVER  -> hi = 3.25, and the sixth evaluation ends the search.
        //
        // With the guard loosened to `d <= ceiling * 1.01` the very first midpoint is forgiven and the
        // bracket climbs instead: 4, 6, 7, 7.5, 7.75, every one of them 3310 s and none of them eligible to
        // be `best`. The 3200 s route is never measured, so it can never be returned, and the search hands
        // back the seed it started with.
        let ceiling = Self.fastest + Self.budget                    // 3300, computed here
        let overByTen: (Double) -> TimeInterval = { lambda in
            if lambda == 0 { return Self.fastest }
            return lambda <= 3 ? 3200 : 3310
        }
        let rec = Recorder()
        let out = try LambdaSearch(fastest: Self.fastest, budget: Self.budget)
            .search { rec.asked.append($0); return overByTen($0) }

        #expect(rec.asked == [0, 4, 2, 3, 3.5, 3.25],
                "a sample over the ceiling has to move `hi`; climbing means the bracket forgave 3310 s")
        #expect(out.lambda == 3)
        #expect(out.duration == 3200, "the scenic route that fits, not the fastest one")
        #expect(out.duration <= ceiling)
        #expect(out.usedBudget, "3200 s spends 1400 s of the 1500 s offered")
        #expect(out.evaluations == 6)
    }

    @Test("a duration exactly on the ceiling must steer the bracket UP")
    func steersUpWhenTheSampleIsExactlyOnTheCeiling() throws {
        // The invariant is `<=`, so a route landing EXACTLY on fastest + budget fits, and everything above
        // it in the bracket is still worth looking at. `if d < ceiling` abandons that whole half. No fixture
        // could see it: every other flat curve in the package sits well UNDER its ceiling
        // (`tieBreaksTowardTheHigherLambda` is flat at 1800 s against 3300), where `<` and `<=` cannot
        // disagree, and the one fixture that touches the boundary - `ceilingIsNotApproximate` - puts it one
        // second on the WRONG side, where they also agree.
        //
        // Derived by hand: every sample is 3300, so every one fits, the bracket climbs 0, 4, 6, 7, 7.5,
        // 7.75, and the tie-break keeps the largest lambda among equally fast routes - the one that avoided
        // the most dull road for the same time. With `<` the bracket collapses downward instead
        // (0, 4, 2, 1, 0.5, 0.25) and the answer is lambda 4: the same 3300 seconds of driving, with more
        // dull road in it, bought with the same six router requests.
        let onTheCeiling: (Double) -> TimeInterval = { _ in Self.fastest + Self.budget }
        let rec = Recorder()
        let out = try LambdaSearch(fastest: Self.fastest, budget: Self.budget)
            .search { rec.asked.append($0); return onTheCeiling($0) }

        #expect(rec.asked == [0, 4, 6, 7, 7.5, 7.75],
                "a sample exactly on the ceiling fits, so the bracket must move `lo` up")
        #expect(out.lambda == 7.75, "the most scenic of a set of routes that all cost 3300 s")
        #expect(out.duration == 3300)
        #expect(out.duration <= Self.fastest + Self.budget)
        #expect(out.usedBudget)
    }
}
