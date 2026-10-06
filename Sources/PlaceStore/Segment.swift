/// One row of corpus.sqlite's `segments` table, as stored, and its geometry decoded on demand.
///
/// Coordinates stay in the corpus's integer e7 degrees and `geometry` stays the stored BLOB of little-endian
/// int32 (lon_e7, lat_e7) pairs (services/etl/etl/geom.py `pack`); `vertices()` decodes it and refuses any
/// blob the shipping builder cannot write (T-0255 R2). A value and its arithmetic use nothing from GRDB, so
/// this file is not gated on it (T-0255 R5).
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

    /// Bytes per vertex: one little-endian int32 lon_e7, then one lat_e7 (geom.py `PACK = struct.Struct("<ii")`).
    static let vertexBytes = 8
    /// schema.py CHECKs `length(geometry) >= 16`: the builder never stores fewer than two vertices.
    static let minimumVertices = 2
    /// `to_e7` of the widest longitude and latitude extractway.py accepts (+/-180 and +/-90 degrees).
    static let maxLonE7: Int32 = 1_800_000_000
    static let maxLatE7: Int32 = 900_000_000

    /// The decoded polyline in stored order. Throws `SegmentGeometryError` for a blob the builder cannot write:
    /// the byte count first, then the vertex count, then each vertex longitude before latitude (T-0255 R2).
    public func vertices() throws -> [SegmentVertex] {
        guard geometry.count % Self.vertexBytes == 0 else {
            throw SegmentGeometryError.partialVertex(byteCount: geometry.count)
        }
        let count = geometry.count / Self.vertexBytes
        guard count >= Self.minimumVertices else {
            throw SegmentGeometryError.tooFewVertices(count: count)
        }
        var out: [SegmentVertex] = []
        out.reserveCapacity(count)
        for index in 0..<count {
            let start = index * Self.vertexBytes
            let lon = Self.littleEndianInt32(geometry, at: start)
            let lat = Self.littleEndianInt32(geometry, at: start + 4)
            guard lon >= -Self.maxLonE7 && lon <= Self.maxLonE7 else {
                throw SegmentGeometryError.longitudeOutOfRange(index: index, lonE7: lon)
            }
            guard lat >= -Self.maxLatE7 && lat <= Self.maxLatE7 else {
                throw SegmentGeometryError.latitudeOutOfRange(index: index, latE7: lat)
            }
            out.append(SegmentVertex(lonE7: lon, latE7: lat))
        }
        return out
    }

    private static func littleEndianInt32(_ bytes: [UInt8], at start: Int) -> Int32 {
        let b0 = UInt32(bytes[start])
        let b1 = UInt32(bytes[start + 1]) << 8
        let b2 = UInt32(bytes[start + 2]) << 16
        let b3 = UInt32(bytes[start + 3]) << 24
        return Int32(bitPattern: b0 | b1 | b2 | b3)
    }
}
