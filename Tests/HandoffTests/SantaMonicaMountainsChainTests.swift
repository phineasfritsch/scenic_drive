import Foundation
import Testing
import ScenicKit
@testable import Handoff

/// Two properties of the LA drive that are not about the spacing of its pins: every point is inside
/// the region the app claims to cover, and the straight line through them is the number the screen
/// shows.
///
/// ## Why the bbox is READ and not re-typed
///
/// `services/etl/regions/la/region.json` is the definition of "the LA region" for the ETL, the graph
/// and the corpus. A test that typed `-119.0, 33.7, -117.85, 34.45` out again would go green after
/// someone moved the region's box, with nine pins sitting outside the graph that is supposed to
/// contain them. So this suite reads that file. It is NOT a soft check: a missing or unparsable
/// region file is a failure, not a skip, because a check that quietly enumerates nothing is the
/// failure mode `ops/` exists to refuse (P-SRC-02, fail closed).
///
/// ## Why the drive's own pair of accessors is checked here
///
/// `HandoffDrive` is what the screen holds, and mapping a case to the wrong array is a defect no
/// Apple-only target on this box could catch. The mapping is one `switch`; this is where it is read.
@Suite("The Santa Monica Mountains chain, the region and the number")
struct SantaMonicaMountainsChainTests {

    // MARK: - The chain

    /// The chain the card's number is measured over: the nine pins in driving order, then Westwood.
    /// Read from `SantaMonicaMountainsRouteTests`, which is the one place they are typed out against
    /// the shipped array.
    static let expectedPoints: [Coordinate] =
        SantaMonicaMountainsRouteTests.expectedWaypoints + [SantaMonicaMountainsRouteTests.westwoodVillage]

    /// THE NUMBER ON THE SCREEN. Floored whole kilometres over `expectedPoints`. An integer, so it is
    /// pinned exactly.
    static let straightLineKilometers = 47

    /// THE NUMBER ON THE SCREEN for the owner's drive, in the unit it renders (T-0203). Floored whole
    /// miles over the same `expectedPoints` and the same metres as `straightLineKilometers` -
    /// 47_445.124 m is 29.48 international miles. Typed out beside the kilometre literal, not
    /// converted from it.
    static let straightLineMiles = 29

    /// The same measurement before the floor, to a metre. The band is one metre, not one kilometre:
    /// it catches a change in the arithmetic (a different radius, a different formula) that the
    /// floored integer would swallow. It is `ScenicKit.Geo`'s haversine, the same code that gives
    /// `StraightLineDistanceTests.straightLineMeters` (112_268.093 m) for the Skyline chain.
    static let straightLineMeters = 47_445.124

    /// THE PER-POINT BOUND, as `StraightLineDistanceTests` writes it: no point in the shipped chain
    /// may be further than this from the literal typed out for it.
    static let pinDriftToleranceMeters = 1_000.0

    @Test("the chain is the shipped pins in driving order, then Westwood")
    func theChainIsTheShippedPinsThenWestwood() {
        let chain = StraightLineDistance.santaMonicaMountainsRoutePoints
        #expect(chain == Self.expectedPoints, "got \(chain)")
        #expect(chain.count == SantaMonicaMountainsRoute.waypoints.count + 1)
        #expect(chain.last == SantaMonicaMountainsRoute.destination)
    }

    @Test("every point is within a kilometre of where this suite thinks it is")
    func everyPointIsWithinAKilometreOfWhereThisSuiteThinksItIs() {
        let chain = StraightLineDistance.santaMonicaMountainsRoutePoints
        #expect(chain.count == Self.expectedPoints.count,
                "the chain is \(chain.count) points, this suite types \(Self.expectedPoints.count)")
        for (index, expected) in Self.expectedPoints.enumerated() where index < chain.count {
            let drift = Geo.distanceMeters(chain[index], expected)
            #expect(drift <= Self.pinDriftToleranceMeters,
                    "point \(index) is \(drift) m from \(expected), bound \(Self.pinDriftToleranceMeters) m")
        }
    }

    @Test("the whole-kilometre figure is the number the LA drive shows")
    func theWholeKilometreFigureIsTheNumberTheScreenShows() {
        let kilometres = StraightLineDistance.santaMonicaMountainsRouteWholeKilometers
        #expect(kilometres == Self.straightLineKilometers, "got \(kilometres) km")
        let metres = StraightLineDistance.meters(through: StraightLineDistance.santaMonicaMountainsRoutePoints)
        #expect(abs(metres - Self.straightLineMeters) <= 1,
                "got \(metres) m, pinned \(Self.straightLineMeters) m")

        // The Skyline figure is NOT moved by any of this. Its literal lives in
        // `StraightLineDistanceTests`; this is the cheap cross-check that the two drives did not
        // become one.
        #expect(StraightLineDistance.skylineRouteWholeKilometers == 112,
                "the Skyline figure moved to \(StraightLineDistance.skylineRouteWholeKilometers) km")
        #expect(kilometres != StraightLineDistance.skylineRouteWholeKilometers)
    }

    @Test("the whole-mile figure is the number the LA drive renders, from the same metres")
    func theWholeMileFigureIsTheNumberTheScreenRenders() {
        let miles = StraightLineDistance.wholeMiles(for: .santaMonicaMountains)
        #expect(miles == Self.straightLineMiles, "got \(miles) mi")
        #expect(StraightLineDistance.wholeMiles(through: StraightLineDistance.santaMonicaMountainsRoutePoints)
                == miles, "the drive's chain and the shipped chain give different miles")
        // ONE COMPUTATION, TWO RENDERINGS: the same metres the kilometre figure floors, floored by
        // the exact mile.
        let metres = StraightLineDistance.meters(through: StraightLineDistance.santaMonicaMountainsRoutePoints)
        #expect(Int((metres / 1_609.344).rounded(.down)) == miles, "got \(metres) m")
        // And the two drives are still two drives in miles as well as in kilometres.
        #expect(StraightLineDistance.wholeMiles(for: .skyline) != miles,
                "both drives render \(miles) miles")
    }

    // MARK: - The region

    /// The LA region's bounding box, read from the file the ETL reads.
    ///
    /// Throws rather than returning an optional: every caller below wants the failure to name what
    /// could not be read.
    static func laRegionBbox() throws -> (minLon: Double, minLat: Double, maxLon: Double, maxLat: Double) {
        // `#filePath` is Tests/HandoffTests/<this file>; three parents up is the repository root.
        let root = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()
            .deletingLastPathComponent()
            .deletingLastPathComponent()
        let regionURL = root.appendingPathComponent("services/etl/regions/la/region.json")
        let data = try Data(contentsOf: regionURL)
        let parsed = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        guard let bbox = parsed?["bbox"] as? [String: Any],
              let minLon = bbox["min_lon"] as? Double,
              let minLat = bbox["min_lat"] as? Double,
              let maxLon = bbox["max_lon"] as? Double,
              let maxLat = bbox["max_lat"] as? Double else {
            throw CocoaError(.coderReadCorrupt)
        }
        return (minLon, minLat, maxLon, maxLat)
    }

    @Test("the region file this suite reads is the LA region and has a box with area")
    func theRegionFileIsReadableAndIsLA() throws {
        // Without this, a file that parsed to an empty box would let every point below pass
        // vacuously - or fail for the wrong reason - and nobody would know which.
        let box = try Self.laRegionBbox()
        #expect(box.minLon < box.maxLon, "box is \(box)")
        #expect(box.minLat < box.maxLat, "box is \(box)")
        #expect(box.minLon < -118 && box.maxLon > -118, "the LA box should straddle -118: \(box)")
    }

    @Test("every pin and the destination are inside the LA region's bbox")
    func everyPointIsInsideTheRegion() throws {
        let box = try Self.laRegionBbox()
        let chain = StraightLineDistance.santaMonicaMountainsRoutePoints
        #expect(chain.count == 10, "the chain is \(chain.count) points")
        for (index, point) in chain.enumerated() {
            #expect(point.longitude >= box.minLon && point.longitude <= box.maxLon,
                    "point \(index) longitude \(point.longitude) is outside [\(box.minLon), \(box.maxLon)]")
            #expect(point.latitude >= box.minLat && point.latitude <= box.maxLat,
                    "point \(index) latitude \(point.latitude) is outside [\(box.minLat), \(box.maxLat)]")
        }
    }

    @Test("the Skyline drive is NOT in the LA region, which is why this drive exists")
    func theSkylineDriveIsOutsideTheLARegion() throws {
        // The standing demonstration that the bbox check above can fail: the same predicate over the
        // Bay Area chain refuses every one of its points. A box edited until it contained both drives
        // would fail here.
        let box = try Self.laRegionBbox()
        let outside = StraightLineDistance.skylineRoutePoints.filter { point in
            point.longitude < box.minLon || point.longitude > box.maxLon
                || point.latitude < box.minLat || point.latitude > box.maxLat
        }
        #expect(outside.count == StraightLineDistance.skylineRoutePoints.count,
                "\(StraightLineDistance.skylineRoutePoints.count - outside.count) Skyline points are inside the LA box")
    }

    // MARK: - The selector the screen holds

    @Test("each drive maps to its own route, and the default is the LA drive")
    func eachDriveMapsToItsOwnRoute() {
        #expect(HandoffDrive.skyline.waypoints == SkylineRoute.waypoints)
        #expect(HandoffDrive.skyline.destination == SkylineRoute.destination)
        #expect(HandoffDrive.santaMonicaMountains.waypoints == SantaMonicaMountainsRoute.waypoints)
        #expect(HandoffDrive.santaMonicaMountains.destination == SantaMonicaMountainsRoute.destination)
        #expect(HandoffDrive.santaMonicaMountains.chain == StraightLineDistance.santaMonicaMountainsRoutePoints)
        #expect(HandoffDrive.skyline.chain == StraightLineDistance.skylineRoutePoints)

        // The ruling, as an assertion: nothing is known at launch, so the owner's drive is what the
        // screen opens on. See `HandoffDrive.defaultDrive` for why the condition in the acceptance
        // line cannot be evaluated at all.
        #expect(HandoffDrive.defaultDrive == .santaMonicaMountains, "got \(HandoffDrive.defaultDrive)")
        #expect(HandoffDrive.allCases.count == 2, "got \(HandoffDrive.allCases)")
    }

    @Test("the distance accessor reports each drive's own figure")
    func theDistanceAccessorFollowsTheDrive() {
        #expect(StraightLineDistance.wholeKilometers(for: .santaMonicaMountains) == Self.straightLineKilometers)
        #expect(StraightLineDistance.wholeKilometers(for: .skyline) == 112)
    }
}
