import Foundation

/// A drive's start and end moments, each at most once (T-0361 R6). NavAdapter's DriveHost asks `begin()` after
/// guidance starts and `end(_:arrived:)` as the drive leaves the screen; an end with no start, a second start and a
/// second end are nothing - SwiftUI may call appear and disappear more than once.
public struct DriveMomentLatch: Sendable, Equatable {
    public private(set) var hasBegun = false
    public private(set) var hasEnded = false

    public init() {}

    /// `.guidanceBegan` the first time; nil after.
    public mutating func begin() -> AppMoment? {
        guard !hasBegun else { return nil }
        hasBegun = true
        return .guidanceBegan
    }

    /// `.guidanceEnded` from the session the first time after `begin()`; nil before it and after.
    public mutating func end(_ session: DriveSession, arrived: Bool) -> AppMoment? {
        guard hasBegun, !hasEnded else { return nil }
        hasEnded = true
        return .guidanceEnded(arrived: arrived, fractionDriven: session.fractionDriven,
                              offRouteCount: session.offRouteCount)
    }
}
