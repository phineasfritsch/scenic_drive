import Foundation

/// One day of a road trip: the vertices it drives between, its driving seconds and metres, its corridor stops
/// in route order, and where it sleeps. The last day arrives at B, so its `overnight` is nil (T-0249 R1).
public struct RoadTripDay: Sendable, Equatable {
    public enum Overnight: Sendable, Equatable {
        /// The nearest lodging within `RoadTrip.overnightRadiusMeters` of the day's end vertex.
        case lodging(name: String, meters: Int)
        /// No lodging within the radius - said, never papered over (T-0249 R6).
        case noLodging
    }

    public let day: Int
    public let startVertex: Int
    public let endVertex: Int
    public let seconds: Int
    public let meters: Int
    public let stops: [String]
    public let overnight: Overnight?

    public init(day: Int, startVertex: Int, endVertex: Int, seconds: Int, meters: Int, stops: [String],
                overnight: Overnight?) {
        self.day = day
        self.startVertex = startVertex
        self.endVertex = endVertex
        self.seconds = seconds
        self.meters = meters
        self.stops = stops
        self.overnight = overnight
    }
}
