/// One day of a road trip as the sheet shows it (T-0313 R5): the Worker's split of the chosen route, whether an
/// overnight stop closes the day, and the day's own path - present only in a FULL itinerary, where it is the leg the
/// per-day Apple Maps handoff pins (R6). A preview carries no path, so it offers no handoff.
public struct TripItineraryDay: Equatable, Sendable {
    public let day: Int
    public let driveSeconds: Double
    public let distanceMeters: Double
    public let overnight: Bool
    public let path: [Coordinate]?

    public init(day: Int, driveSeconds: Double, distanceMeters: Double, overnight: Bool, path: [Coordinate]?) {
        self.day = day
        self.driveSeconds = driveSeconds
        self.distanceMeters = distanceMeters
        self.overnight = overnight
        self.path = path
    }
}
