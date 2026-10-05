#if canImport(GRDB)
/// Why `PlaceStore(path:)` refused a file. Every refusal is a reason a device must not read the file at all.
public enum PlaceStoreError: Error, Equatable {
    /// `PRAGMA application_id` is not "SCNC": the file is some other SQLite database.
    case notACorpus(applicationID: Int)
    /// `meta.schema_version` is not `PlaceStore.schemaVersion`: this reader cannot parse that file (plan, OTA).
    case schemaVersionMismatch(found: String, expected: Int)
    /// `meta.build_complete` is not "1": the build was killed before CorpusWriter.finalize.
    case incompleteBuild(buildComplete: String)
    /// A required `meta` key is absent.
    case missingMeta(key: String)
    /// A `meta` value the device compares as an integer is not one.
    case malformedMeta(key: String, value: String)
}
#endif
