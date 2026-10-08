import Foundation

/// RED STUB (T-0317): the signatures only; replaced by the ruled state machine in the GREEN commit.
public struct DriveSession: Sendable, Equatable {
    public static let awayThresholdMeters: Double = 50
    public static let offRouteDwellSeconds: TimeInterval = 5

    public private(set) var mode: DriveMode = .guiding
    public private(set) var surface: DriveSurface = .full
    public private(set) var line: DriveLine
    public private(set) var waypoints: [Coordinate]
    public private(set) var progressSegment = 0
    public private(set) var isOnline: Bool
    public let lambda: Double

    public init?(line coordinates: [Coordinate], waypoints: [Coordinate], lambda: Double, online: Bool) {
        guard let line = DriveLine(coordinates) else { return nil }
        self.line = line
        self.waypoints = waypoints
        self.lambda = lambda
        self.isOnline = online
    }

    public mutating func observe(_ fix: DriveFix) -> RerouteRequest? { nil }
    public mutating func connectivity(online: Bool) -> RerouteRequest? { nil }
    @discardableResult
    public mutating func rerouteArrived(line coordinates: [Coordinate], waypoints: [Coordinate]) -> Bool { false }
    public mutating func rerouteFailed() {}
}
