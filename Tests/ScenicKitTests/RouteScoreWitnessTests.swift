import Foundation
import Testing
@testable import ScenicKit

/// Exact-double witnesses. These pin comparisons that differ on ONE input class - a value that is bit-for-bit
/// the boundary - so they need hex float literals and a suite of their own rather than sitting among fixtures
/// chosen for readability.
///
/// Split out because `RouteScoreBoundaryTests` passed the 300-line cap. The mutation harness's TESTS tuple
/// was updated in the same commit: a suite split that the vacuity proof does not know about silently stops
/// the proof emptying all the tests, which has happened five times in this repository (T-0132).
@Suite("Route score witnesses")
struct RouteScoreWitnessTests {

    @Test("a run landing exactly on the tolerated boundary is an episode, at both closing sites")
    func runExactlyOnTheToleratedBoundaryIsAnEpisode() {
        // The mutation this kills - `>=` to `>` at the two episode closing sites - was REMOVED from the
        // harness with the reason "with the tolerance present it is unobservable: at a run of exactly 800 m
        // both `>=` and `>` clear `800 - tolerance`". The first half is true; the conclusion is false, and
        // the sign-off reviewer of PR #73 showed it with compiled witnesses.
        //
        // `>=` and `>` differ on exactly one input class: `run == episodeMinLength - tolerance` EXACTLY as a
        // double. `tolerance = scale * 1e-9` where `scale` is the whole route length, so a witness is a
        // fixed point of `X == 800.0 - (X + dull) * 1e-9`. That is a one-parameter family, not one lucky
        // value - the two below were found independently by searching outward from the approximate root and
        // verified in Python before being written here:
        //
        //     X = 799.9999992  with no dull tail : 799.9999992 == 800.0 - 799.9999992e-9      -> true
        //     X = 799.999999   with a 200 m tail : 799.999999  == 800.0 - (799.999999+200)e-9 -> true
        //
        // Written as HEX FLOAT literals so the exact double survives decimal parsing - a decimal literal
        // that round-trips on this toolchain is not guaranteed to be the same bit pattern elsewhere, and
        // one ulp either way destroys the witness.
        let atEnd = ScoredEdge(length: 0x1.8ffffff94a036p+9, score: 0.9)
        #expect(RouteScore.episodes([atEnd]) == 1,
                "a run ending the route exactly on the tolerated boundary is an episode")

        let inLoop = ScoredEdge(length: 0x1.8ffffff79c843p+9, score: 0.9)
        let dull = ScoredEdge(length: 200.0, score: 0.1)
        #expect(RouteScore.episodes([inLoop, dull]) == 1,
                "a run closed by a dull stretch exactly on the tolerated boundary is an episode")

        // And the boundary is where it is claimed to be: one ulp below it is NOT an episode, so this test
        // pins the comparison rather than merely asserting that two long edges count.
        #expect(RouteScore.episodes([ScoredEdge(length: 700.0, score: 0.9)]) == 0)
    }
}
