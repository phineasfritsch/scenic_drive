import Foundation

/// Where the drive session stands with respect to the planned line (T-0317 R5).
public enum DriveMode: Sendable, Equatable, CaseIterable {
    /// On the planned line, or away for less than the dwell.
    case guiding
    /// Off-route while online: one reroute request is out; nothing more is asked until it lands or fails.
    case rerouting
    /// Off-route with no reroute coming: guidance continues toward the planned line, and zero requests are made.
    case rejoining
}
