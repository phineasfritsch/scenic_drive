/// Where the Saved list is (T-0306 R4): loading -> list, and from the list one of renaming, confirmDelete,
/// needsReplan (a refused replay, shown with its own line) or replaying - each back to the list.
public enum SavedListState: Equatable, Sendable {
    case loading
    case list
    case renaming(Int64, String)
    case confirmDelete(Int64)
    case needsReplan(Int64)
    case replaying(Int64)
}
