import Foundation
import Testing
@testable import ScenicKit

/// The properties that matter here are invariances, not values.
///
/// A weighted sum of four terms will produce *a* number for any input; that number is only worth anything if
/// it describes the drive rather than describing how the router happened to segment and orient the path. The
/// plan pins two of these explicitly - *"RouteScore invariant under reversal (1e-9) and re-encoding (0.5%)"*
/// - and they are the tests that can actually fail for a real reason.
@Suite("Route score")
struct RouteScoreTests {

    /// A plausible scenic route: freeway shoulder, canyon middle, arterial run-in.
    static let realistic: [ScoredEdge] = [
        ScoredEdge(length: 8000, score: 0.0),      // motorway shoulder, scores 0 by construction
        ScoredEdge(length: 1200, score: 0.35),     // arterial approach
        ScoredEdge(length: 2400, score: 0.78),     // canyon
        ScoredEdge(length: 1800, score: 0.83),     // canyon continues, different way
        ScoredEdge(length: 900, score: 0.42),      // down into town
        ScoredEdge(length: 1500, score: 0.20),     // arterial
    ]

    static func split(_ edges: [ScoredEdge], into k: Int) -> [ScoredEdge] {
        edges.flatMap { e in
            (0..<k).map { _ in ScoredEdge(length: e.length / Double(k), score: e.score) }
        }
    }

    // MARK: - the invariances

    @Test("driving the route backwards does not change how pretty it is")
    func reversalInvariant() throws {
        let forward = try #require(RouteScore(edges: Self.realistic))
        let backward = try #require(RouteScore(edges: Self.realistic.reversed()))
        #expect(abs(forward.value - backward.value) < 1e-9)
        #expect(forward.episodeCount == backward.episodeCount)
        #expect(abs(forward.p90 - backward.p90) < 1e-9)
    }

    @Test("how the router split the path does not change how pretty it is", arguments: [2, 3, 5, 17])
    func reEncodingInvariant(k: Int) throws {
        // The router may return one OSM way as six path-detail intervals or six ways as one. Splitting every
        // edge into k equal pieces with the same score is exactly that, and the drive is identical.
        let whole = try #require(RouteScore(edges: Self.realistic))
        let pieces = try #require(RouteScore(edges: Self.split(Self.realistic, into: k)))
        #expect(abs(whole.value - pieces.value) < 1e-9)
        #expect(whole.episodeCount == pieces.episodeCount)
        #expect(abs(whole.mean - pieces.mean) < 1e-9)
        #expect(abs(whole.dudFraction - pieces.dudFraction) < 1e-9)
        #expect(abs(whole.totalLength - pieces.totalLength) < 1e-6)
    }

    // MARK: - length weighting, which is where a plausible implementation goes wrong

    @Test("ten metres of glory does not outvote ten kilometres of arterial")
    func percentileIsLengthWeighted() {
        // Two edges either way, so a percentile taken over the EDGE LIST returns 1.0 and calls this route
        // spectacular. Over metres it returns 0.1, which is what the drive is.
        let lopsided = [ScoredEdge(length: 10, score: 1.0),
                        ScoredEdge(length: 10_000, score: 0.1)]
        #expect(RouteScore.lengthWeightedPercentile(lopsided, fraction: 0.90) == 0.1)
    }

    @Test("the percentile counts up from the bottom, so p90 is the high end")
    func percentileSortsAscending() {
        // The fixture above returns 0.1 under BOTH sort directions, so it cannot see one character at
        // RouteScore.swift changing `<` to `>` - which turns p90 into p10 with the whole suite green and
        // moves the realistic route's p90 from 0.83 to 0.00. A reviewer found that. This fixture is
        // asymmetric on purpose: three equal thirds, so p90 and p10 name different scores.
        let thirds = [ScoredEdge(length: 1000, score: 0.1),
                      ScoredEdge(length: 1000, score: 0.5),
                      ScoredEdge(length: 1000, score: 0.9)]
        #expect(RouteScore.lengthWeightedPercentile(thirds, fraction: 0.90) == 0.9)
        #expect(RouteScore.lengthWeightedPercentile(thirds, fraction: 0.10) == 0.1)
        #expect(RouteScore.lengthWeightedPercentile(thirds, fraction: 0.50) == 0.5)
    }

    @Test("the percentile boundary landing exactly on an edge boundary is stable under re-splitting")
    func percentileIsStableOnTheBoundary() throws {
        // The bug this pins, found by a reviewer and real: `target` was derived from a `reduce` while the
        // running sum was accumulated separately, and floating-point addition is not associative. When the
        // boundary fell exactly on an edge boundary the two sums disagreed in their last bits and p90
        // jumped to the next distinct score.
        //
        // Here the boundary sits exactly at 9000 m of 10000, which is p90. Measured before the fix:
        // k = 1, 2, 4 gave p90 = 0.1 and value 0.031; k = 3, 7, 9, 12, 21, 22, 23, 26, ... gave p90 = 0.9
        // and value 0.231. A 0.2 swing on a 0...1 score from nothing but how the router segmented the path.
        //
        // `reEncodingInvariant` could not see it: its `realistic` fixture never puts the boundary on an
        // edge boundary, and its worst delta over the same range of k is 1e-15.
        let boundary = [ScoredEdge(length: 9000, score: 0.1),
                        ScoredEdge(length: 1000, score: 0.9)]
        let whole = try #require(RouteScore(edges: boundary))
        for k in 1...40 {
            let pieces = try #require(RouteScore(edges: Self.split(boundary, into: k)))
            #expect(abs(pieces.p90 - whole.p90) < 1e-9, "k=\(k): p90 \(pieces.p90) vs \(whole.p90)")
            #expect(abs(pieces.value - whole.value) < 1e-9, "k=\(k): value \(pieces.value)")
        }
    }

    @Test("the score uses the ninetieth percentile, and the number is pinned")
    func percentileFractionIsPinned() throws {
        // `matchesTheFormula` recomputes the expected value from `s.p90`, so it stays self-consistent under
        // any percentile definition - 0.90 -> 0.70 survives it, moving the realistic route's value from
        // 0.320 to 0.218. The fraction needs a witness outside the code that uses it.
        // Deliberately uneven. Three EQUAL thirds give the same answer for p70 and p90 - which was the
        // first version of this fixture, and it failed for that reason. Here 75% of the length scores 0.1,
        // so p70 lands on 0.1 and p90 on 0.9.
        let uneven = [ScoredEdge(length: 7500, score: 0.1),
                      ScoredEdge(length: 1000, score: 0.5),
                      ScoredEdge(length: 1500, score: 0.9)]
        let s = try #require(RouteScore(edges: uneven))
        #expect(s.p90 == RouteScore.lengthWeightedPercentile(uneven, fraction: 0.90))
        #expect(s.p90 == 0.9, "the top 15% of the length scores 0.9, so p90 is 0.9")
        #expect(RouteScore.lengthWeightedPercentile(uneven, fraction: 0.70) == 0.1)
        #expect(s.p90 != RouteScore.lengthWeightedPercentile(uneven, fraction: 0.70))
    }

    @Test("the thresholds are strict or non-strict exactly as documented")
    func thresholdStrictness() throws {
        // Every threshold's intended strictness was stated only in a doc comment, and CLAUDE.md forbids
        // anchoring a guard on a comment. No fixture used a score of exactly 0.6 or exactly 0.25, or a run
        // of exactly 800 m, so `>` versus `>=` was free to flip in any of three places.

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

    @Test("the constants are the plan's, and dudThreshold is ours")
    func constantsArePinned() {
        // The source claims dudThreshold is "named rather than inlined so that tuning it is a one-line
        // change with a test that moves". A reviewer pointed out that was false: nothing moved when it
        // changed. Now something does.
        #expect(RouteScore.meanWeight == 0.60)
        #expect(RouteScore.p90Weight == 0.25)
        #expect(RouteScore.dudPenalty == 0.15)
        #expect(RouteScore.episodeWeight == 0.10)
        #expect(RouteScore.episodeThreshold == 0.6)
        #expect(RouteScore.episodeMinLength == 800.0)
        #expect(RouteScore.episodeTarget == 3.0)
        #expect(RouteScore.dudThreshold == 0.25)
        #expect(RouteScore.honestFailureThreshold == 0.45)
    }

    @Test("the mean is over metres, not over edges")
    func meanIsLengthWeighted() throws {
        let lopsided = [ScoredEdge(length: 10, score: 1.0),
                        ScoredEdge(length: 990, score: 0.0)]
        let s = try #require(RouteScore(edges: lopsided))
        #expect(abs(s.mean - 0.01) < 1e-9)      // an edge-mean would say 0.5
    }

    @Test("an episode is counted across edge boundaries, not within one edge")
    func episodesSpanEdges() {
        // Five kilometres of one canyon road, returned by the router as twelve intervals because the OSM way
        // is split at every junction. Every interval is under the 800 m minimum on its own. Asking the
        // question per edge gives zero episodes for the prettiest road in the region.
        let canyon = (0..<12).map { _ in ScoredEdge(length: 420, score: 0.8) }
        #expect(RouteScore.episodes(canyon) == 1)

        // And a run must be broken by a genuinely dull stretch, not merely by an edge boundary.
        let broken = canyon.prefix(6) + [ScoredEdge(length: 3000, score: 0.1)] + canyon.suffix(6)
        #expect(RouteScore.episodes(Array(broken)) == 2)
    }

    @Test("scattered prettiness is not a scenic drive")
    func fragmentsAreNotEpisodes() {
        // Fifty 200 m gems separated by 300 m of arterial. Excellent mean, no episode: you never get to
        // enjoy any of it.
        let confetti = (0..<50).flatMap { _ in
            [ScoredEdge(length: 200, score: 0.9), ScoredEdge(length: 300, score: 0.3)]
        }
        #expect(RouteScore.episodes(confetti) == 0)
    }

    // MARK: - the terms

    @Test("motorway shoulders count as duds without disqualifying the route")
    func motorwayIsADud() throws {
        let s = try #require(RouteScore(edges: Self.realistic))
        // The 8 km motorway and the 1.5 km arterial are duds; 1.2 km at 0.35 and 0.9 km at 0.42 are not.
        let expected = (8000.0 + 1500.0) / 15_800.0
        #expect(abs(s.dudFraction - expected) < 1e-9)
        // CLAUDE.md: motorway is penalised, not excluded. The route still scores, and still has its episode.
        #expect(s.episodeCount == 1)
        #expect(s.value > 0)
    }

    @Test("the value is the plan's formula, computed by hand")
    func matchesTheFormula() throws {
        let s = try #require(RouteScore(edges: Self.realistic))
        let expected = 0.60 * s.mean + 0.25 * s.p90 - 0.15 * s.dudFraction
            + 0.10 * min(1.0, Double(s.episodeCount) / 3.0)
        #expect(abs(s.value - expected) < 1e-12)
    }

    @Test("a dull route is an honest failure, and says so")
    func honestFailure() throws {
        let dull = [ScoredEdge(length: 12_000, score: 0.05),
                    ScoredEdge(length: 3000, score: 0.15)]
        let s = try #require(RouteScore(edges: dull))
        #expect(s.isHonestFailure)
        #expect(s.episodeCount == 0)
    }

    @Test("a genuinely scenic route is not an honest failure")
    func goodRoutePasses() throws {
        let good = [ScoredEdge(length: 3000, score: 0.85),
                    ScoredEdge(length: 4000, score: 0.9),
                    ScoredEdge(length: 1000, score: 0.5)]
        let s = try #require(RouteScore(edges: good))
        #expect(!s.isHonestFailure)
        #expect(s.episodeCount == 1)
    }

    // MARK: - bounds and refusals

    @Test("the score stays inside 0...1 even when the dud penalty dominates")
    func staysInRange() throws {
        // Everything is a dud, so the negative term is at full strength and the positive ones are near zero.
        let allDud = [ScoredEdge(length: 20_000, score: 0.0)]
        let s = try #require(RouteScore(edges: allDud))
        #expect(s.value >= 0 && s.value <= 1)

        let allPerfect = (0..<10).map { _ in ScoredEdge(length: 2000, score: 1.0) }
        let best = try #require(RouteScore(edges: allPerfect))
        #expect(best.value >= 0 && best.value <= 1)
    }

    @Test("no route is not a dull route")
    func emptyIsNil() {
        // Returning 0 here would make "the router found nothing" indistinguishable from "the router found
        // a freeway", and those need different words on the screen.
        #expect(RouteScore(edges: []) == nil)
    }

    @Test("an invalid edge is refused rather than absorbed",
          arguments: [ScoredEdge(length: 0, score: 0.5),
                      ScoredEdge(length: -100, score: 0.5),
                      ScoredEdge(length: .nan, score: 0.5),
                      ScoredEdge(length: .infinity, score: 0.5),
                      ScoredEdge(length: 100, score: 1.5),
                      ScoredEdge(length: 100, score: -0.1),
                      ScoredEdge(length: 100, score: .nan)])
    func refusesInvalidEdges(bad: ScoredEdge) {
        #expect(RouteScore(edges: [bad]) == nil)
        #expect(RouteScore(edges: Self.realistic + [bad]) == nil)
    }
}
