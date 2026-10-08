import Foundation

/// A reroute that landed: the new line and the pins on it (T-0321). DriveSession checks both before taking them.
public struct RerouteReply: Sendable, Equatable {
    public let line: [Coordinate]
    public let waypoints: [Coordinate]

    public init(line: [Coordinate], waypoints: [Coordinate]) {
        self.line = line
        self.waypoints = waypoints
    }
}
