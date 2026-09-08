import Foundation

/// How much of a loop is the same road driven twice, in opposite directions.
///
/// "Just drive 45 minutes and come back" is a paid feature, and the thing that ruins it is a route that goes
/// out along a road and returns along the same road. GraphHopper's `round_trip` produces those regularly -
/// it optimises for a distance target, and out-and-back is the cheapest way to hit one. So the check is
/// ours, applied to the returned geometry, and a route that fails it is reseeded rather than shown.
///
/// The plan's parameters: **25 m cells, heading delta > 150 degrees, retrace < 15% of length.**
///
/// ## Three things that are easy to get wrong here, and all three are in the tests
///
/// **The heading comparison must wrap.** A road driven north-north-west at 350 degrees and back at 170 is a
/// retrace; `abs(350 - 170) = 180` catches that one, but a road at 010 driven back at 190 gives
/// `abs(10 - 190) = 180` and a road at 350 returning at 010 gives `abs(350 - 10) = 340`, which a naive
/// comparison reads as *more* opposite than opposite. This repository already contains that exact bug,
/// reproduced deliberately in `services/etl/etl/curvature.py` to match the Curvature project's published
/// numbers - which is a good reason to be sure it is not reproduced accidentally here.
///
/// **Long segments must be sampled, not just endpointed.** OSM ways are sometimes drawn with a single
/// straight segment hundreds of metres long. Recording only its midpoint puts a 500 m stretch in one 25 m
/// cell, and the return trip along it then registers as 25 m of retrace out of 500. The route would pass a
/// 15% test while being an out-and-back.
///
/// **Cells must be metric.** A grid quantised in degrees is 25 m tall and about 19 m wide at Los Angeles,
/// and 12 m wide in Anchorage. Two passes that fall in different cells are not detected at all.
public enum RetraceDetector {
    /// Metres. Coarse enough that the two directions of one road land in the same cell, fine enough that
    /// genuinely different parallel roads do not.
    public static let cellSizeMeters = 25.0

    /// Degrees. Above this the two passes are heading opposite ways rather than merely crossing.
    public static let oppositeHeadingDegrees = 150.0

    /// A loop may be this much retrace and no more.
    public static let maxRetraceFraction = 0.15

    /// Samples per cell along a segment. Two is enough that no cell a segment crosses is skipped.
    static let samplesPerCell = 2.0

    /// The fraction of the route's length driven in the opposite direction to an earlier pass through the
    /// same 25 m cell. Nil for a route with no length - there is no fraction of nothing.
    public static func retraceFraction(_ points: [Coordinate]) -> Double? {
        guard points.count >= 2 else { return nil }
        for p in points where !(p.latitude.isFinite && p.longitude.isFinite) { return nil }

        let origin = points[0]
        guard metersPerDegreeLongitude(at: origin.latitude) > 1 else { return nil }  // no grid at the pole

        var headingsByCell: [Cell: [Double]] = [:]
        var total = 0.0
        var retraced = 0.0

        for (a, b) in zip(points, points.dropFirst()) {
            let length = Geo.distanceMeters(a, b)
            guard length.isFinite, length > 0 else { continue }
            total += length
            let heading = Geo.initialBearingDegrees(from: a, to: b)

            let steps = max(1, Int((length / (cellSizeMeters / samplesPerCell)).rounded(.up)))
            let share = length / Double(steps)
            for i in 0..<steps {
                let t = (Double(i) + 0.5) / Double(steps)
                let lat = a.latitude + (b.latitude - a.latitude) * t
                let lon = a.longitude + (b.longitude - a.longitude) * t
                let cell = self.cell(Coordinate(latitude: lat, longitude: lon), origin: origin)
                let seen = headingsByCell[cell] ?? []
                if seen.contains(where: { angularDifference($0, heading) > oppositeHeadingDegrees }) {
                    retraced += share
                }
                headingsByCell[cell] = seen + [heading]
            }
        }

        guard total > 0 else { return nil }
        return retraced / total
    }

    /// True when the route retraces itself little enough to be worth calling a loop.
    public static func isAcceptableLoop(_ points: [Coordinate]) -> Bool {
        guard let f = retraceFraction(points) else { return false }
        return f <= maxRetraceFraction
    }

    /// Metres per degree of longitude at a latitude.
    ///
    /// Extracted so the grid can be tested directly. A constant 111_320 here - the equatorial value - makes
    /// cells 25 m tall and 12.5 m wide at latitude 60, and a road driven out and back with any lateral
    /// offset then lands in different columns and goes undetected. That failure is invisible to any
    /// out-and-back fixture, because an exact retrace lands in the same cell whatever shape the cell is;
    /// the only way to see it is to ask the grid directly, which `cellsAreSquare` does.
    static func metersPerDegreeLongitude(at latitude: Double) -> Double {
        111_320.0 * cos(latitude * .pi / 180)
    }

    static let metersPerDegreeLatitude = 111_132.0

    /// The cell a point falls in, relative to the route's first point.
    static func cell(_ p: Coordinate, origin: Coordinate) -> Cell {
        Cell(
            x: Int(((p.longitude - origin.longitude)
                    * metersPerDegreeLongitude(at: origin.latitude) / cellSizeMeters).rounded(.down)),
            y: Int(((p.latitude - origin.latitude)
                    * metersPerDegreeLatitude / cellSizeMeters).rounded(.down))
        )
    }

    /// The smaller angle between two compass headings, in `0...180`.
    ///
    /// This is the wrap-aware form. `abs(a - b)` is the bug: it calls 350 and 010 - twenty degrees apart, the
    /// same direction - a 340 degree difference, and would count a road continuing straight through north as
    /// a retrace of itself.
    static func angularDifference(_ a: Double, _ b: Double) -> Double {
        let d = abs(a - b).truncatingRemainder(dividingBy: 360)
        return d > 180 ? 360 - d : d
    }

    struct Cell: Hashable {
        let x: Int
        let y: Int
    }
}
