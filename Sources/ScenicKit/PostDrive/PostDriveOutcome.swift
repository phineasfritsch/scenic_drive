import Foundation

/// How a drive ended, for the post-drive question (T-0358 R1). The app has no entitlement state, so the plan's tier
/// split is a split by where the drive ran: in-app guidance (the paid surface) arrives or ends early; a handoff to
/// another maps app (the free surface) is all the app ever knows of the free drive.
public enum PostDriveOutcome: Sendable, Equatable, Hashable, CaseIterable {
    /// An in-app drive ended after DriveVoice's arrival (the destination within 30 m along the line): drive_completed.
    case arrived
    /// An in-app drive ended before arriving.
    case endedEarly
    /// The route was handed to another maps app; the drive itself happened there.
    case handedOff
}
