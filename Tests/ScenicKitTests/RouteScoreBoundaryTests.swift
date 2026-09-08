import Foundation
import Testing
@testable import ScenicKit

/// The boundaries, which is where every defect this type has shipped has actually lived.
///
/// Three reviews of `RouteScore` found three bugs and all three were the same bug: a quantity that the
/// router's segmentation perturbs in its last bits, compared against a threshold with a bare `>=`. The
/// percentile's running sum against `total * fraction`; an episode's accumulated run against
/// `episodeMinLength`; and, next door to both, thresholds and fractions that no fixture pinned closely
/// enough for a plausible wrong value to fail.
///
/// A separate suite from `RouteScoreTests` because the file cap is 300 lines and because these tests share
/// one shape: a fixture placed exactly ON a boundary, an expectation written out as a literal, and - where
/// the router's segmentation is the variable - a sweep over k equal splits.
@Suite("Route score boundaries")
struct RouteScoreBoundaryTests {

    /// n runs of 1000 m at 0.9, separated by 1000 m at 0.1. Each run is an episode: 1000 m clears the
    /// 800 m minimum, and 0.9 clears the 0.6 threshold while 0.1 does not.
    static func alternating(_ n: Int) -> [ScoredEdge] {
        var edges: [ScoredEdge] = []
        for i in 0..<n {
            if i > 0 { edges.append(ScoredEdge(length: 1000, score: 0.1)) }
            edges.append(ScoredEdge(length: 1000, score: 0.9))
        }
        return edges
    }

    // MARK: - the percentile boundary (moved here from RouteScoreTests, which is at its 300-line cap)

    @Test("the percentile boundary landing exactly on an edge boundary is stable under re-splitting")
    func percentileIsStableOnTheBoundary() throws {
        // The bug this pins, found by a reviewer and real: p90 moved with how the router segmented the
        // path. The first fix's account of WHY was wrong, and this comment used to repeat it - it said
        // `target` came from a `reduce` while the running sum was accumulated separately, and that the two
        // sums differed in their last bits. They do not: `reduce` is a left fold over the same sequence in
        // the same order, and over this fixture at k = 1...400 the two totals differ by exactly 0.0. The
        // cause is comparing an accumulated sum against `total * fraction`, whose rounding does not track
        // the accumulation's; the tolerance is the whole fix. See RouteScore.boundaryTolerance.
        //
        // Here the boundary sits exactly at 9000 m of 10000, which is p90. Measured before the fix:
        // k = 1, 2, 4 gave p90 = 0.1 and value 0.031; k = 3, 7, 9, 12, 21, 22, 23, 26, ... gave p90 = 0.9
        // and value 0.231. A 0.2 swing on a 0...1 score from nothing but how the router segmented the path.
        //
        // `reEncodingInvariant` could not see it: its `realistic` fixture never puts the boundary on an
        // edge boundary, and its worst delta over the same range of k is 1e-15.
        // The expected values are LITERALS, worked out by hand. The first version compared every split
        // against `whole.p90` and `whole.value` - both taken from the function under test on the same
        // fixture - so it asserted the percentile was CONSISTENT and never that it was RIGHT. A second
        // reviewer flipped one character (`target - tolerance` to `target + tolerance`) and restored the
        // exact 0.200 swing the first reviewer had blocked on, with this test still green.
        //
        // 90% of 10000 m is 9000 m, and the first 9000 m of length scores 0.1, so p90 is 0.1 - the boundary
        // is inclusive. The route score then follows from the four terms:
        //   mean = (9000*0.1 + 1000*0.9)/10000 = 0.18
        //   p90  = 0.1
        //   dud  = 9000/10000 = 0.9   (0.1 is at or below dudThreshold 0.25)
        //   episodes = 1             (1000 m at 0.9 exceeds 0.6, and 1000 >= 800)
        //   0.60*0.18 + 0.25*0.1 - 0.15*0.9 + 0.10*(1/3) = 0.108 + 0.025 - 0.135 + 0.033333 = 0.031333
        let boundary = [ScoredEdge(length: 9000, score: 0.1),
                        ScoredEdge(length: 1000, score: 0.9)]
        let expectedP90 = 0.1
        let expectedValue = 0.60 * 0.18 + 0.25 * 0.1 - 0.15 * 0.9 + 0.10 * (1.0 / 3.0)

        let whole = try #require(RouteScore(edges: boundary))
        #expect(abs(whole.p90 - expectedP90) < 1e-12)
        #expect(abs(whole.value - expectedValue) < 1e-12)

        for k in 1...40 {
            let pieces = try #require(RouteScore(edges: RouteScoreTests.split(boundary, into: k)))
            #expect(abs(pieces.p90 - expectedP90) < 1e-9, "k=\(k): p90 \(pieces.p90)")
            #expect(abs(pieces.value - expectedValue) < 1e-9, "k=\(k): value \(pieces.value)")
        }
    }

    // MARK: - strictness of every threshold in the file

    @Test("the thresholds are strict or non-strict exactly as documented")
    func thresholdStrictness() throws {
        // Every threshold's intended strictness was stated only in a doc comment, and CLAUDE.md forbids
        // anchoring a guard on a comment. No fixture used a score of exactly 0.6 or exactly 0.25, or a run
        // of exactly 800 m, so `>` versus `>=` was free to flip in any of three places. The fourth is
        // `isHonestFailure`, pinned by `honestFailureIsStrictAtItsThreshold` below.

        // An episode needs to EXCEED 0.6; exactly 0.6 is not an episode.
        #expect(RouteScore.episodes([ScoredEdge(length: 5000, score: RouteScore.episodeThreshold)]) == 0)
        #expect(RouteScore.episodes([ScoredEdge(length: 5000,
                                                score: RouteScore.episodeThreshold + 0.001)]) == 1)

        // A run of exactly the minimum length counts. Both places it can be closed need a fixture: a run
        // that ENDS THE ROUTE is closed by the final check after the loop, and a run closed by a dull
        // stretch mid-route is closed inside it. Testing only the first leaves the second free to flip -
        // the mutation harness found exactly that, because the single-edge fixture below never reaches the
        // in-loop branch.
        #expect(RouteScore.episodes([ScoredEdge(length: RouteScore.episodeMinLength, score: 0.9)]) == 1)
        #expect(RouteScore.episodes([ScoredEdge(length: RouteScore.episodeMinLength - 1, score: 0.9)]) == 0)
        #expect(RouteScore.episodes([ScoredEdge(length: RouteScore.episodeMinLength, score: 0.9),
                                     ScoredEdge(length: 2000, score: 0.1)]) == 1,
                "a run of exactly the minimum, closed by a dull stretch, is still an episode")
        #expect(RouteScore.episodes([ScoredEdge(length: RouteScore.episodeMinLength - 1, score: 0.9),
                                     ScoredEdge(length: 2000, score: 0.1)]) == 0)

        // A score of exactly the dud threshold IS a dud.
        let atThreshold = try #require(RouteScore(edges: [
            ScoredEdge(length: 1000, score: RouteScore.dudThreshold),
            ScoredEdge(length: 1000, score: RouteScore.dudThreshold + 0.001),
        ]))
        #expect(abs(atThreshold.dudFraction - 0.5) < 1e-9)
    }

    // MARK: - the episode minimum, which is an ACCUMULATED length

    @Test("an episode of exactly the minimum length survives being re-split")
    func episodeOfExactlyTheMinimumSurvivesResplitting() throws {
        // The same defect class as the percentile boundary, in the same file, and it survived the two
        // reviews that fixed the percentile. `run` is accumulated across edges and then compared with a
        // bare `>=` against episodeMinLength, so 800 m returned by the router as k equal intervals does
        // not sum to 800 m and the episode is thrown away.
        //
        // Measured against the shipped code before this fix, over k = 1...40:
        //   [800 m @ 0.9]                    lost its episode at k = 12, 14, 17, 21, 23, 26, 28, 30, 31,
        //                                    34, 36  (99 of the first 200 k)
        //   [400 m @ 0.9, 400 m @ 0.9]       - the Brief's junction case, a canyon the router returns as
        //                                    two ways - lost it at k = 6, 7, 13, 14, 15, 17, 18, 21, 22,
        //                                    24, 26, 27, 29, 31, 34, 36, 38
        //   [800 m @ 0.9, 1200 m @ 0.1]      lost it at the same k as the first
        //
        // Both places a run can be closed need their own fixture, exactly as `thresholdStrictness` needs
        // two: a run that ENDS THE ROUTE is closed by the check after the loop, and a run closed by a dull
        // stretch is closed inside it. `endsTheRoute` and `junction` exercise the first, and
        // `closedByADullStretch` the second.
        let endsTheRoute = [ScoredEdge(length: 800, score: 0.9)]
        let junction = [ScoredEdge(length: 400, score: 0.9),
                        ScoredEdge(length: 400, score: 0.9)]
        let closedByADullStretch = [ScoredEdge(length: 800, score: 0.9),
                                    ScoredEdge(length: 1200, score: 0.1)]

        for k in 1...40 {
            #expect(RouteScore.episodes(RouteScoreTests.split(endsTheRoute, into: k)) == 1,
                    "k=\(k): 800 m in \(k) pieces is still 800 m of road")
            #expect(RouteScore.episodes(RouteScoreTests.split(junction, into: k)) == 1,
                    "k=\(k): the canyon is one episode however the router cut it")
            #expect(RouteScore.episodes(RouteScoreTests.split(closedByADullStretch, into: k)) == 1,
                    "k=\(k): closed by a dull stretch rather than by the end of the route")
        }

        // And the whole score with it. Worked out by hand for `closedByADullStretch`:
        //   total = 800 + 1200                                                     = 2000 m
        //   mean  = (800*0.9 + 1200*0.1)/2000 = (720 + 120)/2000 = 840/2000        = 0.42
        //   p90   = 0.90 * 2000 = 1800 m; ascending that is 1200 m of 0.1 then 800 m of 0.9, so 1800 m
        //           falls inside the 0.9 stretch                                   = 0.9
        //   dud   = 1200/2000  (0.1 is at or below dudThreshold 0.25)              = 0.6
        //   episodes = 1
        //   0.60*0.42 + 0.25*0.9 - 0.15*0.6 + 0.10*(1/3)
        //     = 0.252 + 0.225 - 0.09 + 0.0333333...                                = 0.4203333...
        // Losing the episode drops the last term and gives 0.387: a 9.6% relative move on a statistic the
        // plan pins at 0.5% and this suite pins at 1e-9.
        let expected = 0.60 * 0.42 + 0.25 * 0.9 - 0.15 * 0.6 + 0.10 * (1.0 / 3.0)
        for k in 1...40 {
            let s = try #require(RouteScore(edges: RouteScoreTests.split(closedByADullStretch, into: k)))
            #expect(s.episodeCount == 1, "k=\(k)")
            #expect(abs(s.value - expected) < 1e-9, "k=\(k): value \(s.value), expected \(expected)")
        }
    }

    // MARK: - the episode cap, which no fixture reached

    @Test("episodes beyond the target buy nothing more")
    func episodeTermSaturatesAtTheTarget() throws {
        // `min(1.0, Double(episodes) / episodeTarget)` was untested through two reviews: dropping the
        // `min` left the whole suite green because no fixture had more than two episodes. Both fixtures
        // below are hand-worked, and the second is the one that bites.
        //
        // Three episodes - the term is exactly at its maximum, so the cap changes nothing here:
        //   total = 3 runs of 1000 m + 2 gaps of 1000 m                            = 5000 m
        //   mean  = (3*1000*0.9 + 2*1000*0.1)/5000 = (2700 + 200)/5000 = 2900/5000 = 0.58
        //   p90   = 0.90 * 5000 = 4500 m; ascending, 2000 m of 0.1 then 3000 m of 0.9 = 0.9
        //   dud   = 2000/5000                                                      = 0.4
        //   0.60*0.58 + 0.25*0.9 - 0.15*0.4 + 0.10*min(1, 3/3)
        //     = 0.348 + 0.225 - 0.06 + 0.10                                        = 0.613
        let three = try #require(RouteScore(edges: Self.alternating(3)))
        #expect(three.episodeCount == 3)
        #expect(abs(three.value - 0.613) < 1e-12)

        // Eight episodes - here the cap is the only thing standing between the term and 0.2666...:
        //   total = 8 runs of 1000 m + 7 gaps of 1000 m                            = 15000 m
        //   mean  = (8*1000*0.9 + 7*1000*0.1)/15000 = (7200 + 700)/15000 = 7900/15000
        //   p90   = 0.90 * 15000 = 13500 m; ascending, 7000 m of 0.1 then 8000 m of 0.9 = 0.9
        //   dud   = 7000/15000
        //   0.60*(7900/15000) + 0.25*0.9 - 0.15*(7000/15000) + 0.10*min(1, 8/3)
        //     = 0.316 + 0.225 - 0.07 + 0.10                                        = 0.571
        // Without the cap the last term is 0.10 * 8/3 = 0.2666... and the value is 0.7376666...: a route
        // of eight one-kilometre gems separated by eight kilometres of arterial would outscore the
        // three-episode route below, and outscore the realistic canyon drive more than twice over.
        let eight = try #require(RouteScore(edges: Self.alternating(8)))
        #expect(eight.episodeCount == 8)
        #expect(abs(eight.value - 0.571) < 1e-12)

        // Both values above are literals, so this ordering is a consequence rather than the assertion.
        #expect(eight.value < three.value, "a fourth episode does not buy more than the third")
    }

    // MARK: - the fourth threshold: whether the product shows the route at all

    @Test("isHonestFailure is strict: a route landing exactly on the threshold is still shown")
    func honestFailureIsStrictAtItsThreshold() throws {
        // `thresholdStrictness` covers the episode threshold, the episode minimum length and the dud
        // threshold - three of the four threshold comparisons in the file. The fourth decides whether the
        // product shows the route or says "not much pretty within 25 minutes of this drive", and
        // `<` -> `<=` survived the whole suite because no fixture put a value exactly on 0.45.
        //
        // This one does, and the arithmetic is exact in binary floating point rather than approximately so.
        // Two 1024 m edges at 0.51 and 0.54: neither is a dud (both above dudThreshold 0.25) and neither
        // is an episode (both at or below episodeThreshold 0.6), so two of the four terms vanish.
        //   mean = (1024*0.51 + 1024*0.54)/2048 = (0.51 + 0.54)/2                  = 0.525
        //   p90  = 0.90 * 2048 = 1843.2 m, which is inside the second edge         = 0.54
        //   0.60*0.525 + 0.25*0.54 = 0.315 + 0.135                                 = 0.45
        let exactlyOnIt = [ScoredEdge(length: 1024, score: 0.51),
                           ScoredEdge(length: 1024, score: 0.54)]
        let onIt = try #require(RouteScore(edges: exactlyOnIt))
        #expect(onIt.value == 0.45, "the fixture has to land ON the threshold or the next line is vacuous")
        #expect(onIt.value == RouteScore.honestFailureThreshold)
        #expect(!onIt.isHonestFailure, "at exactly the threshold the route is shown: the comparison is `<`")

        // A witness on each side, so the property is not pinned only at the one point.
        //   below: mean = 0.52, p90 = 0.53 -> 0.60*0.52 + 0.25*0.53 = 0.312 + 0.1325 = 0.4445
        //   above: mean = 0.53, p90 = 0.55 -> 0.60*0.53 + 0.25*0.55 = 0.318 + 0.1375 = 0.4555
        let below = try #require(RouteScore(edges: [ScoredEdge(length: 1024, score: 0.51),
                                                    ScoredEdge(length: 1024, score: 0.53)]))
        #expect(abs(below.value - 0.4445) < 1e-12)
        #expect(below.isHonestFailure)

        let above = try #require(RouteScore(edges: [ScoredEdge(length: 1024, score: 0.51),
                                                    ScoredEdge(length: 1024, score: 0.55)]))
        #expect(abs(above.value - 0.4555) < 1e-12)
        #expect(!above.isHonestFailure)
    }

    // MARK: - which percentile, and how wide its tolerance is allowed to be

    @Test("the ninetieth percentile is pinned from both sides, not merely to somewhere above 0.85")
    func percentileFractionIsPinnedFromBothSides() throws {
        // `percentileFractionIsPinned` puts its boundary at 75% of the length, which pins the fraction
        // only to (0.85, 0.90]: a reviewer showed that 0.86, 0.89 and 0.90 are indistinguishable to the
        // entire suite. These two fixtures put the boundary 1 m either side of 90% of a 10 km route, which
        // pins it to (0.8999, 0.9001].
        //
        // Below: 8999 m of the 10000 scores 0.1, so 90% of the length reaches 1 m past that stretch and
        // p90 is 0.9. Any fraction at or below 0.8999 answers 0.1 instead.
        let boundaryJustBelow = [ScoredEdge(length: 8999, score: 0.1),
                                 ScoredEdge(length: 1001, score: 0.9)]
        let low = try #require(RouteScore(edges: boundaryJustBelow))
        #expect(low.p90 == 0.9)

        // Above: 9001 m scores 0.1, so 90% of the length is still inside it and p90 is 0.1. Any fraction
        // above 0.9001 answers 0.9 instead.
        let boundaryJustAbove = [ScoredEdge(length: 9001, score: 0.1),
                                 ScoredEdge(length: 999, score: 0.9)]
        let high = try #require(RouteScore(edges: boundaryJustAbove))
        #expect(high.p90 == 0.1)
    }

    @Test("the boundary tolerance stays far below any distance a route could really have")
    func boundaryToleranceIsFarBelowAnyRealEdge() throws {
        // `total * 1e-9` was an unnamed inlined literal and a reviewer floated it to `total * 0.04`
        // undetected: 4% of route length, which is 12 km of road on a 300 km trip deciding a boundary the
        // tolerance exists to resolve to the millimetre. The tolerance absorbs accumulation noise - about
        // 1e-13 of the route even when it is split into thousands of pieces - and nothing else.
        #expect(RouteScore.boundaryTolerance == 1e-9)

        // 1 m in 10 km is 1e-4 of the route: a real distinction, and the smallest one any fixture here
        // draws. The tolerance has to stay under it. At 1e-4 or wider this answers 0.1.
        let oneMetreShortOfTheBoundary = [ScoredEdge(length: 8999, score: 0.1),
                                          ScoredEdge(length: 1001, score: 0.9)]
        #expect(RouteScore.lengthWeightedPercentile(oneMetreShortOfTheBoundary, fraction: 0.90) == 0.9)

        // And it cannot quietly go to zero either: a boundary landing exactly on an edge boundary is
        // INCLUSIVE, which is what `percentileIsStableOnTheBoundary` pins over k equal splits.
        let exactlyOnTheBoundary = [ScoredEdge(length: 9000, score: 0.1),
                                    ScoredEdge(length: 1000, score: 0.9)]
        #expect(RouteScore.lengthWeightedPercentile(exactlyOnTheBoundary, fraction: 0.90) == 0.1)

        // The episode minimum uses the same constant on the same scale, and `thresholdStrictness` pins its
        // upper limit: a 799 m run is not an episode, so the tolerance can never reach 1 m.
        #expect(RouteScore.episodes([ScoredEdge(length: 799, score: 0.9)]) == 0)
        #expect(RouteScore.episodes([ScoredEdge(length: 800, score: 0.9)]) == 1)
    }
}
