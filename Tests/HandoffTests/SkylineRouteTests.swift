import Foundation
import Testing
import ScenicKit
@testable import Handoff

/// The pins of the hard-coded Skyline drive: how many, in what order, and how far apart.
///
/// ## Why every coordinate is typed out again below
///
/// The fixtures here are literals, not `SkylineRoute.waypoints`. A test whose expected value is read
/// out of the thing it checks passes for any value that thing happens to hold - it witnesses nothing.
/// The same lesson is written into `AppleMapsDirectionsCapTests`, where every fixture reached the cap
/// through `AppleMapsDirections.maxWaypoints` and raising the cap from 9 to 99 left the suite green.
/// So the seven coordinates appear twice in this repository on purpose, and editing one of them
/// without the other is a red test rather than a silent re-plan of somebody's drive.
///
/// ## Why this file has its own great-circle function
///
/// `ScenicKit.Geo.distanceMeters` is the product's haversine and is deliberately NOT used here.
/// `metresApart` below is the spherical law of cosines - a different formula, written out in this
/// file - so that a wrong `Geo` and a wrong bound cannot agree with each other. Production code does
/// not measure the spacing of these pins at all today; if it ever does, it must not reach for this
/// function either. `helperMeasuresAKnownDistance` pins the helper against a distance that can be
/// worked out by hand, so a broken helper fails by name instead of quietly widening the bound.
@Suite("The Skyline route's pins")
struct SkylineRouteTests {

    // MARK: - The seven pins, typed out (see the suite comment)

    static let i280DalyCity = Coordinate(latitude: 37.70526, longitude: -122.47165)
    static let canadaRoadWoodside = Coordinate(latitude: 37.44197, longitude: -122.26667)
    static let canadaRoadMid = Coordinate(latitude: 37.47579, longitude: -122.30852)
    static let canadaRoadAt92 = Coordinate(latitude: 37.50621, longitude: -122.34073)
    static let halfMoonBayRoad = Coordinate(latitude: 37.50745, longitude: -122.34299)
    static let skylineRidge = Coordinate(latitude: 37.38776, longitude: -122.26638)
    static let skylineSouthOfSkyLonda = Coordinate(latitude: 37.36648, longitude: -122.24765)

    static let expectedWaypoints: [Coordinate] = [
        i280DalyCity,
        canadaRoadWoodside,
        canadaRoadMid,
        canadaRoadAt92,
        halfMoonBayRoad,
        skylineRidge,
        skylineSouthOfSkyLonda,
    ]

    /// The 280 -> Cañada -> 92 leg: off the freeway at Woodside, north along Crystal Springs
    /// Reservoir, up to CA-92. Typed out rather than sliced out of `SkylineRoute.waypoints`, for the
    /// reason in the suite comment; `theCanadaLegIsWhereThisTestThinksItIs` is what ties the two
    /// together, so a reordering of the route cannot leave this test measuring a different leg.
    static let canadaLeg: [Coordinate] = [
        canadaRoadWoodside,
        canadaRoadMid,
        canadaRoadAt92,
        halfMoonBayRoad,
    ]

    /// That leg as it appears in the array the app actually hands Apple Maps.
    ///
    /// Located by its two typed-out END POINTS, not by a pair of index numbers. With `1...4` written
    /// out, deleting a pin from the middle of the route slides the window one pin down the ridge and
    /// the spacing test then reports a gap on a leg nobody asked about - the check would still go red,
    /// but for the wrong reason and with the wrong number in the message. Anchored on the end points,
    /// deleting a pin shortens this slice and the failure names the gap that actually opened.
    ///
    /// Empty if either end point is missing or they are the wrong way round, which makes the spacing
    /// below infinite rather than vacuously fine.
    static func canadaLegAsShipped() -> [Coordinate] {
        let w = SkylineRoute.waypoints
        guard let start = w.firstIndex(of: canadaRoadWoodside),
              let end = w.firstIndex(of: halfMoonBayRoad),
              start < end else { return [] }
        return Array(w[start...end])
    }

    /// THE BOUND. No two consecutive pins on the Cañada leg may be further apart than this.
    ///
    /// Six kilometres is a product choice, not a measurement: it is loose enough that the pins can be
    /// nudged onto better points on the same roads without a test edit, and tight enough that the
    /// Edgewood Road rat-run cannot fit inside a gap - deleting the mid-Cañada pin opens a gap this
    /// test then reports and refuses. It is stated here, once, as a number this file owns.
    static let canadaLegMaxSpacingMeters = 6_000.0

    // MARK: - This file's own great-circle distance

    /// Metres between two positions on a sphere, by the spherical law of cosines.
    ///
    /// NOT `Geo.distanceMeters` - see the suite comment. The radius is the IUGG mean Earth radius,
    /// written out here rather than read from `Geo.earthRadiusMeters` for the same reason.
    static func metresApart(_ a: Coordinate, _ b: Coordinate) -> Double {
        let radiusMeters = 6_371_008.8
        let toRadians = Double.pi / 180
        let lat1 = a.latitude * toRadians
        let lat2 = b.latitude * toRadians
        let deltaLon = (b.longitude - a.longitude) * toRadians
        let cosine = sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(deltaLon)
        return radiusMeters * acos(max(-1, min(1, cosine)))
    }

    /// Consecutive spacings along `pins`, in metres.
    static func spacings(_ pins: [Coordinate]) -> [Double] {
        guard pins.count > 1 else { return [] }
        return (0..<(pins.count - 1)).map { metresApart(pins[$0], pins[$0 + 1]) }
    }

    // MARK: - The helper itself

    @Test("the great-circle helper measures a distance that can be checked by hand")
    func helperMeasuresAKnownDistance() {
        // One degree of latitude on a sphere of radius 6_371_008.8 m is 6_371_008.8 * pi / 180 m,
        // which is 111_194.9266... m. Nothing in Handoff, ScenicKit or this suite is consulted to get
        // that; it is arithmetic on the radius this file writes out.
        let oneDegree = Self.metresApart(Coordinate(latitude: 0, longitude: 0),
                                         Coordinate(latitude: 1, longitude: 0))
        #expect(abs(oneDegree - 111_194.9266) < 0.5, "one degree of latitude measured \(oneDegree) m")

        // Zero distance must not come back as NaN: `acos` of a cosine that floating point pushed a
        // hair above 1 is NaN, and a NaN spacing compares false against any bound, so the maximum
        // test would pass while measuring nothing.
        let samePoint = Self.metresApart(Self.canadaRoadMid, Self.canadaRoadMid)
        #expect(samePoint == 0, "a point to itself measured \(samePoint) m")
    }

    // MARK: - Count, contents, order

    @Test("there are seven pins, and the number is pinned")
    func pinCountIsSeven() {
        // Written out, not `expectedWaypoints.count` and not `maxWaypoints`: the plan's cap is nine
        // "pinned waypoints at decision points", and this route is under it because seven decision
        // points is what the drive has - a list that grew to nine without anybody deciding to add two
        // would still be inside the cap and would still be a different drive.
        #expect(SkylineRoute.waypoints.count == 7, "got \(SkylineRoute.waypoints.count)")
    }

    @Test("every pin is the coordinate the reverse geocode returned")
    func everyPinIsTheVerifiedLiteral() {
        #expect(SkylineRoute.waypoints == Self.expectedWaypoints, "got \(SkylineRoute.waypoints)")
        #expect(SkylineRoute.destination == Coordinate(latitude: 37.78794, longitude: -122.40752),
                "got \(SkylineRoute.destination)")
    }

    @Test("the Cañada leg is the slice this test thinks it is")
    func theCanadaLegIsWhereThisTestThinksItIs() {
        // Without this, reordering the route would leave `maxSpacingOnTheCanadaLeg` measuring four
        // coordinates that are no longer consecutive in the array Apple Maps is handed.
        let slice = Self.canadaLegAsShipped()
        #expect(slice == Self.canadaLeg, "got \(slice)")
    }

    @Test("the pins run the drive: south on 280, north up Cañada to 92, then south down the ridge")
    func orderIsTheDrive() throws {
        // RULED, because "latitude non-increasing from the I-280 pin onward" is NOT true of this route
        // and never was: Cañada Road is driven NORTHBOUND from Woodside up to CA-92, so latitude rises
        // across the middle of the array. Monotone per leg is what is actually true, and each leg is
        // one direction of travel:
        //   pins 0..1  southbound I-280            latitude strictly decreasing
        //   pins 1..4  northbound Cañada, west 92  latitude strictly increasing
        //   pins 4..6  southbound CA-35 ridge      latitude strictly decreasing
        let w = SkylineRoute.waypoints
        try #require(w.count == 7)

        #expect(w[0].latitude > w[1].latitude, "280 leg: \(w[0].latitude) then \(w[1].latitude)")

        for i in 1..<4 {
            #expect(w[i].latitude < w[i + 1].latitude,
                    "Cañada leg pin \(i): \(w[i].latitude) then \(w[i + 1].latitude)")
        }

        for i in 4..<6 {
            #expect(w[i].latitude > w[i + 1].latitude,
                    "ridge leg pin \(i): \(w[i].latitude) then \(w[i + 1].latitude)")
        }

        // The Cañada leg also runs west the whole way, which is the half of "northbound up the
        // reservoir" that latitude alone does not catch.
        for i in 1..<4 {
            #expect(w[i].longitude > w[i + 1].longitude,
                    "Cañada leg pin \(i): \(w[i].longitude) then \(w[i + 1].longitude)")
        }
    }

    // MARK: - The spacing bound

    @Test("no gap on the 280 -> Cañada -> 92 leg is wider than the bound")
    func maxSpacingOnTheCanadaLeg() {
        // Measured over the array the app actually hands Apple Maps, not over this file's fixtures -
        // `theCanadaLegIsWhereThisTestThinksItIs` is what proves those are the same four pins.
        let leg = Self.canadaLegAsShipped()
        let gaps = Self.spacings(leg)
        let widest = gaps.max() ?? .infinity
        #expect(widest < Self.canadaLegMaxSpacingMeters,
                "widest gap on the Cañada leg is \(widest) m, bound \(Self.canadaLegMaxSpacingMeters) m; gaps were \(gaps)")
    }

    @Test("the mid-Cañada pin is what keeps that bound: without it the gap is over it")
    func midCanadaPinIsWhatKeepsTheBound() {
        // The RED demonstration, standing: delete the mid-Cañada pin from `SkylineRoute` and
        // `maxSpacingOnTheCanadaLeg` fails. This test is the same arithmetic on this file's own
        // literals, so the reason the bound holds is stated rather than folklore, and a future edit
        // that moves the mid pin until the bound is met trivially has to fail one of the two.
        let withoutMid = [Self.canadaRoadWoodside, Self.canadaRoadAt92, Self.halfMoonBayRoad]
        let widest = Self.spacings(withoutMid).max() ?? 0
        #expect(widest > Self.canadaLegMaxSpacingMeters,
                "without the mid-Cañada pin the widest gap is \(widest) m, not over the \(Self.canadaLegMaxSpacingMeters) m bound")
    }

    // MARK: - The route still builds a URL

    @Test("seven pins still build a handoff URL")
    func theRouteStillBuildsAURL() throws {
        let url = try AppleMapsDirections(source: nil,
                                          destination: SkylineRoute.destination,
                                          waypoints: SkylineRoute.waypoints,
                                          mode: .driving).url()
        let components = URLComponents(url: url, resolvingAgainstBaseURL: false)
        let pinned = (components?.queryItems ?? []).filter { $0.name == "waypoint" }.map { $0.value ?? "" }
        #expect(pinned == ["37.70526,-122.47165",
                           "37.44197,-122.26667",
                           "37.47579,-122.30852",
                           "37.50621,-122.34073",
                           "37.50745,-122.34299",
                           "37.38776,-122.26638",
                           "37.36648,-122.24765"], "got \(pinned)")
    }
}
