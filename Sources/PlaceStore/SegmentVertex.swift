/// One decoded vertex of a segment's geometry, in the corpus's integer e7 degrees: `geom.to_e7` in
/// services/etl/etl/geom.py, `int(round(degrees * 1e7))`. Longitude first, the order the BLOB stores.
public struct SegmentVertex: Equatable, Sendable {
    public let lonE7: Int32
    public let latE7: Int32

    public init(lonE7: Int32, latE7: Int32) {
        self.lonE7 = lonE7
        self.latE7 = latE7
    }
}
