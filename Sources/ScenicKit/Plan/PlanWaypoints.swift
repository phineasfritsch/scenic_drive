import Foundation

/// The pins that make a handoff reproduce the planned drive instead of approximating it.
///
/// Apple Maps is handed an origin, a destination and a short ordered list of stops; it re-routes between
/// consecutive stops. So a pin has to be placed wherever the planned route makes a choice a fastest-route
/// engine would not make - which is where the route CHANGES ROAD. Pinning evenly spaced points instead
/// would put pins in the middle of long straight stretches, where they buy nothing, and leave the junction
/// that matters unpinned.
///
/// When there are more road changes than pins to spend, the ones kept are the changes onto the LONGEST
/// stretches: a 6 km road the driver must be on is what the route is; a 40 m connector between two of them
/// is reproduced by any router that is already at both ends of it.
public enum PlanWaypoints {

    /// Our cap, and it must equal `AppleMapsDirections.maxWaypoints`. ScenicKit cannot import Handoff - the
    /// dependency runs the other way and that direction is deliberate - so the two constants are held
    /// together by a test in HandoffTests, which is the only place both types are visible.
    public static let maximum = 9

    /// Up to `limit` decision points along the route, in route order.
    ///
    /// The origin and the destination are never among them: they are the URL's `source` and `destination`,
    /// and pinning them again spends a waypoint on a point Apple Maps already has.
    public static func decisionPoints(table: PlanTable, path: RoutePath,
                                      limit: Int = maximum) -> [Coordinate] {
        guard limit > 0, path.coordinates.count > 2 else { return [] }
        let last = path.coordinates.count - 1
        let candidates = table.rows.dropFirst().filter { $0.fromIndex > 0 && $0.fromIndex < last }
        let kept = candidates
            .sorted { left, right in
                left.meters == right.meters ? left.fromIndex < right.fromIndex : left.meters > right.meters
            }
            .prefix(limit)
            .map(\.fromIndex)
            .sorted()
        return kept.map { path.coordinates[$0] }
    }
}
