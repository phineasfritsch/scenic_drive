import Foundation

/// One replay as the Saved list hands it to the plan sheet (T-0306 R3): the saved start already at 2 dp, the corpus
/// place nearest the saved end, and the saved budget. The saved waypoints are not here: they never leave the device.
public struct SavedReplay: Equatable, Sendable {
    /// How far from the saved end, in degrees on each axis, a destination place may be.
    public static let reach: Double = 0.01
    public let id: Int64
    public let start: Coordinate
    public let destination: PlanPlace
    public let budgetMinutes: Int

    public init(id: Int64, start: Coordinate, destination: PlanPlace, budgetMinutes: Int) {
        self.id = id
        self.start = start
        self.destination = destination
        self.budgetMinutes = budgetMinutes
    }

    /// The place within `reach` of `point` on both axes (inclusive) nearest to it, east-west scaled by the cosine of
    /// the latitude; a tie goes to the lower id. Nil when none is within reach.
    public static func nearest(to point: Coordinate, among places: [PlanPlace]) -> PlanPlace? {
        let scale = cos(point.latitude * Double.pi / 180)
        var best: (place: PlanPlace, distance: Double)?
        for place in places {
            let dLat = place.coordinate.latitude - point.latitude
            let dLon = place.coordinate.longitude - point.longitude
            guard abs(dLat) <= reach, abs(dLon) <= reach else { continue }
            let distance = dLat * dLat + (dLon * scale) * (dLon * scale)
            if let current = best, current.distance < distance
                || (current.distance == distance && current.place.id < place.id) { continue }
            best = (place, distance)
        }
        return best?.place
    }
}
