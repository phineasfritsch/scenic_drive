import Foundation
import Testing
@testable import ScenicKit

/// A road that is NOT axis-aligned, which is the only shape that needs the index's four corner cells.
///
/// reviewer-sg-pr76's B1. No fixture in this repository ever separated a pair INSIDE the radius along a
/// diagonal: `dividedOutAndBack` and the 40 m street offset their two passes in latitude, the out-and-back
/// fixtures retrace themselves exactly (which lands in the same cell whatever shape the cell is), and both
/// probes in `RetraceIndexTests` were due east and due north. A pair separated along an axis differs on ONE
/// cell axis; only a diagonal separation differs on both at once. So the four corners of the 3x3
/// neighbourhood had no witness anywhere - not in the suite, not in `MUTATIONS`, not in `KNOWN_MISSED`, not
/// in `EQUIVALENT`. Deleting them (a plus-shaped neighbourhood) left all 41 tests green at exit 0 while
/// this road loses up to a third of its retrace, at some grid phases and not others: verbatim the G2
/// failure this whole task exists to prevent, moved from an axis-aligned 14 m separation to a diagonal
/// 24 m one.
///
/// `RetraceIndexTests` asks the index directly - which cells can a pair inside the radius land in, and does
/// the search visit them. This asks what that is worth to a ROUTE, which is a different question and the
/// one a product failure is actually made of. Its own file because `RetraceGridTests` is at 240 of the 300
/// lines the cap allows, and `ops/mutate/retrace.py`'s `TEST_FILES` gained this file in the SAME commit -
/// a suite the vacuity proof does not know about silently stops it emptying all the tests ([[T-0132]]).
@Suite("Retrace on a diagonal road")
struct RetraceDiagonalTests {

    /// A divided road on bearing 045: 20 m steps, 1200 m out and 1200 m back, the return carriageway 24 m
    /// PERPENDICULAR to the road (north-west of it) rather than offset in latitude.
    ///
    /// Everything is placed by bisecting on `Geo.distanceMeters` - the probe `RetraceIndexTests` uses,
    /// referenced rather than copied so a second one cannot drift - so the 20 m and 24 m labels are the
    /// decider's own metres. A fixture that lays itself out on some other metres-per-degree constant and
    /// then calls its separation 24 m is this file's own history: the last round's sweep labelled a
    /// separation 24.99 m when it was really 25.004 m, past the radius, and blamed the code for not
    /// detecting it.
    ///
    /// `approachMeters` runs north into the junction before the diagonal starts. Translating the whole
    /// route does nothing - the grid is anchored on the route's own bounding box, so it moves with it - but
    /// lengthening the approach moves the diagonal pair relative to that anchor, which walks the phase.
    static func diagonalDividedOutAndBack(approachMeters: Double) -> [Coordinate] {
        let junction = Coordinate(latitude: 34.0689, longitude: -118.4452)
        // A RATIO, not a metre: `northUnits = cos(lat)` against `eastUnits = 1` is what makes the bearing
        // 045 rather than 040. The LENGTH of every offset below still comes from the bisection.
        let k = cos(junction.latitude * .pi / 180)
        func delta(north: Double, east: Double, meters: Double) -> (dLat: Double, dLon: Double) {
            let p = RetraceIndexTests.point(from: junction, northUnits: north, eastUnits: east,
                                            meters: meters)
            return (p.latitude - junction.latitude, p.longitude - junction.longitude)
        }
        let out = delta(north: k, east: 1, meters: 20)          // 20 m on bearing 045
        let north = delta(north: 1, east: 0, meters: 20)        // the approach leg, due north
        let side = delta(north: k, east: -1, meters: 24)        // 24 m on bearing 315

        var pts: [Coordinate] = []
        let steps = Int((approachMeters / 20).rounded(.up))
        for i in stride(from: steps, through: 1, by: -1) {
            let back = approachMeters * Double(i) / Double(steps) / 20
            pts.append(Coordinate(latitude: junction.latitude - north.dLat * back,
                                  longitude: junction.longitude - north.dLon * back))
        }
        for i in 0...60 {
            pts.append(Coordinate(latitude: junction.latitude + out.dLat * Double(i),
                                  longitude: junction.longitude + out.dLon * Double(i)))
        }
        for i in stride(from: 60, through: 0, by: -1) {
            pts.append(Coordinate(latitude: junction.latitude + out.dLat * Double(i) + side.dLat,
                                  longitude: junction.longitude + out.dLon * Double(i) + side.dLon))
        }
        return pts
    }

    @Test("a divided road on a diagonal is retrace at every phase, corner cells included")
    func diagonalDividedRoadIsRetraceAtEveryPhase() {
        // The fixture asserts what it IS, measured by the decider, before anything is concluded from it.
        let r = Self.diagonalDividedOutAndBack(approachMeters: 0)
        #expect(abs(Geo.distanceMeters(r[0], r[1]) - 20) < 1e-6,
                "step is \(Geo.distanceMeters(r[0], r[1])) m, not 20")
        #expect(abs(Geo.initialBearingDegrees(from: r[0], to: r[1]) - 45) < 0.001,
                "bearing is \(Geo.initialBearingDegrees(from: r[0], to: r[1])), not 045")
        // 0.01 m rather than 1e-6: the perpendicular offset is one constant pair of degrees applied at
        // every point, and a degree of longitude shortens by 0.01% over the 848 m of latitude this leg
        // climbs. The label is true to a centimetre, which is what the 25 m radius needs it to be.
        #expect(abs(Geo.distanceMeters(r[60], r[61]) - 24) < 0.01,
                "carriageways are \(Geo.distanceMeters(r[60], r[61])) m apart, not 24")

        // Every sample on the return leg has an outbound sample within 25 m and 180 degrees against it, so
        // the retrace is the return leg's share of the route: 1200 / (2400 + approach). Measured, every
        // phase below sits within 0.005 of that. With the four corner cells deleted the same road measures
        // 0.32 to 0.39 at four of these twelve phases - a third of a real road's retrace gone, and only at
        // some phases, which is what makes it the kind of defect that ships.
        for approach in [0.0, 20, 40, 60, 80, 100, 120, 140, 160, 180, 220, 260] {
            let route = Self.diagonalDividedOutAndBack(approachMeters: approach)
            let f = RetraceDetector.retraceFraction(route)
            let expected = 1200.0 / (2400.0 + approach)
            #expect(abs((f ?? 0) - expected) < 0.02,
                    "approach \(approach) m: measured \(f ?? -1) retrace, not \(expected)")
            #expect(!RetraceDetector.isAcceptableLoop(route),
                    "approach \(approach) m: this diagonal out-and-back was accepted as a loop")
        }
    }
}
