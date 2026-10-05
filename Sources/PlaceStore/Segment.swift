#if canImport(GRDB)
/// One row of corpus.sqlite's `segments` table, as stored.
///
/// Coordinates stay in the corpus's integer e7 degrees and `geometry` stays the stored BLOB of little-endian
/// int32 (lon_e7, lat_e7) pairs: decoding it into vertices is arithmetic that reaches the drawn line, and it
/// lands with its first consumer and its own mutation population (T-0175 ruling R5).
public struct Segment: Equatable, Sendable {
    public let segmentID: Int64
    public let wayID: Int64
    public let bucket: Int
    public let offsetMM: Int
    public let lengthMM: Int
    public let minLonE7: Int
    public let minLatE7: Int
    public let maxLonE7: Int
    public let maxLatE7: Int
    public let midLonE7: Int
    public let midLatE7: Int
    public let geometry: [UInt8]

    public init(segmentID: Int64, wayID: Int64, bucket: Int, offsetMM: Int, lengthMM: Int,
                minLonE7: Int, minLatE7: Int, maxLonE7: Int, maxLatE7: Int, midLonE7: Int, midLatE7: Int,
                geometry: [UInt8]) {
        self.segmentID = segmentID
        self.wayID = wayID
        self.bucket = bucket
        self.offsetMM = offsetMM
        self.lengthMM = lengthMM
        self.minLonE7 = minLonE7
        self.minLatE7 = minLatE7
        self.maxLonE7 = maxLonE7
        self.maxLatE7 = maxLatE7
        self.midLonE7 = midLonE7
        self.midLatE7 = midLatE7
        self.geometry = geometry
    }
}
#endif
