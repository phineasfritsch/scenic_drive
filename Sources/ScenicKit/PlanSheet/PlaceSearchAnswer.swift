import Foundation

/// What one submitted address search shows (T-0362 R8): places the sheet can plan to, best first, or one line of copy.
public enum PlaceSearchAnswer: Equatable, Sendable {
    case places([PlanPlace])
    case notice(String)

    /// Said when there is no search to ask - no https base in this build, or the Worker has no search box.
    public static let unavailableNotice = "Address search isn't available yet. Named places still work."
}
