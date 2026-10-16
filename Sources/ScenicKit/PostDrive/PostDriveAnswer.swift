import Foundation

/// The closed answer set of the post-drive question (T-0358 R5), in the order the buttons show. Two answers send the
/// post_drive_answer case (a Bool on the wire); skipping sends nothing.
public enum PostDriveAnswer: Sendable, Equatable, Hashable, CaseIterable {
    case prettier
    case notPrettier
    case dismissed

    /// The button's words.
    public var title: String {
        switch self {
        case .prettier: return "Prettier"
        case .notPrettier: return "Not really"
        case .dismissed: return "Skip"
        }
    }

    /// What the telemetry case carries, or nil when nothing is sent.
    public var prettier: Bool? {
        switch self {
        case .prettier: return true
        case .notPrettier: return false
        case .dismissed: return nil
        }
    }
}
