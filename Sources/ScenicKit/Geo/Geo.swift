import Foundation

/// Great-circle geometry on a spherical Earth. Accurate to ~0.3%, which is more than the
/// scenic engine needs; nothing downstream depends on sub-metre precision.
public enum Geo {
    /// IUGG mean Earth radius.
    public static let earthRadiusMeters: Double = 6_371_008.8

    /// Haversine distance in metres.
    public static func distanceMeters(_ a: Coordinate, _ b: Coordinate) -> Double {
        let lat1 = a.latitude.radians, lat2 = b.latitude.radians
        let dLat = (b.latitude - a.latitude).radians
        let dLon = (b.longitude - a.longitude).radians
        let h = sin(dLat / 2) * sin(dLat / 2) + cos(lat1) * cos(lat2) * sin(dLon / 2) * sin(dLon / 2)
        return 2 * earthRadiusMeters * asin(min(1, sqrt(h)))
    }

    /// Initial bearing from `a` to `b`, degrees clockwise from true north in [0, 360).
    public static func initialBearingDegrees(from a: Coordinate, to b: Coordinate) -> Double {
        let lat1 = a.latitude.radians, lat2 = b.latitude.radians
        let dLon = (b.longitude - a.longitude).radians
        let y = sin(dLon) * cos(lat2)
        let x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dLon)
        let deg = atan2(y, x).degrees
        return (deg + 360).truncatingRemainder(dividingBy: 360)
    }
}

extension Double {
    var radians: Double { self * .pi / 180 }
    var degrees: Double { self * 180 / .pi }
}
