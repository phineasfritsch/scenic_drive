import Foundation
import Handoff
import ScenicKit
import Testing

/// The Saddle Peak drive (T-0236): the engine's route from PR #124 - `ops/plan` over
/// `Tests/Fixtures/t0182/plan-pair` at +25 min, lambda 7.75 - as the app's first and default drive.
///
/// Every literal below is typed out AGAIN from the URL quoted in T-0182's Log, not read from the type under
/// test, so a pin edited in `SaddlePeakRoute` is refused here by name. The URL assertion is on the shipping
/// symbol `HandoffDrive.url()` - the construction the button and the clipboard both use.
@Suite("SaddlePeakRoute")
struct SaddlePeakRouteTests {
    /// ops/plan's `source`, held as `SaddlePeakRoute.origin` and NOT in the URL (the ruling is in the type).
    static let origin = Coordinate(latitude: 34.09440, longitude: -118.60130)
    static let destination = Coordinate(latitude: 34.03650, longitude: -118.68700)
    static let waypoints: [Coordinate] = [
        Coordinate(latitude: 34.08350, longitude: -118.60162),
        Coordinate(latitude: 34.07941, longitude: -118.60288),
        Coordinate(latitude: 34.06814, longitude: -118.61111),
        Coordinate(latitude: 34.07507, longitude: -118.62613),
        Coordinate(latitude: 34.08375, longitude: -118.63666),
        Coordinate(latitude: 34.08111, longitude: -118.64574),
        Coordinate(latitude: 34.07001, longitude: -118.65343),
        Coordinate(latitude: 34.08025, longitude: -118.70367),
        Coordinate(latitude: 34.06937, longitude: -118.70790),
    ]

    /// T-0182's URL with `source=` removed (the app sends `source: nil`) - otherwise byte for byte.
    static let expectedURL = "https://maps.apple.com/directions?destination=34.03650,-118.68700"
        + "&waypoint=34.08350,-118.60162&waypoint=34.07941,-118.60288&waypoint=34.06814,-118.61111"
        + "&waypoint=34.07507,-118.62613&waypoint=34.08375,-118.63666&waypoint=34.08111,-118.64574"
        + "&waypoint=34.07001,-118.65343&waypoint=34.08025,-118.70367&waypoint=34.06937,-118.70790"
        + "&mode=driving"

    @Test("the nine pins, the destination and the origin are ops/plan's, exactly")
    func theLiteralsAreTheEnginesOwn() {
        #expect(SaddlePeakRoute.waypoints == Self.waypoints, "got \(SaddlePeakRoute.waypoints)")
        #expect(SaddlePeakRoute.destination == Self.destination, "got \(SaddlePeakRoute.destination)")
        #expect(SaddlePeakRoute.origin == Self.origin, "got \(SaddlePeakRoute.origin)")
        #expect(HandoffDrive.saddlePeak.waypoints == Self.waypoints)
        #expect(HandoffDrive.saddlePeak.destination == Self.destination)
    }

    @Test("the handoff URL is T-0182's URL without the source")
    func theHandoffURLIsTheEnginesURL() throws {
        let url = try HandoffDrive.saddlePeak.url()
        #expect(url.absoluteString == Self.expectedURL, "got \(url.absoluteString)")
        // The origin is NOT a waypoint: the cap is full at nine (ops/plan printed `WAYPOINTS 9 of max 9`).
        #expect(HandoffDrive.saddlePeak.waypoints.count == AppleMapsDirections.maxWaypoints)
        #expect(!HandoffDrive.saddlePeak.waypoints.contains(Self.origin))
    }

    @Test("Saddle Peak is the default and first of three drives")
    func saddlePeakIsTheDefaultOfThree() {
        #expect(HandoffDrive.defaultDrive == .saddlePeak, "got \(HandoffDrive.defaultDrive)")
        #expect(HandoffDrive.allCases.count == 3, "got \(HandoffDrive.allCases)")
        #expect(HandoffDrive.allCases.first == .saddlePeak, "got \(HandoffDrive.allCases)")
    }

    @Test("only the Saddle Peak drive names a route geometry resource")
    func onlySaddlePeakHasGeometry() {
        #expect(HandoffDrive.saddlePeak.routeGeometryResource == "saddle-peak")
        #expect(HandoffDrive.santaMonicaMountains.routeGeometryResource == nil)
        #expect(HandoffDrive.skyline.routeGeometryResource == nil)
        #expect(HandoffDrive.routeGeometrySubdirectory == "Routes")
        #expect(HandoffDrive.routeGeometryExtension == "geojson")
    }

    @Test("the straight line through the pins is 17 km, 10 miles")
    func theStraightLineIsTheChains() {
        #expect(StraightLineDistance.wholeKilometers(for: .saddlePeak) == 17)
        #expect(StraightLineDistance.wholeMiles(for: .saddlePeak) == 10)
        #expect(HandoffDrive.saddlePeak.chain == Self.waypoints + [Self.destination])
    }

    @Test("the home sentence is this drive's own, digit-free, and ends in the promise")
    func theHomeSentenceIsThisDrivesOwn() {
        let sentence = HandoffDrive.saddlePeak.timingSentence
        #expect(sentence == "A slow mountain afternoon, not a shortcut - the coast road is the quick way. "
            + HandoffDrive.realTimePromise, "got \(sentence)")
        #expect(sentence.rangeOfCharacter(from: .decimalDigits) == nil)
        #expect(HandoffDrive.skyline.timingSentence.contains("the longest of the three drives"))
    }
}
