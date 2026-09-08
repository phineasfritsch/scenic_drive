import Foundation

/// How pretty a whole route is, from the scenic scores of the stretches it is made of.
///
///     0.60 * mean + 0.25 * p90 - 0.15 * dudFraction + 0.10 * min(1, episodes / 3)
///
/// The four terms answer four different questions, and dropping any of them lets a bad route score well:
///
///   * **mean** - is it pretty on average? Alone, it rewards a route that is uniformly mediocre.
///   * **p90** - is any of it really good? A drive needs a high point; a flat 0.5 the whole way is a commute.
///   * **dudFraction** - how much of it is actively dull? This is the only negative term, and it is what
///     stops a route buying a good mean with one spectacular canyon bolted onto twenty minutes of arterial.
///   * **episodes** - is the pretty part *sustained*? Prettiness scattered over fifty 200 m fragments is not
///     a scenic drive, it is a scenic drive's worth of scenery arranged so you never get to enjoy any of it.
///
/// ## Everything here is weighted by LENGTH, and that is the whole difficulty
///
/// The router is free to split one OSM way into six path-detail intervals, or merge six into one, and to
/// return the route in either direction. None of that changes the drive. So none of it may change the score:
/// a per-edge mean would let a router that splits a dull edge in half double that edge's vote. Every
/// statistic below is computed over metres, never over edges, and the test suite asserts invariance under
/// both reversal and arbitrary re-splitting.
public struct RouteScore: Equatable, Sendable {
    // The plan's weights.
    public static let meanWeight = 0.60
    public static let p90Weight = 0.25
    public static let dudPenalty = 0.15
    public static let episodeWeight = 0.10

    /// A stretch scoring above this, sustained for `episodeMinLength`, is an episode.
    public static let episodeThreshold = 0.6

    /// Metres. Below this it is a nice corner, not a stretch of road you remember.
    public static let episodeMinLength = 800.0

    /// Episodes beyond this buy nothing more.
    public static let episodeTarget = 3.0

    /// How close to a boundary still counts as being ON it, as a fraction of the route's own length.
    ///
    /// Two statistics here compare an ACCUMULATED length against a boundary: the percentile's running sum
    /// against `total * fraction`, and an episode's run against `episodeMinLength`. Both accumulations
    /// depend on how many pieces the router split the route into, and floating-point addition is not
    /// associative, so a boundary landing exactly on an edge boundary is decided by the last bits of a sum
    /// rather than by the road. At such a boundary the answer is genuinely ambiguous, so the tie is broken
    /// deterministically - toward the lower score, and toward keeping the episode - rather than left to the
    /// noise. Both uses have a fixture that fails without it.
    ///
    /// Relative to the route's own length, so it means the same thing for a 2 km loop and a 300 km road
    /// trip. 1e-9 sits between the two magnitudes that matter: accumulation error is about 1e-13 of the
    /// route even when it is split into thousands of pieces, and the smallest real distinction any fixture
    /// here draws is 1 m in 10 km, which is 1e-4. Named rather than inlined because a reviewer floated the
    /// inlined version to 4% of route length - 12 km on a long trip - with the whole suite green.
    public static let boundaryTolerance = 1e-9

    /// At or below this, a stretch is a dud.
    ///
    /// **The plan does not specify this number.** It names the `dud_frac` term and its weight and leaves the
    /// threshold open. 0.25 is chosen here to mean "actively dull rather than merely unremarkable" - it puts
    /// motorway and trunk (which score 0 by construction) and bare arterial into the dud bucket while
    /// leaving ordinary residential and unclassified roads out of it. It is a tuning constant, it is named
    /// rather than inlined so that tuning it is a one-line change with a test that moves, and it must not be
    /// mistaken for a value the plan handed down.
    public static let dudThreshold = 0.25

    public let value: Double
    public let mean: Double
    public let p90: Double
    public let dudFraction: Double
    public let episodeCount: Int
    public let totalLength: Double

    /// Below this the route has no scenic middle worth showing, and the product says so out loud rather than
    /// presenting a dull route as an answer. From the plan: *"not much pretty within 25 minutes of this
    /// drive"*.
    ///
    /// **The plan does not specify this number**, any more than it specifies `dudThreshold`. It names the
    /// behaviour and leaves the threshold open, so 0.45 is chosen here - and what it actually rejects is
    /// worth writing down rather than discovering in the field. The formula's ceiling is 0.95
    /// (0.60 + 0.25 + 0.10, with the dud term at zero), so 0.45 is not "half of a good route"; it is
    /// roughly "mean around 0.5, with a high point".
    ///
    /// The suite's `realistic` fixture - 8 km of motorway shoulder, 4.2 km of 0.78-0.83 canyon, arterial
    /// either side - scores 0.320162 and IS an honest failure at 0.45. A reviewer flagged that as a
    /// surprise, and it is: 51% motorway by length is the shape a lot of drives over 15 km have to take.
    /// It is not motorway being excluded - the route still scores, still keeps its episode and is still
    /// returned, which is the CLAUDE.md invariant - but whether the product should show that route or
    /// refuse it is a tuning question that needs the router and a real corpus. It is not settled by
    /// inventing a number here that makes a fixture read well, so the number stays and the consequence is
    /// pinned instead: `motorwayScoresAsADudAndIsAnHonestFailure` is the assertion that must move if 0.45
    /// ever does.
    public static let honestFailureThreshold = 0.45

    public var isHonestFailure: Bool { value < Self.honestFailureThreshold }

    /// Score a route. Returns nil for an empty route or one containing an invalid edge - there is no
    /// meaningful score for "no road", and inventing 0 would make a missing route look like a dull one.
    public init?(edges: [ScoredEdge]) {
        guard !edges.isEmpty, edges.allSatisfy(\.isValid) else { return nil }
        let total = edges.reduce(0.0) { $0 + $1.length }
        guard total > 0, total.isFinite else { return nil }

        let mean = edges.reduce(0.0) { $0 + $1.score * $1.length } / total
        let p90 = Self.lengthWeightedPercentile(edges, fraction: 0.90)
        let dud = edges.filter { $0.score <= Self.dudThreshold }
                       .reduce(0.0) { $0 + $1.length } / total
        let episodes = Self.episodes(edges)

        let raw = Self.meanWeight * mean
            + Self.p90Weight * p90
            - Self.dudPenalty * dud
            + Self.episodeWeight * min(1.0, Double(episodes) / Self.episodeTarget)

        // The dud term is negative, so the expression is not bounded below by 0 on its own. Clamped rather
        // than left to go negative: callers compare against thresholds and a negative score would order
        // correctly but read as a bug in every log line it appears in.
        self.value = min(1.0, max(0.0, raw))
        self.mean = mean
        self.p90 = p90
        self.dudFraction = dud
        self.episodeCount = episodes
        self.totalLength = total
    }

    /// The score at which `fraction` of the route's LENGTH is at or below it.
    ///
    /// Not `sorted()[Int(0.9 * count)]`. That is the percentile of the edge list, which answers a question
    /// about how the router chose to segment the path rather than about the drive. Ten metres of glorious
    /// coast road and ten kilometres of arterial are two edges either way; only the length-weighted form
    /// says the route is mostly arterial.
    static func lengthWeightedPercentile(_ edges: [ScoredEdge], fraction: Double) -> Double {
        // ASCENDING. `fraction` of the length lies at or below the returned score, so 0.90 is the high end.
        // Sorting the other way turns p90 into p10 silently, and on a real route that moves the score by
        // more than any weight change would.
        let sorted = edges.sorted { $0.score < $1.score }

        // The bug this guards, and the mechanism - CORRECTED, because the first fix got the mechanism
        // wrong and a later reviewer's measurements said so.
        //
        // A reviewer demonstrated a p90 that depended on how the router segmented the path, on
        // [9000 m @ 0.1, 1000 m @ 0.9] - the boundary sits exactly at 9000 m, which is p90 - split into k
        // equal pieces per interval, exactly what the router does at junctions. k = 1, 2, 4 gave p90 = 0.1
        // and a route score of 0.031; k = 3, 7, 9, 12, 21 and 176 others up to k = 400 gave p90 = 0.9 and
        // 0.231. A 0.2 swing on a 0...1 score from nothing but segmentation, which is precisely the
        // invariance this type exists to provide.
        //
        // The first fix blamed `total` having come from a separate `sorted.reduce` while the running sum
        // was accumulated by the loop, "and floating-point addition is not associative". That explanation
        // is FALSE: `reduce` is a left fold over the same sequence in the same order, so the two totals are
        // bit-identical for every input - measured over the fixture at k = 1...400, worst difference
        // exactly 0.0. Reverting that half alone changes nothing at all, and a third reviewer measured
        // exactly that.
        //
        // The real cause is comparing an ACCUMULATED sum against `total * fraction`, a product whose
        // rounding does not track the accumulation's. The tolerance below is the whole fix: with it, 0 of
        // 400 splits flip, with or without the separate reduce. Accumulating once is kept because it is
        // the better shape, not because it is load-bearing.
        var running: [Double] = []
        running.reserveCapacity(sorted.count)
        var cumulative = 0.0
        for e in sorted {
            cumulative += e.length
            running.append(cumulative)
        }
        let total = cumulative
        guard total > 0 else { return sorted.last?.score ?? 0 }

        // At a boundary the correct answer is genuinely ambiguous - both adjacent scores are defensible -
        // so the tie is broken deterministically toward the lower score rather than left to the noise.
        let target = total * fraction
        let tolerance = total * Self.boundaryTolerance
        for (i, c) in running.enumerated() where c >= target - tolerance {
            return sorted[i].score
        }
        return sorted.last?.score ?? 0
    }

    /// Count the maximal runs of consecutive above-threshold stretches that are long enough to enjoy.
    ///
    /// Runs are accumulated ACROSS edge boundaries. Asking "is this edge above threshold and over 800 m"
    /// per edge would count zero episodes on a five-kilometre canyon road the router happened to return as
    /// twelve intervals, which is the normal case and not an exotic one.
    ///
    /// And because the run is ACCUMULATED, comparing it against `episodeMinLength` is the same boundary
    /// problem as the percentile's, in the same file, needing the same cure - which the first two versions
    /// of this file missed while fixing the percentile, and a third reviewer found. 800 m returned as
    /// twelve 66.67 m intervals does not sum to 800 m, and a bare `>=` then throws the episode away: on
    /// `[800 m @ 0.9]` a bare comparison lost the episode for 99 of the first 200 equal splits, and on
    /// `[800 m @ 0.9, 2000 m @ 0.1]` that moves the route's score from 0.348333 to 0.315000 - 9.6% - against
    /// a suite tolerance of 1e-9 and the plan's 0.5% re-encoding pin. The Brief's own junction case
    /// reproduces it: a canyon returned as 400 m + 400 m loses its episode at k = 6, 7, 13, 14, 15, 17, 18,
    /// 21, 22, 24, 26, 27, 29, 31, 34, 36, 38.
    static func episodes(_ edges: [ScoredEdge]) -> Int {
        // Same scale as the percentile's: the route's own length. That is at most a millimetre on a
        // 1000 km trip, six orders of magnitude below the 1 m margin `thresholdStrictness` pins at 799 m,
        // so it cannot promote a run that is genuinely short into an episode.
        var scale = 0.0
        for e in edges { scale += e.length }
        let tolerance = scale * Self.boundaryTolerance

        var count = 0
        var run = 0.0
        for e in edges {
            if e.score > episodeThreshold {
                run += e.length
            } else {
                if run >= episodeMinLength - tolerance { count += 1 }
                run = 0
            }
        }
        if run >= episodeMinLength - tolerance { count += 1 }
        return count
    }
}
