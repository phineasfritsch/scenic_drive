import Foundation

/// What the drive session asks for when it leaves the line online: the rest of the SAME drive, never a bare
/// origin-to-destination (T-0317 R2/R4, P-NAV-01).
///
/// This is the device-side value. How it travels is the Worker's half: /plan's whitelist carries neither pins
/// nor lambda today, and the server may never receive more than one 2-dp coordinate per action, so the wire
/// form is free to send a plan token plus `firstRemainingWaypoint` instead of the coordinates themselves.
public struct RerouteRequest: Sendable, Equatable {
    /// The fix that tripped the reroute.
    public let origin: Coordinate
    /// The pinned waypoints not yet passed, in route order.
    public let remainingWaypoints: [Coordinate]
    /// The index in the current plan's pins of `remainingWaypoints.first` (the count of pins already passed).
    public let firstRemainingWaypoint: Int
    /// The planned line's last vertex.
    public let destination: Coordinate
    /// The plan's lambda, unchanged.
    public let lambda: Double

    public init(origin: Coordinate, remainingWaypoints: [Coordinate], firstRemainingWaypoint: Int,
                destination: Coordinate, lambda: Double) {
        self.origin = origin
        self.remainingWaypoints = remainingWaypoints
        self.firstRemainingWaypoint = firstRemainingWaypoint
        self.destination = destination
        self.lambda = lambda
    }
}
