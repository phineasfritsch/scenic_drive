import Foundation

/// How much of a loop is the same road driven twice, in opposite directions.
///
/// "Just drive 45 minutes and come back" is a paid feature, and the thing that ruins it is a route that goes
/// out along a road and returns along the same road. GraphHopper's `round_trip` produces those regularly -
/// it optimises for a distance target, and out-and-back is the cheapest way to hit one. So the check is
/// ours, applied to the returned geometry, and a route that fails it is reseeded rather than shown.
///
/// The plan's parameters: **25 m cells, heading delta > 150 degrees, retrace at most 15% of length.**
///
/// The plan says both `< 15%` (in the engine section) and `<= 0.15` (in the property table). reviewer-pr76
/// found the code doing `<=` under a doc comment saying `<`. `<=` is kept - it is the number the property
/// table will be checked against - and the prose is corrected here rather than the behaviour, because
/// silently tightening a product threshold to match a comment is the larger change. The boundary is pinned
/// by `exactlyTheThresholdIsAcceptable` through `isAcceptable(fraction:)`, which exists because a test that
/// can only reach the comparison through a route fixture cannot reach it at 0.15 at all.
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
    /// How close two passes must come before they can count as the same road. The plan's 25 m.
    ///
    /// This is the PRODUCT decision and it is measured with `Geo.distanceMeters`, the same haversine the rest
    /// of the app uses. The grid below is only an index for finding candidates.
    public static let retraceRadiusMeters = 25.0

    /// The index grid's cell size. An implementation detail, and **deliberately larger than the radius**.
    ///
    /// reviewer-pr76 found the reason. The grid measures longitude at 111_320 m/degree while
    /// `Geo.distanceMeters` is haversine on `Geo.earthRadiusMeters`, which works out at 111_195.08 m/degree -
    /// so the grid's metre is 0.1123% short and a pair exactly 25 true metres apart reads as **1.001123
    /// cells**. Just over one. Two such points can therefore fall TWO columns apart, outside a 3x3 search,
    /// where the distance test is never asked - and they measured it: with the road held fixed and only the
    /// anchor moving, 8 of 10001 phases flipped a retracing out-and-back to ACCEPTED. That is verbatim the
    /// defect this type exists to prevent, relocated from a 14 m separation to a 24.99 m one.
    ///
    /// The guarantee now holds by margin rather than by the two scales happening to agree. With the cell at
    /// twice the radius, two points within `retraceRadiusMeters` differ by at most
    /// `25 x 1.001123 / 50 = 0.5006` cells on each axis, so their floors differ by at most 1 and the 3x3
    /// neighbourhood always contains both - and it would still hold if the two scales disagreed by up to a
    /// factor of two. A guarantee that depends on a constant somewhere else being close enough is not a
    /// guarantee; this one does not.
    ///
    /// **The minimum that works is `radius * 1.001123`, not `2 * radius`**, and that was measured rather
    /// than assumed: `indexNeverSeparatesAPairInsideTheRadius` goes red at `cell == radius` and stays green
    /// at `1.002 * radius`. The factor of two is headroom against the scales drifting further apart, not the
    /// edge of correctness - which matters, because somebody shrinking this constant will find the
    /// guarantee test still green well below 2x and should know that is expected.
    ///
    /// Only the EAST axis can break it. The grid's longitude metre (111_320) is LARGER than the decider's
    /// (111_195.08), so the grid thinks an east-west pair is further apart than it is and can push it over
    /// a boundary. The grid's latitude metre (111_132) is SMALLER, so a north-south pair reads SHORT and
    /// never straddles two. A test that only walked north would be green against every version of this
    /// defect.
    ///
    /// The unit in that sentence used to be wrong, and it is the unit this whole comment turns on. It read
    /// "a north-south pair reads as 0.999433 cells" while the cell is TWICE the radius. Measured, with the
    /// decider's 111_195.080234 m/degree: a 25 m north-south pair spans 24.985818 grid metres - 0.999433 of
    /// the RADIUS and 0.499716 of the 50 m cell; its east-west twin spans 25.028086 - 1.001123 of the radius
    /// and 0.500562 of the cell. The paragraph above uses CELLS (0.5006), the F1 paragraph uses the old grid
    /// where the cell WAS the radius (1.001123), and this one silently used neither. Both readings are under
    /// one cell, which is why the conclusion survived the wrong number - and why nothing here caught it.
    static let indexCellMeters = 2 * retraceRadiusMeters

    /// Degrees. Above this the two passes are heading opposite ways rather than merely crossing.
    public static let oppositeHeadingDegrees = 150.0

    /// A loop may be this much retrace and no more. Inclusive: exactly this much is acceptable.
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

            let steps = max(1, Int((length / (retraceRadiusMeters / samplesPerCell)).rounded(.up)))
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
                // then exactly `retraceRadiusMeters`, set by geometry rather than by where a boundary fell.
                let seen = neighbourhood.flatMap { samplesByCell[Cell(x: cell.x + $0.0, y: cell.y + $0.1)] ?? [] }
                let here = Coordinate(latitude: lat, longitude: lon)
                if seen.contains(where: { angularDifference($0.heading, heading) > oppositeHeadingDegrees
                                          && Geo.distanceMeters($0.point, here) <= retraceRadiusMeters }) {
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
        return isAcceptable(fraction: f)
    }

    /// The threshold decision on its own: is this much retrace acceptable?
    ///
    /// Split out of `isAcceptableLoop` so the `<=` has a witness. reviewer-fn-pr76's N3: the test named
    /// `exactlyTheThresholdIsAcceptable` asserted `0.15 <= maxRetraceFraction`, which is the line above it
    /// restated and says nothing about this comparison - so `<=` here could be changed to `<` and the whole
    /// suite stayed green at exit 0 with zero failing names. No route fixture can close that, because no
    /// fraction computed from a geometry lands on 0.15 exactly; the predicate has to be reachable on its own
    /// for the boundary to be testable at all.
    ///
    /// Internal rather than public: `isAcceptableLoop` is still the whole API, and nothing outside this
    /// module should be asking about a bare fraction.
    static func isAcceptable(fraction f: Double) -> Bool {
        f <= maxRetraceFraction
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
            x: Int(((p.longitude - anchor.longitude) * metersPerDegreeLon / indexCellMeters).rounded(.down)),
            y: Int(((p.latitude - anchor.latitude) * metersPerDegreeLatitude / indexCellMeters).rounded(.down))
        )
    }

    /// The nine cells a sample is compared against: its own and its eight neighbours.
    ///
    /// The four CORNERS are the part that is load-bearing for a road which is not due north or due east: a
    /// pair on an axis differs on one cell axis, a pair on a diagonal differs on both at once. Witnessed by
    /// `theSearchCoversEveryCellAPairCanLandIn` (every offset a pair inside the radius can take is one of
    /// these nine, and all four diagonal offsets do occur) and by `RetraceDiagonalTests` (deleting them
    /// costs a divided road on bearing 045 up to a third of its retrace, at some grid phases and not
    /// others). Nothing pinned them until reviewer-sg-pr76 asked for it.
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
