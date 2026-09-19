import Foundation
import Testing
import ScenicKit
@testable import Handoff

/// The one measured number the home screen is allowed to show: the straight line through the drive's
/// pins, in driving order, ending at the destination.
///
/// ## Why the tolerance is per pin and not on the total
///
/// The rule this suite was written for is "red if a pin moves more than a kilometre". A band around the
/// TOTAL cannot express it. Moving a mid-chain pin perpendicular to its two legs changes the sum by
/// roughly `d^2/2 * (1/L1 + 1/L2)` - for a one-kilometre move between ten-kilometre legs, about a
/// hundred metres. `aPinMovedOffTheRidgeIsCaughtByThePerPinBoundAndNotByTheTotal` is that case,
/// measured: the pin moves 1.1 km and the floored total does not move at all. So the total is pinned
/// EXACTLY, as a floored integer that needs no tolerance, and the kilometre lives on each point.
///
/// ## Where the literals come from
///
/// The seven pins are read from `SkylineRouteTests`, which is the one place they are typed out against
/// the shipped array; typing them a third time here is what `SkylineRidgeLegTests` refused to do and
/// this suite refuses for the same reason. The destination is typed out below because no suite had
/// typed it before this one.
@Suite("The drive's straight-line distance")
struct StraightLineDistanceTests {

    // MARK: - The literals this suite pins

    /// San Francisco, the destination. From `SkylineRoute`'s provenance block: the forward query
    /// `San Francisco, California` returned relation 111968 at `37.7879363, -122.4075201`, rounded to
    /// the five decimals `AppleMapsDirections.coordinateDecimals` allows.
    static let sanFrancisco = Coordinate(latitude: 37.78794, longitude: -122.40752)

    /// The chain the card's number is measured over: the pins in driving order, then the destination.
    static let expectedPoints: [Coordinate] = SkylineRouteTests.expectedWaypoints + [sanFrancisco]

    /// THE NUMBER ON THE CARD. Floored whole kilometres over `expectedPoints`, from
    /// `StraightLineDistance.wholeKilometers(through:)`. An integer, so it is pinned exactly.
    static let straightLineKilometers = 112

    /// The same measurement before the floor, to a metre. The band is one metre and not one kilometre:
    /// it is here to catch a change in the arithmetic (a different radius, a different formula) that
    /// the floored integer would swallow, not to allow a pin to move.
    static let straightLineMeters = 112_268.093

    /// THE PER-POINT BOUND. No point in the shipped chain may be further than this from the literal
    /// this suite types out for it. This is the "more than a kilometre" rule, expressed where it can
    /// actually be enforced.
    static let pinDriftToleranceMeters = 1_000.0

    /// NOT A PIN. Pin 5 (`skylineSouthOfCA92`) moved 1119.8 m up the ridge, towards the CA-92 junction
    /// it was deliberately placed below (see `SkylineRoute` pin 5 and `SkylineRidgeLegTests`). Kept as
    /// a literal because `aPinMovedOffTheRidgeIsCaughtByThePerPinBoundAndNotByTheTotal` measures the
    /// chain it produces, and that chain is the reason the tolerance is not written on the total.
    static let driftedSkylinePin = Coordinate(latitude: 37.48272, longitude: -122.35830)

    // MARK: - The tests

    @Test("the chain is the shipped pins in driving order, then the destination")
    func theChainIsTheShippedPinsThenTheDestination() {
        let chain = StraightLineDistance.skylineRoutePoints
        #expect(chain == Self.expectedPoints, "got \(chain)")
        #expect(chain.count == SkylineRoute.waypoints.count + 1)
        #expect(chain.last == SkylineRoute.destination)
    }

    @Test("every point is within a kilometre of where this suite thinks it is")
    func everyPointIsWithinAKilometreOfWhereThisSuiteThinksItIs() {
        let chain = StraightLineDistance.skylineRoutePoints
        #expect(chain.count == Self.expectedPoints.count,
                "the chain is \(chain.count) points, this suite types \(Self.expectedPoints.count)")
        for (index, expected) in Self.expectedPoints.enumerated() where index < chain.count {
            let drift = Geo.distanceMeters(chain[index], expected)
            #expect(drift <= Self.pinDriftToleranceMeters,
                    "point \(index) is \(drift) m from \(expected), bound \(Self.pinDriftToleranceMeters) m")
        }
    }

    @Test("the whole-kilometre figure is the number the card shows")
    func theWholeKilometreFigureIsTheNumberTheCardShows() {
        let kilometres = StraightLineDistance.skylineRouteWholeKilometers
        #expect(kilometres == Self.straightLineKilometers, "got \(kilometres) km")
        let metres = StraightLineDistance.meters(through: StraightLineDistance.skylineRoutePoints)
        #expect(abs(metres - Self.straightLineMeters) <= 1,
                "got \(metres) m, pinned \(Self.straightLineMeters) m")
    }

    @Test("the figure is floored, not rounded: 1999 m of chain is 1 km and never 2")
    func theFigureIsFlooredAndNeverRoundedUp() {
        // Two points ~1999 m apart on a meridian: 0.01797 degrees of latitude is 1998.9 m at this
        // radius. A round-half-up would print 2 km, which would be the drive claiming a kilometre
        // nobody measured.
        let a = Coordinate(latitude: 37.00000, longitude: -122.00000)
        let b = Coordinate(latitude: 37.01797, longitude: -122.00000)
        let metres = StraightLineDistance.meters(through: [a, b])
        #expect(metres > 1_900 && metres < 2_000, "got \(metres) m")
        #expect(StraightLineDistance.wholeKilometers(through: [a, b]) == 1)
        #expect(StraightLineDistance.wholeKilometers(through: []) == 0)
        #expect(StraightLineDistance.wholeKilometers(through: [a]) == 0)
    }

    @Test("a pin moved off the ridge is caught by the per-point bound and NOT by the total")
    func aPinMovedOffTheRidgeIsCaughtByThePerPinBoundAndNotByTheTotal() {
        // The RED demonstration, standing. `driftedSkylinePin` is pin 5 moved 1.1 km towards the CA-92
        // junction - perpendicular enough to the ridge leg that the sum barely notices.
        var drifted = Self.expectedPoints
        let index = 4
        #expect(drifted[index] == SkylineRouteTests.skylineSouthOfCA92, "index \(index) is not pin 5")
        drifted[index] = Self.driftedSkylinePin

        let drift = Geo.distanceMeters(Self.expectedPoints[index], Self.driftedSkylinePin)
        #expect(drift > Self.pinDriftToleranceMeters,
                "the drifted pin is only \(drift) m away, so it does not demonstrate anything")

        // And this is why that bound is not written on the total: the total moves by about a metre and
        // the floored figure does not move at all.
        let metres = StraightLineDistance.meters(through: drifted)
        #expect(abs(metres - Self.straightLineMeters) < Self.pinDriftToleranceMeters,
                "the total moved \(abs(metres - Self.straightLineMeters)) m, which a kilometre band WOULD catch")
        #expect(StraightLineDistance.wholeKilometers(through: drifted) == Self.straightLineKilometers,
                "the floored figure moved to \(StraightLineDistance.wholeKilometers(through: drifted)) km")
    }
}
