import Foundation

/// The reach the Surprise card uses until the /isochrone client exists (T-0273 R2): straight-line distance, a road
/// factor and an average speed. An ESTIMATE, and the card says so; T-0263's SurpriseIsochrone replaces it with the
/// same SurpriseReach, so Surprise.pick never changes.
public enum SurpriseOfflineReach {
    /// Road distance over straight-line distance: canyon and surface-street circuity.
    public static let roadFactor = 1.4

    /// 45 km/h, no traffic data.
    public static let averageMetersPerMinute = 750.0

    /// The round trip the card offers: two hours to kill.
    public static let budgetMinutes = 120

    /// Where the estimate starts. The app holds no location yet (no CoreLocation in a feature target, no
    /// permission flow), so the card names it.
    public static let origin = Coordinate(latitude: 34.0689, longitude: -118.4452)

    /// The origin as the card says it.
    public static let originName = "Westwood"

    /// There and back, rounded UP to the minute: the card never promises less than the estimate.
    public static func roundTripMinutes(meters: Double) -> Int {
        Int((2 * meters * roadFactor / averageMetersPerMinute).rounded(.up))
    }

    /// Every candidate's estimated round trip from `origin`; the budget is the selector's ceiling.
    public static func reach(from origin: Coordinate, to candidates: [SurpriseCandidate],
                             budgetMinutes: Int) -> SurpriseReach {
        var minutes: [String: Int] = [:]
        for candidate in candidates {
            minutes[candidate.id] = roundTripMinutes(meters: Geo.distanceMeters(origin, candidate.coordinate))
        }
        return SurpriseReach(budgetMinutes: budgetMinutes, roundTripMinutes: minutes)
    }
}
