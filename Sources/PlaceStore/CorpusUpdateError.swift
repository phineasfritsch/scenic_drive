/// Why a corpus OTA step refused (T-0300 O1, O6). A refusal never touches the active corpus.
public enum CorpusUpdateError: Error, Equatable, Sendable {
    /// The manifest body is not a JSON object.
    case manifestNotAnObject
    /// The manifest's keys are not exactly `CorpusManifest.fields`: the missing and the extra ones, sorted.
    case manifestFields(missing: [String], extra: [String])
    /// A manifest field has the wrong JSON type.
    case manifestFieldType(field: String)
    /// A manifest field is of the right type but out of range.
    case manifestValue(field: String)
    /// The downloaded file's byte count, or its SHA-256, is not the manifest's: what was found.
    case verifyFailed(foundBytes: Int, hashMatches: Bool)
    /// rename(2) refused between two corpus slots.
    case renameFailed(from: String, to: String)
}
