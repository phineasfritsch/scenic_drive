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

    }

    @Test("a run one ulp short of the tolerated boundary is not an episode")
    func runOneUlpBelowTheToleratedBoundaryIsNotAnEpisode() {
        // This assertion used to read `episodes([ScoredEdge(length: 700.0, score: 0.9)]) == 0` under the
        // comment "one ulp below it is NOT an episode, so this test pins the comparison". 700 m is 100 m
        // below the boundary, eleven orders of magnitude out from one ulp. The one-ulp property was true
        // and nothing in the suite checked it - the same defect the test above was written to close, inside
        // that test. The coarse case is not lost: `thresholdStrictness` already pins 799 m at zero.
        //
        // 0x1.8ffffff94a035p+9 = 799.9999991999999 is exactly one ulp below the at-end witness above
        // (799.9999992), a gap of 1.1368683772161603e-13 m. The bound `800.0 - scale * 1e-9` is
        // 799.9999992 for both fixtures - one ulp of `scale` moves the tolerance by about 1e-22 - so this
        // is the LARGEST run that is not an episode, and the pair straddles the boundary with nothing
        // between them.
        //
        // That is what makes the pair pin the tolerance's USE SITE and not merely the constant. Measured in
        // Python against the same arithmetic: this fixture becomes an episode for any tolerance constant at
        // or above 1.0000000837403711e-09, so it refuses a use site inlined at 1e-6, 1e-7 or 1e-8 of route
        // length, each of which the suite accepted before; and the witness above refuses a tolerance of
        // zero, one on the wrong side, or one absolute in metres.
        #expect(RouteScore.episodes([ScoredEdge(length: 0x1.8ffffff94a035p+9, score: 0.9)]) == 0,
                "one ulp below the tolerated boundary the run is short, so it is not an episode")
    }

    @Test("the percentile boundary landing exactly on the tolerated bound takes the lower score")
    func percentileExactlyOnTheToleratedBoundaryTakesTheLowerScore() {
        // The twin of the episode witnesses above, at the other accumulated-length boundary in this file.
        // `for (i, c) in running.enumerated() where c >= target - tolerance` is the same `>=`-against-a-
        // tolerated-boundary comparison as the two episode closing sites; `RouteScore` states the behaviour
        // twice - "the tie is broken deterministically toward the lower score" - and until this test
        // nothing asserted it. Turning that one character into `>` passed all 40 tests.
        //
        // `>=` and `>` differ on exactly one input class: `c == target - tolerance` exactly as a double.
        // With a 1000 m high edge that is a fixed point of `a == (a + 1000) * 0.9 - (a + 1000) * 1e-9`, and
        // it is not one lucky value - the solution is a BAND of ten consecutive doubles
        // (0x1.193fffcb923a1p+13 ... 0x1.193fffcb923aap+13), because the bound is flat under rounding
        // across them. The fixture below sits FIVE ulps into that band, five from either edge, so it is not
        // one ulp away from flipping in either direction. Found by walking outward from the algebraic root
        // in Python and transcribed here; hex float literals so the exact bits survive decimal parsing.
        let high = ScoredEdge(length: 1000.0, score: 0.9)
        let onTheBound = ScoredEdge(length: 0x1.193fffcb923a6p+13, score: 0.1)   // 8999.999900000006 m
        #expect(RouteScore.lengthWeightedPercentile([onTheBound, high], fraction: 0.90) == 0.1,
                "the 90% boundary lands exactly on the tolerated bound, so it takes the LOWER score")

        // The far side, which is what holds the tolerance's SIZE down at this site. Eight ulps below the
        // band the boundary falls genuinely inside the high edge, so p90 is 0.9. Measured: it flips to 0.1
        // for any tolerance constant at or above 1.0000001666368189e-09, so this assertion refuses a use
        // site inlined at 1e-8, 1e-7, 1e-6, 1e-5 or 0.04 of route length - and the assertion above refuses
        // a tolerance made absolute in metres, which the doc comment on `boundaryTolerance` forbids in
        // words ("it means the same thing for a 2 km loop and a 300 km road trip") and nothing enforced.
        let justBelowTheBound = ScoredEdge(length: 0x1.193fffcb92399p+13, score: 0.1) // 8999.999899999983 m
        #expect(RouteScore.lengthWeightedPercentile([justBelowTheBound, high], fraction: 0.90) == 0.9,
                "eight ulps below the tolerated bound the boundary is inside the high edge")
    }
}
