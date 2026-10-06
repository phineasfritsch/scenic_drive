/// Why `Segment.vertices()` refused a geometry BLOB: each case is a blob the shipping builder cannot write
/// (T-0255 ruling R2), so a corpus holding one is corrupt and no polyline is drawn from it.
public enum SegmentGeometryError: Error, Equatable {
    /// The byte count is not a multiple of 8 (one little-endian int32 lon_e7 + one lat_e7 per vertex).
    case partialVertex(byteCount: Int)
    /// Fewer than two whole vertices; schema.py CHECKs `length(geometry) >= 16`.
    case tooFewVertices(count: Int)
    /// A lon_e7 outside [-1_800_000_000, 1_800_000_000]; extractway.py refuses such a longitude.
    case longitudeOutOfRange(index: Int, lonE7: Int32)
    /// A lat_e7 outside [-900_000_000, 900_000_000]; extractway.py refuses such a latitude.
    case latitudeOutOfRange(index: Int, latE7: Int32)
}
