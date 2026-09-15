import Foundation
import Testing
@testable import ScenicKit

/// The INDEX, asked directly rather than through route outcomes.
///
/// `RetraceGridTests` asks what verdict a route gets. This asks the question underneath it: can the grid
/// used to find candidates ever separate a pair that the distance test would have accepted? That is a
/// property of two constants and a floor division, and it is answered by constructing the worst grid phase -
/// not by driving fixtures past it and hoping to land on the 0.1123% of phases where it breaks.
///
/// Split out because the two questions together passed the 300-line cap. The mutation harness's TEST_FILES
/// was updated in the same commit: a suite split the vacuity proof does not know about silently stops it
/// emptying all the tests, which has happened five times in this repository (T-0132).
@Suite("Retrace index")
struct RetraceIndexTests {

    /// Near UCLA, where the developer will drive these.
    static let base = Coordinate(latitude: 34.0689, longitude: -118.4452)

    /// A point exactly `meters` TRUE metres from `origin`, found by bisecting on `Geo.distanceMeters` -
    /// the same function that decides a retrace.
    ///
    /// Not computed from any metres-per-degree constant, and that is the whole point. The previous version
    /// of the probe below placed its east point at `radius / (111_320 * cos(lat))` and then handed
    /// `cell()` the same `111_320 * cos(lat)`; the division and the multiplication cancel EXACTLY, so the
    /// assertion held for any value of either constant and the test passed against the very defect it was
    /// written to catch. It was also placing the pair 24.972 m apart while calling it 25 - just outside the
    /// 28 mm band the finding is about.
    ///
    /// The rule was already written out for `mPerDegLat` two declarations above ("deriving these from
    /// RetraceDetector would make every offset below cancel against the grid it is meant to probe"), and
    /// then broken one line later for `mPerDegLon`. Measuring with the decider is the only form of this
    /// probe that cannot cancel.
    static func point(from origin: Coordinate, northUnits: Double, eastUnits: Double,
                      meters: Double) -> Coordinate {
        func at(_ t: Double) -> Coordinate {
            Coordinate(latitude: origin.latitude + northUnits * t,
                       longitude: origin.longitude + eastUnits * t)
        }
        var lo = 0.0, hi = 1e-6
        while Geo.distanceMeters(origin, at(hi)) < meters { hi *= 2 }
        for _ in 0..<200 {
            let mid = (lo + hi) / 2
            if Geo.distanceMeters(origin, at(mid)) < meters { lo = mid } else { hi = mid }
        }
        return at((lo + hi) / 2)
    }

    @Test("two points a radius apart are never more than one cell apart, at the WORST grid phase")
    func indexNeverSeparatesAPairInsideTheRadius() {
        // The guarantee, tested at the phase CONSTRUCTED to break it rather than sampled in the hope of
        // landing on it.
        //
        // Why construction and not a sweep. At `indexCellMeters == retraceRadiusMeters` a pair a radius
        // apart reads as 1.001123 cells, so their floors differ by 2 only when the first one's fractional
        // position is >= 0.998877 - a band 0.1123% of a cell wide. My previous version swept 400 phases,
        // which resolves 0.25%, so it stepped straight over the band and passed against the very defect it
        // was written for. Sampling for a band narrower than the step is not a test, it is a lottery.
        //
        // Only the EAST axis is at risk, and that asymmetry is the shape of the bug: the grid's longitude
        // metre (111_320) is LARGER than the decider's (111_195.08), so the grid thinks an east-west pair is
        // further apart than it is and can push it over a boundary. The grid's latitude metre (111_132) is
        // SMALLER, so a north-south pair reads as 0.999433 cells and can never straddle two. A test that
        // only walked north would be green against every version of this defect.
        let lat0 = 34.0689, lon0 = -118.4452
        let radius = RetraceDetector.retraceRadiusMeters
        let cell = RetraceDetector.indexCellMeters
        let a = Coordinate(latitude: lat0, longitude: lon0)
        let east = Self.point(from: a, northUnits: 0, eastUnits: 1, meters: radius)
        let north = Self.point(from: a, northUnits: 1, eastUnits: 0, meters: radius)

        // The fixture asserts what it IS, measured by the decider, before anything is concluded from it. The
        // previous version placed its pair 24.972 m apart while calling it 25 - just outside the band it was
        // hunting - because the probe cancelled against the grid's own constant.
        #expect(abs(Geo.distanceMeters(a, east) - radius) < 1e-6,
                "east probe is \(Geo.distanceMeters(a, east)) m, not \(radius)")
        #expect(abs(Geo.distanceMeters(a, north) - radius) < 1e-6,
                "north probe is \(Geo.distanceMeters(a, north)) m, not \(radius)")

        // The grid's own longitude metre, written independently. This is an INPUT to `cell()`, and it is
        // what the anchor phase is expressed in - it is not a source for the probe above.
        let mPerLon = 111_320.0 * cos(lat0 * .pi / 180)

        // Place the anchor so that `a` sits at fractional position `f` inside its cell, for the handful of
        // f values that matter: just below a boundary is where a pair slightly over one cell wide splits.
        func worstSeparation(f: Double) -> (x: Int, y: Int) {
            let anchor = Coordinate(latitude: lat0 - f * cell / 111_195.080234,
                                    longitude: lon0 - f * cell / mPerLon)
            let ca = RetraceDetector.cell(a, anchor: anchor, metersPerDegreeLon: mPerLon)
            let cE = RetraceDetector.cell(east, anchor: anchor, metersPerDegreeLon: mPerLon)
            let cN = RetraceDetector.cell(north, anchor: anchor, metersPerDegreeLon: mPerLon)
            return (abs(cE.x - ca.x), abs(cN.y - ca.y))
        }

        var worstX = 0, worstY = 0
        // The constructed worst phases, then a fine sweep as well - the sweep cannot be the only instrument,
        // but it costs nothing and covers phases the construction did not anticipate.
        var phases: [Double] = [0.0, 0.5, 0.9, 0.99, 0.999, 0.9999, 0.99999, 0.999999]
        phases += (0..<5000).map { Double($0) / 5000.0 }
        for f in phases {
            let d = worstSeparation(f: f)
            worstX = max(worstX, d.x)
            worstY = max(worstY, d.y)
        }
        #expect(worstX <= 1, "east-west: a pair \(radius) m apart landed \(worstX) cells apart")
        #expect(worstY <= 1, "north-south: a pair \(radius) m apart landed \(worstY) cells apart")
    }

    @Test("every cell a pair inside the radius can land in is one the index actually searches")
    func theSearchCoversEveryCellAPairCanLandIn() {
        // reviewer-pr76's B1. The test above asserts the BOUND - that neither axis separates by more than
        // one cell - and stops there. The guarantee the source claims is stronger: that the search VISITS
        // the cell the pair landed in. On a road that is not due north or due east the two cells differ on
        // BOTH axes at once, and nothing exercised a corner: both probes above are axis-aligned, and so is
        // every route fixture in this repository (`dividedOutAndBack` separates its carriageways in
        // latitude only). Replacing the nine cells with a plus - the four sides, no corners - left all 41
        // tests green at exit 0 while a divided road on bearing 045 lost up to a third of its retrace.
        //
        // So this asks BOTH halves. Every offset that can occur must be searched, and the four diagonal
        // offsets must occur - an assertion over a set that never contains a corner would be green against
        // exactly the mutation it is written for, which is this file's own history twice over.
        let lat0 = 34.0689, lon0 = -118.4452
        let radius = RetraceDetector.retraceRadiusMeters
        let cell = RetraceDetector.indexCellMeters
        let a = Coordinate(latitude: lat0, longitude: lon0)
        let mPerLon = 111_320.0 * cos(lat0 * .pi / 180)

        // 24 bearings, each placed by bisecting on `Geo.distanceMeters`. `eastUnits` carries a 1/cos(lat)
        // RATIO so the bearings come out evenly spread rather than bunched about east and west; the LENGTH
        // still comes from the decider, so no metres-per-degree constant enters the probe and there is
        // nothing here to cancel against the grid being probed.
        let k = cos(lat0 * .pi / 180)
        var probes: [(bearing: Double, point: Coordinate)] = []
        for i in 0..<24 {
            let theta = Double(i) * 15.0 * .pi / 180
            let p = Self.point(from: a, northUnits: cos(theta), eastUnits: sin(theta) / k, meters: radius)
            #expect(abs(Geo.distanceMeters(a, p) - radius) < 1e-6,
                    "probe \(i) is \(Geo.distanceMeters(a, p)) m from the origin, not \(radius)")
            probes.append((Geo.initialBearingDegrees(from: a, to: p), p))
        }

        // The two axes' phases are swept INDEPENDENTLY. A corner needs the pair to straddle a column
        // boundary and a row boundary at the same time, and one f moving both anchors together cannot
        // produce that - with a single f this set comes out as the five cells of a plus, and the test would
        // pass against the very mutation it exists for.
        var phases: [Double] = [0.0, 0.001, 0.5, 0.9, 0.99, 0.999, 0.9999, 0.99999, 0.999999]
        phases += (0..<40).map { Double($0) / 40.0 }
        var witness: [RetraceDetector.Cell: Double] = [:]
        for fx in phases {
            for fy in phases {
                let anchor = Coordinate(latitude: lat0 - fy * cell / 111_195.080234,
                                        longitude: lon0 - fx * cell / mPerLon)
                let ca = RetraceDetector.cell(a, anchor: anchor, metersPerDegreeLon: mPerLon)
                for probe in probes {
                    let c = RetraceDetector.cell(probe.point, anchor: anchor, metersPerDegreeLon: mPerLon)
                    witness[RetraceDetector.Cell(x: c.x - ca.x, y: c.y - ca.y)] = probe.bearing
                }
            }
        }

        for (offset, bearing) in witness.sorted(by: { ($0.key.x, $0.key.y) < ($1.key.x, $1.key.y) }) {
            #expect(RetraceDetector.neighbourhood.contains(where: { $0 == (offset.x, offset.y) }),
                    """
                    a pair \(radius) m apart on bearing \(Int(bearing.rounded())) landed at cell \
                    offset (\(offset.x), \(offset.y)), which the index does not search
                    """)
        }
        for (dx, dy) in [(-1, -1), (-1, 1), (1, -1), (1, 1)] {
            #expect(witness[RetraceDetector.Cell(x: dx, y: dy)] != nil,
                    """
                    no pair inside the radius ever landed at diagonal offset (\(dx), \(dy)), so the \
                    assertion above says nothing about the corner cells
                    """)
        }
    }
}
