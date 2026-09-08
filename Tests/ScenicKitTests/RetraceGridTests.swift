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
    static let mPerDegLat = 111_132.0
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
        // Finiteness was screened; range was not. 1e17 is finite, and the cell arithmetic trapped with
        // "Double value cannot be converted to Int because the result would be greater than Int.max".
        #expect(RetraceDetector.retraceFraction(
            [Self.base, Coordinate(latitude: 34.0689, longitude: 1e17)]) == nil)
        #expect(RetraceDetector.retraceFraction(
            [Self.base, Coordinate(latitude: 91.0, longitude: -118.0)]) == nil)
        #expect(RetraceDetector.retraceFraction(
            [Self.base, Coordinate(latitude: 34.0, longitude: -181.0)]) == nil)
    }
}
