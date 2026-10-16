import Foundation

/// When the app may ask the post-drive question (T-0358 R2/R3): as an in-app drive ends, or at the next open after a
/// handoff (region monitoring needs an owner capability, so the free tier cannot be asked at arrival).
public enum PostDriveMoment: Sendable, Equatable, Hashable, CaseIterable {
    /// The driver tapped End drive.
    case driveEnded
    /// The app came to the foreground after a handoff.
    case appOpened
}
