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

    // `percentileIsStableOnTheBoundary` and `thresholdStrictness` live in RouteScoreBoundaryTests: they
    // are boundary tests, and this file is at its 300-line cap.

    @Test("the score uses the ninetieth percentile, and the number is pinned")
    func percentileFractionIsPinned() throws {
        // `matchesTheFormula` recomputes the expected value from `s.p90`, so it stays self-consistent under
        // any percentile definition - 0.90 -> 0.70 survives it, moving the realistic route's value from
        // 0.320 to 0.218. The fraction needs a witness outside the code that uses it.
        // Deliberately uneven. Three EQUAL thirds give the same answer for p70 and p90 - which was the
        // first version of this fixture, and it failed for that reason. Here 75% of the length scores 0.1,
        // so p70 lands on 0.1 and p90 on 0.9.
        //
        // The first version of THIS test then compared `s.p90` against
        // `lengthWeightedPercentile(uneven, fraction: 0.90)` - the same function, on the same fixture -
        // and `s.p90 != lengthWeightedPercentile(uneven, fraction: 0.70)`. Both are the implementation
        // compared with itself and neither pins a value. Every expectation below is a literal.
        // This fixture pins the fraction only to (0.85, 0.90]; `percentileFractionIsPinnedFromBothSides`
        // in RouteScoreBoundaryTests narrows it to (0.8999, 0.9001].
        let uneven = [ScoredEdge(length: 7500, score: 0.1),
                      ScoredEdge(length: 1000, score: 0.5),
                      ScoredEdge(length: 1500, score: 0.9)]
        let s = try #require(RouteScore(edges: uneven))
        #expect(s.p90 == 0.9, "the top 15% of the length scores 0.9, so p90 is 0.9")
        #expect(RouteScore.lengthWeightedPercentile(uneven, fraction: 0.70) == 0.1)
        #expect(RouteScore.lengthWeightedPercentile(uneven, fraction: 0.85) == 0.5,
                "85% of 10000 m is 8500 m, which is exactly where the 0.5 stretch ends")
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

    @Test("a motorway shoulder is penalised not excluded, and 8 km of it is an honest failure")
    func motorwayScoresAsADudAndIsAnHonestFailure() throws {
        let s = try #require(RouteScore(edges: Self.realistic))
        // CLAUDE.md: motorway is penalised, not excluded. What that means here, and all it means, is that
        // the 8 km at 0.0 goes into the dud fraction and the route still scores - it is not refused, it
        // keeps its episode, and it comes back with a number.
        // The 8 km motorway and the 1.5 km arterial are duds; 1.2 km at 0.35 and 0.9 km at 0.42 are not.
        #expect(abs(s.dudFraction - (8000.0 + 1500.0) / 15_800.0) < 1e-9)
        #expect(s.episodeCount == 1)
        #expect(s.value > 0)

        // The previous version stopped there, under the title "motorway shoulders count as duds WITHOUT
        // DISQUALIFYING THE ROUTE". A reviewer pointed out that the fixture does the opposite: at value
        // 0.320162 against honestFailureThreshold 0.45 the product reports this route as "not much pretty
        // within 25 minutes of this drive". The name asserted the opposite of what the fixture showed, and
        // nothing asserted the verdict at all. The verdict is now pinned rather than left as an untested
        // consequence of a tuning constant - if 0.45 is ever retuned on corpus evidence, this is the line
        // that has to move with it.
        #expect(s.isHonestFailure)
    }

    @Test("the value is the plan's formula on the realistic route, every term computed by hand")
    func matchesTheFormula() throws {
        let s = try #require(RouteScore(edges: Self.realistic))
        // Worked out by hand from the FIXTURE, not from `s`. The previous version built `expected` out of
        // s.mean, s.p90, s.dudFraction and s.episodeCount, so it asserted only that the four terms were
        // combined in the documented way and said nothing about the four terms themselves: a 0.90 -> 0.70
        // percentile left it green, and so did a p90 of 0.00.
        //
        //   total = 8000 + 1200 + 2400 + 1800 + 900 + 1500                        = 15800 m
        //   mean  = (1200*0.35 + 2400*0.78 + 1800*0.83 + 900*0.42 + 1500*0.20) / 15800
        //         = (420 + 1872 + 1494 + 378 + 300) / 15800 = 4464/15800          = 0.2825316...
        //   p90   = 0.90 * 15800 = 14220 m. Ascending, the cumulative lengths are 8000, 9500, 10700,
        //           11600, 14000, 15800, so 14220 m first falls inside the 1800 m at 0.83 = 0.83
        //   dud   = (8000 at 0.00 + 1500 at 0.20) / 15800 = 9500/15800            = 0.6012658...
        //   episodes = 1 (2400 + 1800 = 4200 m contiguous above 0.6)
        //   value = 0.60*0.2825316... + 0.25*0.83 - 0.15*0.6012658... + 0.10*(1/3)
        //         = 0.1695189... + 0.2075 - 0.0901898... + 0.0333333...           = 0.320162447257384
        #expect(abs(s.totalLength - 15_800) < 1e-9)
        #expect(abs(s.mean - 4464.0 / 15_800.0) < 1e-12)
        #expect(s.p90 == 0.83)
        #expect(abs(s.dudFraction - 9500.0 / 15_800.0) < 1e-12)
        #expect(s.episodeCount == 1)
        #expect(abs(s.value - 0.320162447257384) < 1e-12)
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
