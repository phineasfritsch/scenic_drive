import Foundation

/// A reroute that landed: the new line and the pins on it (T-0321), its ETA and whether it continues the drive
/// (T-0330). DriveSession checks the line, the pins and the ETA before taking any of them.
public struct RerouteReply: Sendable, Equatable {
    public let line: [Coordinate]
    public let waypoints: [Coordinate]
    /// T-0328 R3: the token the Worker remembered THIS answer under; nil when it remembered nothing.
    public let planToken: String?
    /// T-0330 R4: the answer's ETA and the fastest route's from the reroute point, in seconds.
    public let etaSeconds: Double
    public let fastestEtaSeconds: Double
    /// T-0330 R3: true when the Worker continued the recalled drive, false on the fresh plan it fell back to.
    public let continued: Bool

    public init(line: [Coordinate], waypoints: [Coordinate], planToken: String? = nil, etaSeconds: Double = 0,
                fastestEtaSeconds: Double = 0, continued: Bool = false) {
        self.line = line
        self.waypoints = waypoints
        self.planToken = planToken
        self.etaSeconds = etaSeconds
        self.fastestEtaSeconds = fastestEtaSeconds
        self.continued = continued
    }
}
