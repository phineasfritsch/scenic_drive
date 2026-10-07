/// A query box in WGS-84 degrees, matched against `segments_rtree` by INTERSECTION.
///
/// Degrees, not e7 integers, because that is what the R*Tree stores (corpuswriter.py writes `min_lon / E7`);
/// the values pass straight into SQL and nothing here converts them.
public struct BoundingBox: Equatable, Sendable {
    public let minLon: Double
    public let minLat: Double
    public let maxLon: Double
    public let maxLat: Double

    public init(minLon: Double, minLat: Double, maxLon: Double, maxLat: Double) {
        self.minLon = minLon
        self.minLat = minLat
        self.maxLon = maxLon
        self.maxLat = maxLat
    }
}
