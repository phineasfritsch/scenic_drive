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
        // Range, not just finiteness. The adjacent guard exists to refuse nonsense rather than quantise it,
        // and it screened the wrong predicate: a longitude of 1e17 is perfectly finite and made the cell
        // arithmetic trap with "Double value cannot be converted to Int because the result would be greater
        // than Int.max". Unreachable from the router today, which is not a reason for the guard to be wrong.
        for p in points where !(-90.0...90.0).contains(p.latitude)
            || !(-180.0...180.0).contains(p.longitude) { return nil }

        // The anchor and the longitude scale come from the BOUNDING BOX, never from points[0].
        //
        // `points[0]` made the grid's position depend on which end of the road the drive started at, and the
        // verdict with it: reviewer-pr76 swept one fixed connector and got f = 0.498 (reject) at 0 m, 0.497
        // at 6 m, and 0.0 (ACCEPT) at 12 m - the same piece of road, three answers. Reversing a route moved
        // the grid by the 14 m between carriageways and flipped `isAcceptableLoop` outright.
        //
        // min and max over the points do not depend on the order they arrive in, so a reversed route gets an
        // identical grid. The reference latitude is the box's mid-latitude rather than any one point's, so
        // the cells stay square across the whole route instead of being sized by whichever end came first.
        let lats = points.map(\.latitude)
        let lons = points.map(\.longitude)
        guard let minLat = lats.min(), let maxLat = lats.max(), let minLon = lons.min() else { return nil }
        let mPerLon = metersPerDegreeLongitude(at: (minLat + maxLat) / 2)
        guard mPerLon > 1 else { return nil }  // no grid at the pole
        let anchor = Coordinate(latitude: minLat, longitude: minLon)

        return retraceFraction(points, anchor: anchor, metersPerDegreeLon: mPerLon)
    }

    /// The retrace fraction on a grid anchored at `anchor`.
    static func retraceFraction(_ points: [Coordinate],
                                anchor: Coordinate,
                                metersPerDegreeLon: Double) -> Double? {
        var samplesByCell: [Cell: [(point: Coordinate, heading: Double)]] = [:]
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
                let cell = self.cell(Coordinate(latitude: lat, longitude: lon), anchor: anchor,
                                     metersPerDegreeLon: metersPerDegreeLon)
                // The grid is an INDEX, not the measurement.
                //
                // Asking only "was an earlier sample in this same cell" makes the verdict depend on where
                // the cell boundaries happen to fall. reviewer-pr76 swept one fixed connector and got three
                // answers from the same road - 0 m and 6 m rejected at f = 0.498, 12 m ACCEPTED at f = 0.0 -
                // because the two carriageways landed either side of a boundary. Reversing a route did the
                // same thing.
                //
                // Two fixes were tried and this suite rejected both. Offsetting the grid by half a cell does
                // not work: carriageways 14 m apart are 0.56 of a 25 m cell apart, wider than any half-cell
                // shift, so the straddle survives every phase. Simply searching the 3x3 neighbourhood does
                // not work either: it reaches up to two cells, so a genuinely parallel street 40 m away
                // started reading as the same road, which is the honest-loop false positive.
                //
                // So the neighbourhood is searched to FIND candidates - every earlier sample within 25 m is
                // guaranteed to be in one of the nine cells - and the actual distance decides. The radius is
                // then exactly `cellSizeMeters`, set by geometry rather than by where a boundary fell.
                let seen = neighbourhood.flatMap { samplesByCell[Cell(x: cell.x + $0.0, y: cell.y + $0.1)] ?? [] }
                let here = Coordinate(latitude: lat, longitude: lon)
                if seen.contains(where: { angularDifference($0.heading, heading) > oppositeHeadingDegrees
                                          && Geo.distanceMeters($0.point, here) <= cellSizeMeters }) {
                    retraced += share
                }
                // Only this sample's own cell records it. Writing `seen` back would copy every neighbour's
                // samples into this cell and they would spread further on each step.
                samplesByCell[cell, default: []].append((here, heading))
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

    /// The cell a point falls in, on one phase of a grid anchored at `anchor`.
    ///
    /// `metersPerDegreeLon` is passed in rather than derived from `p` itself. Scaling longitude at each
    /// point's own latitude would stop the grid being a grid - the columns would change width down the
    /// route - and on a route spanning under 2 km the difference is about 0.03%, far too small for any
    /// fixture here to notice while being wrong in principle.
    static func cell(_ p: Coordinate, anchor: Coordinate, metersPerDegreeLon: Double) -> Cell {
        Cell(
            x: Int(((p.longitude - anchor.longitude) * metersPerDegreeLon / cellSizeMeters).rounded(.down)),
            y: Int(((p.latitude - anchor.latitude) * metersPerDegreeLatitude / cellSizeMeters).rounded(.down))
        )
    }

    /// The nine cells a sample is compared against: its own and its eight neighbours.
    static let neighbourhood: [(Int, Int)] = [(-1, -1), (-1, 0), (-1, 1),
                                              (0, -1), (0, 0), (0, 1),
                                              (1, -1), (1, 0), (1, 1)]

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
