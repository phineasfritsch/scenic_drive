import Foundation
import Testing
@testable import ScenicKit

/// A loop that drives out and back along the same road is the failure mode of `round_trip`, not an exotic
/// case: the engine optimises for a distance target and out-and-back is the cheapest way to hit one. So
/// these tests are mostly about the shapes that fool a plausible implementation - a crossroads, a parallel
/// street one block over, a road that runs through north, and a way drawn as one long straight segment.
@Suite("Retrace detector")
struct RetraceDetectorTests {

    /// Near UCLA, where the developer will drive these.
    static let base = Coordinate(latitude: 34.0689, longitude: -118.4452)

    /// A straight run of `count` points `spacing` metres apart on a bearing.
    static func line(from start: Coordinate, bearing: Double, spacing: Double,
                     count: Int) -> [Coordinate] {
        let rad = bearing * .pi / 180
        let dLat = cos(rad) * spacing / 111_132.0
        let dLon = sin(rad) * spacing / (111_320.0 * cos(start.latitude * .pi / 180))
        return (0..<count).map {
            Coordinate(latitude: start.latitude + dLat * Double($0),
                       longitude: start.longitude + dLon * Double($0))
        }
    }

    // MARK: - the thing it is for

    @Test("a road driven out and back is almost entirely retrace")
    func outAndBackIsRetrace() throws {
        let out = Self.line(from: Self.base, bearing: 0, spacing: 50, count: 40)   // 1.95 km north
        let there = out + out.reversed()
        let f = try #require(RetraceDetector.retraceFraction(there))
        #expect(f > 0.45, "half the length is the return leg; it was \(f)")
        #expect(!RetraceDetector.isAcceptableLoop(there))
    }

    @Test("a genuine loop that returns by a different road is not retrace")
    func realLoopIsClean() throws {
        // A square: north, east, south, west, back to the start. Every leg is a different road.
        var pts = Self.line(from: Self.base, bearing: 0, spacing: 50, count: 20)
        pts += Self.line(from: pts.last!, bearing: 90, spacing: 50, count: 20).dropFirst()
        pts += Self.line(from: pts.last!, bearing: 180, spacing: 50, count: 20).dropFirst()
        pts += Self.line(from: pts.last!, bearing: 270, spacing: 50, count: 20).dropFirst()
        let f = try #require(RetraceDetector.retraceFraction(pts))
        #expect(f < RetraceDetector.maxRetraceFraction, "a square loop retraced \(f)")
        #expect(RetraceDetector.isAcceptableLoop(pts))
    }

    @Test("crossing your own path is not retracing it")
    func crossingIsNotRetrace() throws {
        // A figure that crosses itself at right angles. The headings differ by 90 degrees, which is a
        // junction, not a road driven twice. A detector that only asked "have I been in this cell before"
        // would call this a retrace and reject every loop that crosses a main road.
        let eastWest = Self.line(from: Self.base, bearing: 90, spacing: 50, count: 30)
        let mid = eastWest[15]
        let southNorth = Self.line(from: Coordinate(latitude: mid.latitude - 0.006,
                                                    longitude: mid.longitude),
                                   bearing: 0, spacing: 50, count: 30)
        let f = try #require(RetraceDetector.retraceFraction(eastWest + southNorth))
        #expect(f < 0.05, "a crossing is not a retrace; got \(f)")
    }

    @Test("a parallel street one block over is a different road")
    func parallelStreetIsNotRetrace() throws {
        // Up one street, across a block, back down the next: the shape of every honest short loop.
        //
        // Built as ONE CONTINUOUS ROUTE, which the first version was not. It concatenated a northbound line
        // with a southbound line starting 120 m east, and concatenation inserts an implicit segment between
        // them - a 1.4 km diagonal running back over the outbound leg at a heading 175 degrees off it. That
        // connector, not the parallel streets, produced 6.9% retrace and failed the assertion. The detector
        // was right; the fixture described a route no car could drive.
        let blockMeters = 120.0
        var pts = Self.line(from: Self.base, bearing: 0, spacing: 50, count: 30)          // 1450 m north
        pts += Self.line(from: pts.last!, bearing: 90, spacing: 40,
                         count: Int(blockMeters / 40) + 1).dropFirst()                    // across the block
        pts += Self.line(from: pts.last!, bearing: 180, spacing: 50, count: 30).dropFirst()  // back south

        let f = try #require(RetraceDetector.retraceFraction(pts))
        #expect(f < 0.05, "streets a block apart are not the same road; got \(f)")
        #expect(RetraceDetector.isAcceptableLoop(pts))
    }

    // MARK: - the three easy mistakes

    @Test("the heading comparison wraps, so a road through north is not a retrace of itself")
    func headingComparisonWraps() {
        // `abs(a - b)` calls 350 and 010 - twenty degrees apart, the same direction - a 340 degree
        // difference, which is "more opposite than opposite". This repository already contains that bug
        // deliberately in curvature.py to match a published oracle, which is a reason to be sure it is not
        // here by accident.
        #expect(RetraceDetector.angularDifference(350, 10) == 20)
        #expect(RetraceDetector.angularDifference(10, 350) == 20)
        #expect(RetraceDetector.angularDifference(0, 180) == 180)
        #expect(RetraceDetector.angularDifference(90, 270) == 180)
        #expect(RetraceDetector.angularDifference(359, 1) == 2)
        #expect(RetraceDetector.angularDifference(45, 45) == 0)
    }

    @Test("a road that runs through north and back is still detected")
    func retraceAcrossNorth() throws {
        // Out on 355, back on 175. A naive `abs(355 - 175) = 180` happens to work here, so the fixture is
        // out on 010 and back on 190 as well, where naive gives 180 too - and out on 350 back on 010, a
        // continuation, where naive gives 340 and would wrongly call it a retrace.
        let out = Self.line(from: Self.base, bearing: 355, spacing: 50, count: 30)
        let f = try #require(RetraceDetector.retraceFraction(out + out.reversed()))
        #expect(f > 0.45)

        // A road bending gently through north: 350 then 010. Same direction, must not be a retrace.
        let leg1 = Self.line(from: Self.base, bearing: 350, spacing: 50, count: 20)
        let leg2 = Self.line(from: leg1.last!, bearing: 10, spacing: 50, count: 20).dropFirst()
        let g = try #require(RetraceDetector.retraceFraction(leg1 + leg2))
        #expect(g < 0.05, "a bend through north is not a retrace; got \(g)")
    }

    @Test("a long straight segment is sampled along its length, not just at its midpoint")
    func longSegmentsAreSampled() throws {
        // OSM draws some ways as a single segment hundreds of metres long. Recording only the midpoint puts
        // 500 m into one 25 m cell.
        //
        // The obvious fixture - one 500 m segment out, one straight back - does NOT catch this, and that
        // was the first version. With one sample per segment, both midpoints land in the same cell with
        // opposite headings, the whole return segment is attributed as retrace, and the fraction is 0.5
        // either way. The bug is invisible because the mis-attribution happens to be the right size.
        //
        // The fixture that separates them: out as ONE 600 m segment, back as THREE 200 m segments. Midpoint
        // sampling puts the outbound sample at 300 m and the return samples at 500, 300 and 100 m - so only
        // the middle one collides, giving 200 of 1200 m. Sampling along the length sees the whole overlap.
        let out = Self.line(from: Self.base, bearing: 0, spacing: 600, count: 2)      // one 600 m segment
        let back = Self.line(from: out[1], bearing: 180, spacing: 200, count: 4)      // three 200 m segments
        let f = try #require(RetraceDetector.retraceFraction(out + back.dropFirst()))
        #expect(f > 0.45, "the return leg retraces the whole outbound segment; got \(f)")
    }

    @Test("every pass through a cell is remembered, not just the first")
    func allHeadingsAreRecorded() throws {
        // Cross a road, drive up a dead-end, come back down it. The cell at the junction is first entered
        // heading east, then north, then south. Keeping only the FIRST heading compares the southbound pass
        // against 90 degrees - a 90 degree difference, under the threshold - and the out-and-back on the
        // dead-end is missed entirely. Keeping all of them compares it against 0 as well, which is 180.
        // Three passes over one road: out, back, out again. That is what a reseeded loop looks like when
        // the router keeps returning the same corridor, and it is where keeping only the first heading
        // shows up.
        //
        // With every heading recorded, pass 2 (180) is retrace against pass 1 (0), and pass 3 (0) is
        // retrace against pass 2 (180) - about two thirds of the length. Keeping only the first heading,
        // pass 3 is compared against 0 alone, matches nobody, and reads as fresh road: about one third.
        //
        // The first version of this test used a junction crossed once at 90 degrees before a two-pass
        // spur, which distinguished nothing: the spur's own cells still had 0 as their first heading, so
        // the return pass was caught either way, and the single junction cell was too small to move the
        // fraction.
        let road = Self.line(from: Self.base, bearing: 0, spacing: 40, count: 16)     // 600 m north
        var pts = road
        pts += road.reversed().dropFirst()
        pts += road.dropFirst()

        let f = try #require(RetraceDetector.retraceFraction(pts))
        #expect(f > 0.55, "two of the three passes are retrace; got \(f)")
        #expect(!RetraceDetector.isAcceptableLoop(pts))
    }

    @Test("cells are square in metres, at every latitude")
    func cellsAreSquare() {
        // Asked of the grid directly, because no route fixture can see this. An exact out-and-back lands in
        // the same cell whatever shape the cell is, so the obvious test - drive a route at three latitudes
        // and check the verdict - passes with the latitude correction deleted. That was the first version.
        //
        // The real failure of an equatorial constant: at latitude 60 the columns become 12.5 m wide instead
        // of 25, so a road driven out and back with any lateral offset (opposite carriageways, GPS jitter)
        // lands in different columns and the retrace is missed entirely.
        // The probe offsets are computed from an INDEPENDENT constant, not from the function under test.
        // The first version placed the east probe at `origin.longitude + d / metersPerDegreeLongitude(at:)`
        // and then `cell()` multiplied that offset back by the same function - the two uses cancel exactly,
        // so `cN.y == cE.x` held for ANY definition of it, including a constant. A second reviewer found
        // that: the test written to catch a self-referential assertion was itself one.
        let metersPerDegreeLonReference = { (lat: Double) in 111_320.0 * cos(lat * .pi / 180) }

        for lat in [0.0, 34.0689, 60.0, -45.0] {
            let origin = Coordinate(latitude: lat, longitude: -118.4452)
            let d = 30.0                                   // metres, more than one 25 m cell
            let north = Coordinate(latitude: lat + d / 111_132.0, longitude: origin.longitude)
            let east = Coordinate(latitude: lat,
                                  longitude: origin.longitude + d / metersPerDegreeLonReference(lat))
            // The scale handed to `cell` is the FUNCTION UNDER TEST, while the probe offsets above come
            // from `metersPerDegreeLonReference`. Passing the reference constant here as well would make
            // the two uses cancel again and pin nothing - which is the exact defect a second reviewer
            // found in the first version of this test.
            let scale = RetraceDetector.metersPerDegreeLongitude(at: lat)
            let cN = RetraceDetector.cell(north, anchor: origin, metersPerDegreeLon: scale)
            let cE = RetraceDetector.cell(east, anchor: origin, metersPerDegreeLon: scale)
            // 30 m north and 30 m east must be the same number of cells away, or the grid is not square.
            #expect(cN.y == cE.x, "at latitude \(lat): \(d) m north is \(cN.y) cells, east is \(cE.x)")
            #expect(cN.y == 1, "30 m should be one 25 m cell away, got \(cN.y)")
            #expect(cE.x == 1, "and so should 30 m east, got \(cE.x)")
        }
    }

    @Test("a latitude correction that is actually applied")
    func longitudeScaleShrinksWithLatitude() {
        // Pins the mechanism the grid depends on, so replacing it with the equatorial constant is caught
        // even though no route fixture can distinguish the two.
        let equator = RetraceDetector.metersPerDegreeLongitude(at: 0)
        let la = RetraceDetector.metersPerDegreeLongitude(at: 34.0689)
        let far = RetraceDetector.metersPerDegreeLongitude(at: 60)
        #expect(abs(equator - 111_320) < 1)
        #expect(la < equator * 0.85, "a degree of longitude is ~92 km at Los Angeles, got \(la)")
        #expect(abs(far - equator / 2) < 500, "cos(60) is exactly 0.5, got \(far)")
    }

    // MARK: - invariance and refusals

    @Test("driving the loop the other way round gives the same answer")
    func reversalInvariant() throws {
        var pts = Self.line(from: Self.base, bearing: 0, spacing: 50, count: 20)
        pts += Self.line(from: pts.last!, bearing: 90, spacing: 50, count: 20).dropFirst()
        pts += Self.line(from: pts.last!, bearing: 200, spacing: 50, count: 25).dropFirst()
        let forward = try #require(RetraceDetector.retraceFraction(pts))
        let backward = try #require(RetraceDetector.retraceFraction(pts.reversed()))
        #expect(abs(forward - backward) < 0.02, "\(forward) vs \(backward)")
    }

    @Test("a route with no length has no retrace fraction")
    func degenerateIsNil() {
        #expect(RetraceDetector.retraceFraction([]) == nil)
        #expect(RetraceDetector.retraceFraction([Self.base]) == nil)
        // Two identical points: zero length, so there is no fraction of anything.
        #expect(RetraceDetector.retraceFraction([Self.base, Self.base]) == nil)
        // And an unacceptable loop rather than a crash.
        #expect(!RetraceDetector.isAcceptableLoop([]))
    }

    @Test("a non-coordinate is refused rather than quantised")
    func refusesNonsense() {
        let bad = Coordinate(latitude: .nan, longitude: -118.0)
        #expect(RetraceDetector.retraceFraction([Self.base, bad]) == nil)
        #expect(RetraceDetector.retraceFraction([Self.base, Coordinate(latitude: 34.0, longitude: .infinity)]) == nil)
    }

    @Test("the threshold constants are the plan's, written out")
    func constantsArePinned() {
        // Every other test reaches these through the symbols, so their values would have no witness. The
        // plan specifies all three - 25 m cells, heading delta > 150 degrees, retrace < 15% - which makes
        // them decisions to be changed deliberately rather than drifted.
        #expect(RetraceDetector.cellSizeMeters == 25.0)
        #expect(RetraceDetector.oppositeHeadingDegrees == 150.0)
        #expect(RetraceDetector.maxRetraceFraction == 0.15)
    }
}
