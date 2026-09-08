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

        // The total is accumulated in exactly the same order and by exactly the same additions as the
        // running sum below. The first version took it with a separate `reduce`, and floating-point
        // addition is not associative: the two sums differed in their last bits, so when the percentile
        // boundary fell on an edge boundary the comparison went whichever way the noise pointed.
        //
        // A reviewer demonstrated it on [9000 m @ 0.1, 1000 m @ 0.9] - the boundary sits exactly at 9000 m,
        // which is p90 - split into k equal pieces per interval, exactly what the router does at junctions.
        // k = 1, 2, 4 gave p90 = 0.1 and a route score of 0.031; k = 3, 7, 9, 12, 21 and many more gave
        // p90 = 0.9 and 0.231. A 0.2 swing on a 0...1 score, from nothing but how the path was segmented -
        // which is precisely the invariance this type exists to provide.
        var running: [Double] = []
        running.reserveCapacity(sorted.count)
        var cumulative = 0.0
        for e in sorted {
            cumulative += e.length
            running.append(cumulative)
        }
        let total = cumulative
        guard total > 0 else { return sorted.last?.score ?? 0 }

        // Even with one accumulation, splitting an edge changes the number of additions and so the last
        // bits. At a boundary the correct answer is genuinely ambiguous - both adjacent scores are defensible
        // - so the tie is broken deterministically toward the lower score rather than left to the noise.
        // The tolerance is relative to the route's own length, so it means the same thing for a 2 km loop
        // and a 300 km road trip.
        let target = total * fraction
        let tolerance = total * 1e-9
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
    static func episodes(_ edges: [ScoredEdge]) -> Int {
        var count = 0
        var run = 0.0
        for e in edges {
            if e.score > episodeThreshold {
                run += e.length
            } else {
                if run >= episodeMinLength { count += 1 }
                run = 0
            }
        }
        if run >= episodeMinLength { count += 1 }
        return count
    }
}
