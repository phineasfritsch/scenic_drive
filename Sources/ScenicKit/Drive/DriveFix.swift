import Foundation

/// One location fix as the drive session sees it: where, how fast, when.
///
/// Foundation-only: NavAdapter bridges a CLLocation into this at its boundary. `speedMetersPerSecond` is passed
/// through as reported, including CoreLocation's -1 for "invalid" - DriveSurface reads that as moving.
/// `timestamp` is seconds on any monotone clock; only differences between fixes are read.
public struct DriveFix: Sendable, Equatable {
    public let coordinate: Coordinate
    public let speedMetersPerSecond: Double
    public let timestamp: TimeInterval

    public init(coordinate: Coordinate, speedMetersPerSecond: Double, timestamp: TimeInterval) {
        self.coordinate = coordinate
        self.speedMetersPerSecond = speedMetersPerSecond
        self.timestamp = timestamp
    }

    /// A fix the session may act on: a real position and a finite clock. Anything else is ignored whole.
    public var isUsable: Bool {
        coordinate.latitude.isFinite && coordinate.longitude.isFinite && timestamp.isFinite
            && (-90...90).contains(coordinate.latitude) && (-180...180).contains(coordinate.longitude)
    }
}
