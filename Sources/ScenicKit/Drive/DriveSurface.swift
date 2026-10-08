import Foundation

/// How much of the drive screen a moving driver may see (T-0317 R6, P-SAFE-09 - the plan's P-SAFE-06 row).
public enum DriveSurface: Sendable, Equatable, CaseIterable {
    /// Stopped or crawling: the whole drive screen.
    case full
    /// Moving: the one large action and voice, nothing else.
    case minimal

    /// The plan's bound. Strictly above it is moving; exactly 4.5 m/s is not.
    public static let motionGateMetersPerSecond: Double = 4.5

    /// `.full` only for a known speed in [0, 4.5]; NaN, negative (CoreLocation's -1 means "invalid") and
    /// infinite speeds are unknown, and an unknown speed is treated as moving.
    public init(speedMetersPerSecond speed: Double) {
        self = speed >= 0 && speed <= Self.motionGateMetersPerSecond ? .full : .minimal
    }
}
