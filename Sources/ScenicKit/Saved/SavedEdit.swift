/// A change the Saved list asks the user store to make (T-0306 R4); the view hands it to the store and nothing else.
public enum SavedEdit: Equatable, Sendable {
    case rename(Int64, String)
    case delete(Int64)
}
