import Foundation

/// RED STUB (T-0317): replaced by the ruled gate in the GREEN commit.
public enum DriveSurface: Sendable, Equatable {
    case full
    case minimal

    public static let motionGateMetersPerSecond: Double = 4.5

    public init(speedMetersPerSecond speed: Double) {
        self = .full
    }
}
