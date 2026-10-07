/// Which number of a saved drive a `SavedDriveError` refused (T-0290 R4b).
public enum SavedDriveField: Equatable, Sendable {
    case latitude
    case longitude
    case lambda
}
