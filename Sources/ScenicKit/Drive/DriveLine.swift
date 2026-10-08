import Foundation

/// The planned polyline a drive follows, and the two measurements the session takes against it (T-0317 R3/R4).
///
/// Distances are taken in a local equirectangular frame centred on the fix: metres east scaled by the cosine of
/// the fix's latitude, metres north unscaled. Over the tens of metres the off-route threshold turns on, that is
/// far inside GPS error; it is exact enough that a fix at a known offset measures to the bit, which is what
/// lets the threshold be tabled at its exact bound.
public struct DriveLine: Sendable, Equatable {
    /// Metres per degree of latitude on Geo's sphere.
    public static let metersPerDegree = Geo.earthRadiusMeters * Double.pi / 180

    public let coordinates: [Coordinate]

    /// nil for fewer than two vertices or any vertex that is not a real position.
    public init?(_ coordinates: [Coordinate]) {
        guard coordinates.count >= 2 else { return nil }
        for c in coordinates {
            guard c.latitude.isFinite, c.longitude.isFinite,
                  (-90...90).contains(c.latitude), (-180...180).contains(c.longitude) else { return nil }
        }
        self.coordinates = coordinates
    }

    public var destination: Coordinate { coordinates[coordinates.count - 1] }
    public var segmentCount: Int { coordinates.count - 1 }

    /// The least distance, in metres, from `point` to the whole line.
    public func distanceMeters(from point: Coordinate) -> Double {
        var best = Double.infinity
        for segment in 0..<segmentCount {
            best = min(best, distanceMeters(from: point, toSegment: segment))
        }
        return best
    }

    /// The distance from `point` to the segment from vertex `segment` to vertex `segment + 1`.
    public func distanceMeters(from point: Coordinate, toSegment segment: Int) -> Double {
        let scale = cos(point.latitude * Double.pi / 180) * Self.metersPerDegree
        let a = coordinates[segment], b = coordinates[segment + 1]
        let ax = (a.longitude - point.longitude) * scale, ay = (a.latitude - point.latitude) * Self.metersPerDegree
        let bx = (b.longitude - point.longitude) * scale, by = (b.latitude - point.latitude) * Self.metersPerDegree
        let dx = bx - ax, dy = by - ay
        let length2 = dx * dx + dy * dy
        let t = length2 > 0 ? min(1, max(0, -(ax * dx + ay * dy) / length2)) : 0
        let cx = ax + t * dx, cy = ay + t * dy
        return (cx * cx + cy * cy).squareRoot()
    }

    /// The segment the driver is on, searched FORWARD from `start` (R4): the first segment at or after `start`
    /// within `threshold`, then the nearest of the contiguous run of within-threshold segments it begins. A loop's
    /// closing leg beside its start is not contiguous with the opening run, so progress cannot jump to the end.
    /// `start` when no segment at or after it is within `threshold`.
    public func progress(from start: Int, at point: Coordinate, within threshold: Double) -> Int {
        var first = start
        while first < segmentCount, !(distanceMeters(from: point, toSegment: first) <= threshold) { first += 1 }
        guard first < segmentCount else { return start }
        var best = first
        var bestDistance = distanceMeters(from: point, toSegment: first)
        var next = first + 1
        while next < segmentCount {
            let d = distanceMeters(from: point, toSegment: next)
            guard d <= threshold else { break }
            if d < bestDistance { best = next; bestDistance = d }
            next += 1
        }
        return best
    }

    /// The vertex index of each pin, matched in order, each strictly after the previous; nil if any pin is not a
    /// vertex of this line in that order.
    public func vertexIndices(of pins: [Coordinate]) -> [Int]? {
        var indices: [Int] = []
        var from = 0
        for pin in pins {
            guard let found = coordinates[from...].firstIndex(of: pin) else { return nil }
            indices.append(found)
            from = found + 1
        }
        return indices
    }
}
