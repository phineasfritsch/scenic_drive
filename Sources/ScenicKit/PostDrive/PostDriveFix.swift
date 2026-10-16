import Foundation

/// The one fix read at an app open after a handoff (T-0366 R3), as CoreLocation gives it: the speed, its accuracy
/// and how old the fix is. Read, turned into a surface, and dropped - nothing stores it.
public struct PostDriveFix: Sendable, Equatable {
    /// A cached fix older than this may be from before the drive, stopped while the driver now moves: not fresh.
    public static let maxAgeSeconds: Double = 10

    public let speedMetersPerSecond: Double
    /// CoreLocation's speedAccuracy: negative means the speed is invalid.
    public let speedAccuracy: Double
    /// Seconds since the fix was taken.
    public let ageSeconds: Double

    public init(speedMetersPerSecond: Double, speedAccuracy: Double, ageSeconds: Double) {
        self.speedMetersPerSecond = speedMetersPerSecond
        self.speedAccuracy = speedAccuracy
        self.ageSeconds = ageSeconds
    }

    /// `.full` only for a known speed (finite accuracy >= 0) on a fresh fix (age in [0, 10] s) that DriveSurface
    /// calls full; anything unknown is moving (P-SAFE-09).
    public var surface: DriveSurface {
        guard speedAccuracy >= 0, speedAccuracy.isFinite, ageSeconds >= 0, ageSeconds <= Self.maxAgeSeconds else {
            return .minimal
        }
        return DriveSurface(speedMetersPerSecond: speedMetersPerSecond)
    }
}
