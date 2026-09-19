import Foundation
import Testing
import ScenicKit
@testable import Handoff

/// The pins of the hard-coded LA drive: how many, in what order, and how far apart.
///
/// ## Why every coordinate is typed out again below
///
/// The fixtures here are literals, not `SantaMonicaMountainsRoute.waypoints`. A test whose expected
/// value is read out of the thing it checks passes for any value that thing happens to hold - it
/// witnesses nothing. So the nine coordinates appear twice in this repository on purpose, and editing
/// one of them without the other is a red test rather than a silent re-plan of somebody's drive.
///
/// ## Why this file has its own great-circle function
///
/// It does not: it reuses `SkylineRouteTests.metresApart`, the spherical law of cosines written out
/// there, deliberately NOT `ScenicKit.Geo`, so that a wrong `Geo` and a wrong bound cannot agree with
/// each other. One formula behind every spacing bound in this bundle, not two that could drift apart,
/// and `SkylineRouteTests.helperMeasuresAKnownDistance` is what pins it against arithmetic done by
/// hand.
@Suite("The Santa Monica Mountains route's pins")
struct SantaMonicaMountainsRouteTests {

    // MARK: - The nine pins, typed out (see the suite comment)

    static let sunsetBrentwood = Coordinate(latitude: 34.05820, longitude: -118.47930)
    static let sunsetPacificPalisades = Coordinate(latitude: 34.04739, longitude: -118.52581)
    static let sunsetAtPCH = Coordinate(latitude: 34.03857, longitude: -118.55562)
    static let pchAtTopanga = Coordinate(latitude: 34.04011, longitude: -118.57930)
    static let topangaVillage = Coordinate(latitude: 34.09312, longitude: -118.60182)
    static let topangaCrest = Coordinate(latitude: 34.12587, longitude: -118.60045)
    static let topangaAtVentura = Coordinate(latitude: 34.16801, longitude: -118.60576)
    static let mulhollandEastOf405 = Coordinate(latitude: 34.13208, longitude: -118.45321)
    static let beverlyGlen = Coordinate(latitude: 34.12922, longitude: -118.44168)

    /// Westwood Village. Typed out here because it is the end of the drive and the last hop of the
    /// chain `SantaMonicaMountainsChainTests` measures.
    static let westwoodVillage = Coordinate(latitude: 34.06110, longitude: -118.44548)

    static let expectedWaypoints: [Coordinate] = [
        sunsetBrentwood,
        sunsetPacificPalisades,
        sunsetAtPCH,
        pchAtTopanga,
        topangaVillage,
        topangaCrest,
        topangaAtVentura,
        mulhollandEastOf405,
        beverlyGlen,
    ]

    // MARK: - The two bounded legs

    /// The coast leg: west along Sunset to PCH, then north-west to the Topanga junction.
    static let coastLeg: [Coordinate] = [
        sunsetBrentwood,
        sunsetPacificPalisades,
        sunsetAtPCH,
        pchAtTopanga,
    ]

    /// The canyon leg: up CA-27 from the coast, through the village, over the crest, down into the
    /// Valley. It BEGINS at the coast leg's last pin, so between the two legs every consecutive pair
    /// from Brentwood to Woodland Hills is under one bound or the other and none falls between them.
    static let canyonLeg: [Coordinate] = [
        pchAtTopanga,
        topangaVillage,
        topangaCrest,
        topangaAtVentura,
    ]

    /// THE COAST BOUND. Six kilometres, the same number `SkylineRouteTests` uses on its Cañada leg
    /// and for the same reason: loose enough that a pin can be nudged onto a better point on the same
    /// road without a test edit, tight enough that the Chautauqua/San Vicente cut cannot fit inside a
    /// gap. `theSunsetPalisadesPinIsWhatKeepsTheCoastBound` is the measurement that says so.
    static let coastLegMaxSpacingMeters = 6_000.0

    /// THE CANYON BOUND. Eight kilometres, deliberately LOOSER than the coast's, for the reason
    /// `SkylineRidgeLegTests`' ridge bound is looser than its Cañada bound: the climb from PCH to
    /// Topanga village is 6.2 km of state highway with no junction in it to pin. It is a ceiling, not
    /// a measurement, and `theTopangaVillagePinIsWhatKeepsTheCanyonBound` is what keeps it honest.
    static let canyonLegMaxSpacingMeters = 8_000.0

    // MARK: - Locating a leg in the shipped array

    /// A leg as it appears in the array the app actually hands Apple Maps, located by its two
    /// typed-out END POINTS rather than by an index pair - with indices written out, deleting a pin
    /// slides the window onto a leg nobody asked about and the failure names the wrong gap.
    ///
    /// Empty if either end point is missing or they are the wrong way round, which makes the spacing
    /// below infinite rather than vacuously fine.
    static func legAsShipped(from start: Coordinate, to end: Coordinate) -> [Coordinate] {
        let w = SantaMonicaMountainsRoute.waypoints
        guard let first = w.firstIndex(of: start),
              let last = w.firstIndex(of: end),
              first < last else { return [] }
        return Array(w[first...last])
    }

    static func coastLegAsShipped() -> [Coordinate] {
        legAsShipped(from: sunsetBrentwood, to: pchAtTopanga)
    }

    static func canyonLegAsShipped() -> [Coordinate] {
        legAsShipped(from: pchAtTopanga, to: topangaAtVentura)
    }

    /// Consecutive spacings, in metres, by `SkylineRouteTests`' law-of-cosines helper.
    static func spacings(_ pins: [Coordinate]) -> [Double] {
        SkylineRouteTests.spacings(pins)
    }

    // MARK: - Count and contents

    @Test("there are nine pins, and the number is pinned")
    func pinCountIsNine() {
        // Written out, not `expectedWaypoints.count` and not `maxWaypoints`: the plan's cap is nine
        // "pinned waypoints at decision points", and this route is AT it because nine decision points
        // is what the drive has. A list that grew past nine would fail `AppleMapsDirections`' cap; a
        // list that shrank to eight would still build a URL and would be a different drive.
        #expect(SantaMonicaMountainsRoute.waypoints.count == 9,
                "got \(SantaMonicaMountainsRoute.waypoints.count)")
    }

    @Test("every pin is the coordinate the reverse geocode returned")
    func everyPinIsTheVerifiedLiteral() {
        #expect(SantaMonicaMountainsRoute.waypoints == Self.expectedWaypoints,
                "got \(SantaMonicaMountainsRoute.waypoints)")
        #expect(SantaMonicaMountainsRoute.destination == Self.westwoodVillage,
                "got \(SantaMonicaMountainsRoute.destination)")
    }

    @Test("the two drives are different drives and share no pin")
    func theTwoDrivesShareNoPin() {
        // The cheapest way this file could be green while the app shipped one drive twice.
        let skyline = Set(SkylineRoute.waypoints.map { "\($0.latitude),\($0.longitude)" })
        let la = Set(SantaMonicaMountainsRoute.waypoints.map { "\($0.latitude),\($0.longitude)" })
        #expect(skyline.intersection(la).isEmpty, "shared pins: \(skyline.intersection(la))")
        #expect(SantaMonicaMountainsRoute.destination != SkylineRoute.destination)
    }

    // MARK: - Order

    @Test("the pins run the drive: west on Sunset, up the canyon, east on the ridge, down to Westwood")
    func orderIsTheDrive() throws {
        // RULED against the numbers rather than assumed. "Latitude monotone" is FALSE for this loop
        // and so is "longitude monotone"; what is true is one direction of travel per leg, and the
        // legs are not on the same axis:
        //   pins 0..3  west on Sunset, north-west on PCH   longitude strictly decreasing
        //              (latitude is NOT monotone: it falls to 34.03857 at PCH and rises again to
        //               34.04011 at the Topanga junction)
        //   pins 3..6  up the canyon to the Valley         latitude strictly increasing
        //              (longitude is NOT monotone: -118.57930, -118.60182, -118.60045, -118.60576)
        //   pins 6..8  the freeway baseline and the ridge  latitude strictly decreasing AND
        //              longitude strictly increasing
        let w = SantaMonicaMountainsRoute.waypoints
        try #require(w.count == 9)

        for i in 0..<3 {
            #expect(w[i].longitude > w[i + 1].longitude,
                    "coast leg pin \(i): \(w[i].longitude) then \(w[i + 1].longitude)")
        }

        for i in 3..<6 {
            #expect(w[i].latitude < w[i + 1].latitude,
                    "canyon leg pin \(i): \(w[i].latitude) then \(w[i + 1].latitude)")
        }

        for i in 6..<8 {
            #expect(w[i].latitude > w[i + 1].latitude,
                    "return leg pin \(i): \(w[i].latitude) then \(w[i + 1].latitude)")
            #expect(w[i].longitude < w[i + 1].longitude,
                    "return leg pin \(i): \(w[i].longitude) then \(w[i + 1].longitude)")
        }

        // The last hop, pin 9 to Westwood, turns back WEST while latitude keeps falling, which is why
        // latitude and not longitude is the invariant that runs to the end of the drive.
        #expect(SantaMonicaMountainsRoute.destination.latitude < w[8].latitude)
        #expect(SantaMonicaMountainsRoute.destination.longitude < w[8].longitude)
    }

    // MARK: - Spacing

    @Test("the coast leg is the slice this test thinks it is")
    func theCoastLegIsWhereThisTestThinksItIs() {
        let slice = Self.coastLegAsShipped()
        #expect(slice == Self.coastLeg, "got \(slice)")
    }

    @Test("the canyon leg is the slice this test thinks it is")
    func theCanyonLegIsWhereThisTestThinksItIs() {
        let slice = Self.canyonLegAsShipped()
        #expect(slice == Self.canyonLeg, "got \(slice)")
    }

    @Test("no gap on the Sunset/PCH coast leg is wider than the bound")
    func maxSpacingOnTheCoastLeg() {
        let gaps = Self.spacings(Self.coastLegAsShipped())
        let widest = gaps.max() ?? .infinity
        #expect(widest < Self.coastLegMaxSpacingMeters,
                "widest gap on the coast leg is \(widest) m, bound \(Self.coastLegMaxSpacingMeters) m; gaps were \(gaps)")
    }

    @Test("no gap on the Topanga canyon leg is wider than the bound")
    func maxSpacingOnTheCanyonLeg() {
        let gaps = Self.spacings(Self.canyonLegAsShipped())
        let widest = gaps.max() ?? .infinity
        #expect(widest < Self.canyonLegMaxSpacingMeters,
                "widest gap on the canyon leg is \(widest) m, bound \(Self.canyonLegMaxSpacingMeters) m; gaps were \(gaps)")
    }

    @Test("the Palisades pin is what keeps the coast bound: without it the gap is over it")
    func theSunsetPalisadesPinIsWhatKeepsTheCoastBound() {
        // The RED demonstration, standing. Without pin 2 the Chautauqua and San Vicente cuts sit
        // inside one 7362.5 m gap.
        let widest = Self.spacings([Self.sunsetBrentwood, Self.sunsetAtPCH]).max() ?? 0
        #expect(widest > Self.coastLegMaxSpacingMeters,
                "without the Palisades pin the widest gap is \(widest) m, not over the \(Self.coastLegMaxSpacingMeters) m bound")
    }

    @Test("the village pin is what keeps the canyon bound: without it the gap is over it")
    func theTopangaVillagePinIsWhatKeepsTheCanyonBound() {
        // The RED demonstration, standing. Without pin 5 the whole Topanga residential grid - Tuna
        // Canyon, Fernwood Pacific, Entrada, Old Topanga - sits inside one 9733.0 m gap.
        let widest = Self.spacings([Self.pchAtTopanga, Self.topangaCrest]).max() ?? 0
        #expect(widest > Self.canyonLegMaxSpacingMeters,
                "without the village pin the widest gap is \(widest) m, not over the \(Self.canyonLegMaxSpacingMeters) m bound")
    }

    @Test("exactly one gap in the whole chain is over the canyon bound, and it is the freeway one")
    func onlyTheFreewayBaselineIsUnbounded() {
        // The return leg is NOT bounded and must not be: pin 7 to pin 8 is 14.6 km of US-101 and
        // I-405, the freeway baseline the Brief asks for, and a bound written to fit it would be a
        // number written to fit. What is asserted instead is the shape - that there is exactly one
        // such gap and that it is that one.
        let chain = SantaMonicaMountainsRoute.waypoints + [SantaMonicaMountainsRoute.destination]
        let gaps = Self.spacings(chain)
        let over = gaps.enumerated().filter { $0.element > Self.canyonLegMaxSpacingMeters }
        #expect(over.count == 1, "gaps over the bound: \(over); all gaps \(gaps)")
        #expect(over.first?.offset == 6, "the unbounded gap is between pins \(over.first?.offset ?? -1) and the next")
        #expect((over.first?.element ?? 0) > 14_000, "the freeway gap measured \(over.first?.element ?? 0) m")
    }

    // MARK: - The route still builds a URL

    @Test("nine pins still build a handoff URL")
    func theRouteStillBuildsAURL() throws {
        let url = try AppleMapsDirections(source: nil,
                                          destination: SantaMonicaMountainsRoute.destination,
                                          waypoints: SantaMonicaMountainsRoute.waypoints,
                                          mode: .driving).url()
        let components = URLComponents(url: url, resolvingAgainstBaseURL: false)
        let pinned = (components?.queryItems ?? []).filter { $0.name == "waypoint" }.map { $0.value ?? "" }
        #expect(pinned == ["34.05820,-118.47930",
                           "34.04739,-118.52581",
                           "34.03857,-118.55562",
                           "34.04011,-118.57930",
                           "34.09312,-118.60182",
                           "34.12587,-118.60045",
                           "34.16801,-118.60576",
                           "34.13208,-118.45321",
                           "34.12922,-118.44168"], "got \(pinned)")
    }
}
