import Foundation
import Testing
@testable import ScenicKit

/// Whether a stretch of road is "the same road" must not depend on where the grid's boundaries happen to
/// fall. That is a separate question from the ones in `RetraceDetectorTests`, which are about the shapes a
/// plausible detector confuses, and it is the question reviewer-pr76 broke the detector with: one fixed
/// connector gave three different verdicts depending only on where it sat.
///
/// Split out because the two suites together passed the 300-line cap.
@Suite("Retrace detector grid")
struct RetraceGridTests {

    /// Near UCLA, where the developer will drive these.
    static let base = Coordinate(latitude: 34.0689, longitude: -118.4452)

    // MARK: - the grid must not decide the verdict (reviewer-pr76, findings G1 and G2)

    /// Metres per degree, as INDEPENDENT constants. Deriving these from `RetraceDetector` would make every
    /// offset below cancel against the grid it is meant to probe.
    /// Metres per degree of latitude on the SAME sphere `Geo.distanceMeters` uses: 2*pi*6_371_008.8/360.
    ///
    /// Written out as an independent literal, not read from `Geo`, but it must be the same SPHERE - because
    /// the thing that decides a retrace is haversine distance, and a fixture that lays its carriageways out
    /// on a different metre is mislabelling its own separations. The first version of the boundary sweep
    /// below used 111_132.0 (the WGS84 value at 45 degrees latitude) and a separation it called 24.99 m was
    /// really 25.004 m - past the radius, correctly not detected, and the test blamed the code. Three
    /// different metres in one test was the whole finding this file exists to close, committed one more time
    /// in the test written to close it.
    static let mPerDegLat = 111_195.080234
    static func mPerDegLon(_ lat: Double) -> Double { 111_320.0 * cos(lat * .pi / 180) }

    /// An approach leg running north for `approachMeters`, then a divided road driven out east and back west
    /// on a carriageway `separationMeters` to the north.
    ///
    /// The approach is what makes this fixture able to fail. Translating a whole route does nothing once the
    /// grid is anchored on the route's own bounding box - the grid moves with it - so a fixture that only
    /// slides sideways passes against ANY implementation, which is the defect this suite exists to catch,
    /// committed inside a test written to close it. What does vary the phase is the distance between the
    /// anchor (the southernmost point, set by the approach) and the pair of carriageways: sweeping
    /// `approachMeters` walks that pair across a row boundary.
    static func dividedOutAndBack(separationMeters: Double, approachMeters: Double) -> [Coordinate] {
        let lat0 = 34.0689
        let lon0 = -118.4452
        let stepLon = 20.0 / mPerDegLon(lat0)          // 20 m steps, east then back west
        var out: [Coordinate] = []

        // North from the anchor to the junction, in 20 m steps.
        let steps = max(1, Int(approachMeters / 20.0))
        for i in 0...steps {
            out.append(Coordinate(latitude: lat0 + (approachMeters * Double(i) / Double(steps)) / mPerDegLat,
                                  longitude: lon0))
        }
        let junction = lat0 + approachMeters / mPerDegLat
        for i in 0...40 { out.append(Coordinate(latitude: junction, longitude: lon0 + Double(i) * stepLon)) }
        for i in stride(from: 40, through: 0, by: -1) {
            out.append(Coordinate(latitude: junction + separationMeters / mPerDegLat,
                                  longitude: lon0 + Double(i) * stepLon))
        }
        return out
    }

    @Test("a divided-road out-and-back is a retrace wherever it sits on the grid")
    func verdictDoesNotDependOnGridPhase() {
        // reviewer-pr76 swept ONE fixed connector and got three answers from the same piece of road:
        // 0 m -> 0.498 (reject), 6 m -> 0.497 (reject), 12 m -> 0.0 (ACCEPT), 18 m -> 0.0, 24 m -> 0.0.
        // The grid was anchored at points[0], so shifting the road shifted the cell boundaries under it and
        // the two carriageways fell into the same column or different ones depending on nothing but phase.
        //
        // This is the product failure the whole task exists to prevent - a loop that doubles back reported
        // as acceptable - and it needed no adversarial input, just a road that starts somewhere else.
        for approach in [0.0, 60.0, 100.0, 140.0, 180.0, 215.0, 240.0, 300.0] {
            let route = Self.dividedOutAndBack(separationMeters: 14, approachMeters: approach)
            let f = RetraceDetector.retraceFraction(route)
            #expect(f != nil)
            #expect((f ?? 0) > 0.25,
                    "approach \(approach) m: retrace measured \(f ?? -1) on a route whose divided leg is driven twice")
            #expect(!RetraceDetector.isAcceptableLoop(route),
                    "approach \(approach) m: this out-and-back was accepted as a loop")
        }
    }

    @Test("reversing a divided-road out-and-back gives the same verdict")
    func reversalDoesNotMoveTheGrid() {
        // Anchoring at points[0] meant reversing the route moved the grid by the 14 m between carriageways.
        // Measured forward 0.4982149264183954, backward 0.0 - and isAcceptableLoop flipped false -> true.
        let route = Self.dividedOutAndBack(separationMeters: 14, approachMeters: 140)
        let forward = RetraceDetector.retraceFraction(route)
        let backward = RetraceDetector.retraceFraction(route.reversed())
        #expect(forward != nil && backward != nil)
        #expect(abs((forward ?? 0) - (backward ?? 0)) < 0.02,
                "forward \(forward ?? -1) vs backward \(backward ?? -1)")
        #expect(RetraceDetector.isAcceptableLoop(route) == RetraceDetector.isAcceptableLoop(route.reversed()))
    }

    @Test("a genuine loop is still accepted, so the phase fix did not just reject everything")
    func aRealLoopIsStillALoop() {
        // Taking the WORST of four grid phases can only raise the measured retrace, so it could in principle
        // turn every route into a rejection. A square circuit - four sides, no side driven twice - must
        // still pass, or the fix has bought correctness by making the check useless.
        let lat0 = 34.0689, lon0 = -118.4452
        let side = 400.0
        let dLat = side / Self.mPerDegLat, dLon = side / Self.mPerDegLon(lat0)
        var out: [Coordinate] = []
        let corners = [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)]
        for (i, c) in corners.enumerated() where i < corners.count - 1 {
            let n = corners[i + 1]
            for s in 0..<20 {
                let t = Double(s) / 20.0
                out.append(Coordinate(latitude: lat0 + (c.0 + (n.0 - c.0) * t) * dLat,
                                      longitude: lon0 + (c.1 + (n.1 - c.1) * t) * dLon))
            }
        }
        out.append(Coordinate(latitude: lat0, longitude: lon0))
        let f = RetraceDetector.retraceFraction(out)
        #expect((f ?? 1) <= 0.15, "a square circuit measured \(f ?? -1) retrace")
        #expect(RetraceDetector.isAcceptableLoop(out))
    }

    @Test("a street 40 m away is a different road, so the neighbourhood must not grow")
    func neighbourhoodIsOneCellNotTwo() {
        // The 3x3 search that fixes the boundary problem buys accuracy with reach: it now compares samples
        // up to a cell away. Widening it to 5x5 would reach 50 m and swallow a genuinely parallel street -
        // the shape of every honest short loop - so the reach needs a witness on BOTH sides.
        //
        // 40 m apart is the discriminating distance: outside 3x3's 25 m, inside 5x5's 50 m. The existing
        // parallel-street fixture sits 120 m out and passes at either width, which is why nothing caught the
        // widening mutation.
        let lat0 = 34.0689, lon0 = -118.4452
        let stepLon = 20.0 / Self.mPerDegLon(lat0)
        var pts: [Coordinate] = []
        for i in 0...40 { pts.append(Coordinate(latitude: lat0, longitude: lon0 + Double(i) * stepLon)) }
        let back = lat0 + 40.0 / Self.mPerDegLat
        for i in stride(from: 40, through: 0, by: -1) {
            pts.append(Coordinate(latitude: back, longitude: lon0 + Double(i) * stepLon))
        }
        let f = RetraceDetector.retraceFraction(pts)
        #expect((f ?? 1) < 0.15, "streets 40 m apart are different roads; measured \(f ?? -1)")
        #expect(RetraceDetector.isAcceptableLoop(pts))
    }

    @Test("an out-of-range coordinate is refused rather than trapped")
    func refusesOutOfRange() {
        // SPLIT from the 1e17 case on purpose, and reviewer-pr76's F2b is why. These two live in their own
        // test because the 1e17 case TRAPS when the range screen is removed - and a trap takes the process
        // down, so any assertion sharing a @Test with it never runs. That turned a perfectly killable
        // mutation into one the harness recorded as unkillable, which is a gap disguised as a fact.
        //
        // An ordinary out-of-range latitude does not trap; without the screen it returns 0.0 instead of nil,
        // and this objects.
        //
        // The 1e17 case that motivated the screen is NOT a fixture here, and splitting it into its own @Test
        // was not enough either: a trap takes the whole test process down, so any assertion anywhere in the
        // run is silenced with it. While that fixture existed, "drop the range screen" could only ever score
        // `trapped` - detected, but not by a check - and the harness recorded it as unkillable. The value
        // that motivated the guard lives in the guard's own documentation, where it cannot suppress a test.
        #expect(RetraceDetector.retraceFraction(
            [Self.base, Coordinate(latitude: 91.0, longitude: -118.0)]) == nil)
        #expect(RetraceDetector.retraceFraction(
            [Self.base, Coordinate(latitude: -91.0, longitude: -118.0)]) == nil)
        #expect(RetraceDetector.retraceFraction(
            [Self.base, Coordinate(latitude: 34.0, longitude: -181.0)]) == nil)
        #expect(RetraceDetector.retraceFraction(
            [Self.base, Coordinate(latitude: 34.0, longitude: 181.0)]) == nil)
    }

    @Test("a repeated coordinate does not plant a due-north sample on a southbound road")
    func duplicatedCoordinateIsNotARetrace() {
        // reviewer-pr76's F2a. `guard length.isFinite, length > 0` had never been seen red, and the harness
        // recorded it as unkillable on the reasoning that a zero-length segment "contributes a sample at a
        // point it already occupies, with the same heading". Measured, that is false:
        // Geo.initialBearingDegrees(from: a, to: a) is 0.0, NOT the segment's heading. So a duplicated
        // coordinate plants a DUE NORTH sample on a road heading due south, and the next segment's samples
        // within the radius score 180 degrees against it - a retrace invented out of a repeated point.
        //
        // Duplicated coordinates are ordinary in OSM geometry and in GPS traces, so this is a real input.
        let lat0 = 34.0689, lon0 = -118.4452
        var pts: [Coordinate] = []
        for i in 0...25 { pts.append(Coordinate(latitude: lat0 - Double(i) * 40.0 / Self.mPerDegLat,
                                                longitude: lon0)) }
        pts.insert(pts[12], at: 13)          // one point repeated, mid-route
        #expect(RetraceDetector.retraceFraction(pts) == 0.0,
                "a one-way road with a repeated point retraces nothing")
    }
    @Test("a separation just under the radius is caught at every phase, not just at 14 m")
    func radiusBoundaryIsCaughtAtEveryPhase() {
        // reviewer-pr76's F1. The previous fix searched a 3x3 neighbourhood of 25 m cells and the source
        // claimed "every earlier sample within 25 m is guaranteed to be in one of the nine cells". It was
        // not: the grid measured longitude at 111_320 m/degree while Geo.distanceMeters is haversine on
        // Geo.earthRadiusMeters = 111_195.08 m/degree, so a pair exactly 25 true metres apart read as
        // 1.001123 cells - just over one - and could land TWO columns apart, outside the search, where the
        // distance test is never asked. They measured 8 of 10001 phases flipping a retracing road to
        // ACCEPTED at a 24.99 m separation.
        //
        // verdictDoesNotDependOnGridPhase covers exactly one separation, 14 m, which is 0.56 cells and never
        // straddles. This sweeps the separation right up to the radius, which is where the guarantee is thin.
        for separation in [14.0, 20.0, 24.0, 24.9, 24.99] {
            for approach in [0.0, 37.0, 74.0, 111.0, 148.0, 185.0] {
                let route = Self.dividedOutAndBack(separationMeters: separation,
                                                                   approachMeters: approach)
                let f = RetraceDetector.retraceFraction(route)
                #expect((f ?? 0) > 0.25,
                        "separation \(separation) m, approach \(approach) m: measured \(f ?? -1)")
                #expect(!RetraceDetector.isAcceptableLoop(route),
                        "separation \(separation) m, approach \(approach) m: accepted as a loop")
            }
        }
    }

    @Test("the index cell is larger than the retrace radius, which is what makes the search complete")
    func indexCellExceedsTheRadius() {
        // The guarantee is by MARGIN, not by two scale constants happening to agree. Two points within the
        // radius differ by at most radius * (grid m/deg) / (haversine m/deg) / cell cells on each axis; with
        // the cell at twice the radius that is about 0.5006, so their floors differ by at most 1 and a 3x3
        // search always contains both. Written out as literals so shrinking the cell back to the radius -
        // which is what reintroduces the defect - fails here and says why.
        #expect(RetraceDetector.retraceRadiusMeters == 25.0)
        #expect(RetraceDetector.indexCellMeters == 50.0)
        // A POLICY margin, deliberately stricter than the guarantee. The guarantee itself needs only
        // `radius * 1.001123` and `indexNeverSeparatesAPairInsideTheRadius` stays green at 1.002x - measured,
        // not assumed. This pin exists so shrinking the cell towards that edge is a deliberate act with a
        // failing test attached, rather than something that silently still works until the constants drift.
        #expect(RetraceDetector.indexCellMeters > RetraceDetector.retraceRadiusMeters * 1.5,
                "policy margin, not the correctness edge; see indexCellMeters' own documentation")
    }

    @Test("a separation past the radius is not a retrace, so the radius is pinned from both sides")
    func pastTheRadiusIsNotRetrace() {
        // The other side of the boundary, and the reason the fix could not simply widen the search. Placed
        // with the same metre the decider uses, so the label on the number is true.
        for sep in [26.0, 30.0, 40.0] {
            for approach in [0.0, 37.0, 111.0] {
                let route = Self.dividedOutAndBack(separationMeters: sep, approachMeters: approach)
                let f = RetraceDetector.retraceFraction(route)
                #expect((f ?? 1) < 0.15,
                        "separation \(sep) m, approach \(approach) m: measured \(f ?? -1)")
            }
        }
    }
}
