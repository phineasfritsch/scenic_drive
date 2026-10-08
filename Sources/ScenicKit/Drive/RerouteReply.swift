import Foundation

/// A reroute that landed: the new line and the pins on it (T-0321). DriveSession checks both before taking them.
public struct RerouteReply: Sendable, Equatable {
    public let line: [Coordinate]
    public let waypoints: [Coordinate]
    /// T-0328 R3: the token the Worker remembered THIS answer under; nil when it remembered nothing.
    public let planToken: String?

    public init(line: [Coordinate], waypoints: [Coordinate], planToken: String? = nil) {
        self.line = line
        self.waypoints = waypoints
        self.planToken = planToken
    }
}
