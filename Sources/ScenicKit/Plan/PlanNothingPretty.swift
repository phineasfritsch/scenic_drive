import Foundation

/// The plan's honest failure (Problem A step 3, T-0230): the route the search chose is inside the ceiling and is
/// not the fastest route, but it is not pretty - `RouteScore.isHonestFailure`, or no scored road at all - so the
/// planner refuses it rather than issuing a dull drive as a scenic one, and says what more could buy.
///
/// It is NOT `PlanFailure.notActuallyDifferent`. That one says the search found no other road; this one says the
/// road it found is dull. A score-8 canyon that is also the fastest road is the first and never the second.
public struct PlanNothingPretty: Equatable, Sendable {

    /// The second offer: the drive on the most scenic weighting the search knows, at the duration the router
    /// measured for it. It may be longer than `fastest + budget` - it is an offer, nothing is planned with it.
    public enum BackRoads: Equatable, Sendable {
        /// Measured, and pretty itself: worth offering.
        case offered(duration: TimeInterval, routeScore: Double)
        /// Measured, and under the floor too (or carrying no scored road, `routeScore` nil): offering it would
        /// repeat the dishonesty this refusal exists to prevent.
        case dull(duration: TimeInterval, routeScore: Double?)
        /// The one request for it was refused or has no recording; the reason, never an invented ETA.
        case unmeasured(String)
    }

    /// The first offer, in seconds of EXTRA time on top of the budget asked for: the plan's "+40".
    public static let moreTimeOffer: TimeInterval = 40 * 60

    /// The lambda of the "all back roads" variant: the top of the bisection's bracket.
    public static let backRoadsLambda = LambdaSearch.maxLambda

    public let budget: TimeInterval
    public let fastestDuration: TimeInterval
    /// The chosen route's RouteScore, or nil when it carries no scored metres.
    public let routeScore: Double?
    public let backRoads: BackRoads

    public init(budget: TimeInterval, fastestDuration: TimeInterval, routeScore: Double?, backRoads: BackRoads) {
        self.budget = budget
        self.fastestDuration = fastestDuration
        self.routeScore = routeScore
        self.backRoads = backRoads
    }

    /// The budget the "more time" offer re-plans with.
    public var moreTimeBudget: TimeInterval { budget + Self.moreTimeOffer }

    /// What ops/plan prints after `ops/plan REFUSED: `, one fact per line.
    public func lines() -> [String] {
        let floor = ScenicPlan.fixed(RouteScore.honestFailureThreshold, 2)
        let why = routeScore.map { "RouteScore \(ScenicPlan.fixed($0, 3)) is under the \(floor) floor" }
            ?? "the route carries no scored road"
        var lines = [
            "not much pretty within \(Self.minutes(budget)) of this drive: \(why)",
            "OFFER more-time: plan again with \(Self.minutes(moreTimeBudget)) of extra time "
                + "(+\(Self.minutes(Self.moreTimeOffer)))",
        ]
        let lambda = ScenicPlan.fixed(Self.backRoadsLambda, 0)
        switch backRoads {
        case let .offered(duration, score):
            lines.append("OFFER all-back-roads: lambda \(lambda), measured ETA \(ScenicPlan.clock(duration)), "
                + "RouteScore \(ScenicPlan.fixed(score, 3))")
        case let .dull(duration, score):
            let dull = score.map { "RouteScore \(ScenicPlan.fixed($0, 3)) is under the floor too" }
                ?? "it carries no scored road either"
            lines.append("NO-OFFER all-back-roads: lambda \(lambda), measured ETA \(ScenicPlan.clock(duration)), "
                + dull)
        case let .unmeasured(reason):
            lines.append("NO-OFFER all-back-roads: lambda \(lambda) was not measured (\(reason))")
        }
        return lines
    }

    /// `25 minutes` for a whole number of minutes, the report's clock spelling otherwise.
    static func minutes(_ seconds: TimeInterval) -> String {
        guard seconds.isFinite, seconds >= 0, seconds.truncatingRemainder(dividingBy: 60) == 0 else {
            return ScenicPlan.clock(seconds)
        }
        let whole = Int(seconds / 60)
        return whole == 1 ? "1 minute" : "\(whole) minutes"
    }
}
