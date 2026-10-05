import Foundation

/// What the driver asked for: the trip in `days` days, no day over `maxDriveSeconds` of driving or
/// `maxMeters` of road (the caller converts miles at 1609.344 m). Both limits are inclusive (T-0249 R4).
public struct RoadTripLimits: Sendable, Equatable {
    public let days: Int
    public let maxDriveSeconds: Int
    public let maxMeters: Int

    public init(days: Int, maxDriveSeconds: Int, maxMeters: Int) {
        self.days = days
        self.maxDriveSeconds = maxDriveSeconds
        self.maxMeters = maxMeters
    }
}
