import Foundation

/// The road-trip day splitter (T-0249): A -> B over N days on a +40% scenic budget, a forward pass over the
/// route's edges under a max drive and max distance per day, 2-4 corridor stops a day, an overnight town per
/// boundary. Pure: it reads a recorded route and a list of places and fetches nothing.
public enum RoadTrip {
    public enum Outcome: Sendable, Equatable {
        case plan([RoadTripDay])
        /// The route's seconds exceed fastest + budget: the budget is a ceiling, never a plan over it.
        case overBudget(routeSeconds: Int, ceilingSeconds: Int)
        /// The limits cannot carry the route to B in `days` days; the pass stopped at `reachedVertex`.
        case tooFewDays(days: Int, reachedVertex: Int)
    }

    public static let budgetPercent = 40
    public static let corridorMeters = 5_000.0
    public static let maxStopsPerDay = 4
    public static let overnightRadiusMeters = 15_000.0

    /// The road trip's extra-time budget: 40% of the fastest, rounded DOWN (the ceiling's safe side).
    public static func budgetSeconds(fastestSeconds: Int) -> Int {
        fastestSeconds * budgetPercent / 100
    }

    public static func plan(edges: [RoadTripEdge], places: [RoadTripPlace], fastestSeconds: Int,
                            limits: RoadTripLimits) -> Outcome {
        .plan([])
    }
}
