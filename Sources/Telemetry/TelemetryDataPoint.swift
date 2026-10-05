import Foundation

/// One Workers Analytics Engine data point, the object `writeDataPoint` takes: `indexes` (at most one, the
/// sampling key), `blobs` and `doubles`, positional - AE stores them as blob1..., double1.... T-0265 R2 fixes
/// the width so a query over blobN or doubleN never shifts by event: indexes = [event], blobs = [event,
/// label, H3 cell or ""], doubles = [value1, value2]. No time is carried; AE stamps its own.
public struct TelemetryDataPoint: Equatable, Encodable, Sendable {
    public let indexes: [String]
    public let blobs: [String]
    public let doubles: [Double]

    public init(indexes: [String], blobs: [String], doubles: [Double]) {
        self.indexes = indexes
        self.blobs = blobs
        self.doubles = doubles
    }
}
