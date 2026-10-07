/// Why `SavedDriveStore` refused a file or a request (T-0290 R1, R2, R6).
public enum UserStoreError: Error, Equatable, Sendable {
    /// `PRAGMA application_id` is neither 0 (a fresh file) nor "SCNU": corpus.sqlite or some other database.
    case notAUserStore(applicationID: Int)
    /// The file records migrations this build does not know (sorted): a newer build wrote it. Nothing was written.
    case unknownMigrations([String])
    /// No saved drive has this id.
    case driveNotFound(id: Int64)
}
