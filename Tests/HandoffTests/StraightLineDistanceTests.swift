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

    /// THE NUMBER ON THE SCREEN, in the unit the screen renders (T-0203). Floored whole miles over
    /// the same `expectedPoints` and the same metres as `straightLineKilometers` - 112_268.093 m is
    /// 69.76 international miles - so the two figures cannot be measurements of different chains.
    /// Typed out beside the kilometre literal rather than converted from it: a test that computes the
    /// number it is pinning is pinning nothing.
    static let straightLineMiles = 69

    /// The same measurement before the floor, to a metre. The band is one metre and not one kilometre:
    /// it is here to catch a change in the RADIUS that the floored integer would swallow, not to allow
    /// a pin to move.
    ///
    /// It does NOT catch a change of FORMULA, and the earlier claim that it did was measured false: a
    /// flat equirectangular formula on the same radius totals 112_268.146 m over this chain, 0.053 m
    /// from the haversine and well inside this band. These legs are short and mostly north-south, which
    /// is precisely where the two formulas agree. `aLongEastWestLegPinsTheFormulaAndTheMileConstant` is
    /// where they do not, and it is what stands behind the formula.
    static let straightLineMeters = 112_268.093

    /// A LONG EAST-WEST LEG, and why a synthetic one has to exist. Twelve degrees of longitude at
    /// latitude 37 is 1_064_944.819 m by the shipped haversine. Over that leg the flat formula above is
    /// 1_065_652.075 m - 707.256 m out, and 662 miles against 661 - so one leg the drive does not
    /// contain is what lets the suite tell the arithmetic apart. It is also the only chain here long
    /// enough for a 1 % error in the metres-to-miles constant to cross a whole mile: 1 % of 661 miles is
    /// six and a half of them, while 1 % of the card's 69.76 miles is still 69.
    static let longLegWest = Coordinate(latitude: 37.00000, longitude: -122.00000)
    static let longLegEast = Coordinate(latitude: 37.00000, longitude: -110.00000)
    static let longLegMeters = 1_064_944.819
    static let longLegKilometers = 1_064
    static let longLegMiles = 661

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

    @Test("the whole-mile figure is the number the screen renders, from the same metres")
    func theWholeMileFigureIsTheNumberTheScreenRenders() {
        let miles = StraightLineDistance.wholeMiles(for: .skyline)
        #expect(miles == Self.straightLineMiles, "got \(miles) mi")
        #expect(StraightLineDistance.wholeMiles(through: StraightLineDistance.skylineRoutePoints) == miles,
                "the drive's chain and the shipped chain give different miles")
        // ONE COMPUTATION, TWO RENDERINGS: both figures floor the same metres, so a change to the
        // arithmetic moves both or neither. A mile is 1_609.344 m exactly.
        let metres = StraightLineDistance.meters(through: StraightLineDistance.skylineRoutePoints)
        #expect(Int((metres / 1_609.344).rounded(.down)) == miles, "got \(metres) m")
        #expect(StraightLineDistance.wholeKilometers(for: .skyline) == Self.straightLineKilometers)
    }

    @Test("the miles are floored too: 1.99 miles of chain is 1 mile and never 2")
    func theMilesAreFlooredAndNeverRoundedUp() {
        // 0.02878 degrees of latitude on a meridian is 3200.7 m - 1.988 miles. A round-half-up would
        // print 2 miles, which would be most of a mile nobody measured.
        let a = Coordinate(latitude: 37.00000, longitude: -122.00000)
        let b = Coordinate(latitude: 37.02878, longitude: -122.00000)
        let metres = StraightLineDistance.meters(through: [a, b])
        #expect(metres > 3_100 && metres < 3_219, "got \(metres) m")
        #expect(StraightLineDistance.wholeMiles(through: [a, b]) == 1)
        #expect(StraightLineDistance.wholeMiles(through: []) == 0)
        #expect(StraightLineDistance.wholeMiles(through: [a]) == 0)
    }

    @Test("a 1,065 km east-west leg pins the formula and the mile constant")
    func aLongEastWestLegPinsTheFormulaAndTheMileConstant() {
        // T-0199. Three mutants walked through the shipped chain untouched: a flat equirectangular
        // formula on the same radius (0.053 m over 112 km of short, mostly north-south legs) and the
        // metres-to-miles constant 1 % either way (69.07 and 70.46 miles, both still floored to 69 next
        // to a 69.76 that floors to 69). On this leg the same three are 707 m and six miles. The chain
        // is synthetic on purpose: the drive has no leg long enough to separate them, and a number the
        // screen renders should not be pinned only where its arithmetic happens not to matter.
        let leg = [Self.longLegWest, Self.longLegEast]
        let metres = StraightLineDistance.meters(through: leg)
        #expect(abs(metres - Self.longLegMeters) <= 1, "got \(metres) m, pinned \(Self.longLegMeters) m")
        #expect(StraightLineDistance.wholeKilometers(through: leg) == Self.longLegKilometers,
                "got \(StraightLineDistance.wholeKilometers(through: leg)) km from \(metres) m")
        #expect(StraightLineDistance.wholeMiles(through: leg) == Self.longLegMiles,
                "got \(StraightLineDistance.wholeMiles(through: leg)) mi from \(metres) m")
    }

    @Test("the miles come from the metres, not from the floored kilometres")
    func theMilesComeFromTheMetresAndNotFromTheFlooredKilometres() {
        // T-0199. `wholeMiles(through:)`'s type note says the miles are not converted from the whole
        // kilometres, "that would floor twice and lose up to a mile" - and nothing measured it. Every
        // chain the suite pinned agreed either way: 112 km * 0.621371 is 69.59 -> 69, 47 km is 29.20 ->
        // 29, and the 1.99-mile synthetic is 3.107 -> 3. This is a length where the two disagree.
        // 0.04496 degrees of latitude on a meridian is 4_999.331 m: 3.1064 miles, so the figure is 3.
        // Floor the kilometres first and 4 km * 0.621371 is 2.4855 -> 2, a mile lost to a second floor.
        let a = Coordinate(latitude: 37.00000, longitude: -122.00000)
        let b = Coordinate(latitude: 37.04496, longitude: -122.00000)
        let metres = StraightLineDistance.meters(through: [a, b])
        #expect(metres > 4_900 && metres < 5_000, "got \(metres) m")
        #expect(StraightLineDistance.wholeKilometers(through: [a, b]) == 4)
        #expect(StraightLineDistance.wholeMiles(through: [a, b]) == 3,
                "got \(StraightLineDistance.wholeMiles(through: [a, b])) mi from \(metres) m")
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

    /// THE ENTRY POINT, which is the symbol the screen renders: `wholeMiles(for:)`, not the helper under
    /// it. `DriveFacts` calls this one, and until T-0199's pre-review pass no mutation edited its body -
    /// every entry in the population edits a helper or a dependency, and the two literals above pin the
    /// two shipped figures without ever asking whether the figure a drive gets is measured over THAT
    /// drive's chain.
    ///
    /// Over `allCases` and re-derived from each drive's own metres rather than named drive by named
    /// drive: the case count is asserted so that the day a third drive lands this test grows with the
    /// enum instead of quietly covering two cases of three. That same range is the tripwire on the
    /// EQUIVALENT entry in `ops/mutate/straightline_mutations.py` which rules the double floor AT this
    /// entry point unkillable - unkillable only while the domain is two drives that floor to the same
    /// mile either way, and this is the test that stops being green about it when one of them moves.
    @Test("every drive's miles are that drive's own chain, floored from that drive's metres")
    func everyDrivesMilesAreThatDrivesOwnChain() {
        #expect(HandoffDrive.allCases.count == 3, "the domain wholeMiles(for:) ranges over has changed")
        for drive in HandoffDrive.allCases {
            let metres = StraightLineDistance.meters(through: drive.chain)
            let rendered = StraightLineDistance.wholeMiles(for: drive)
            #expect(rendered == Int((metres / 1_609.344).rounded(.down)),
                    "\(drive.rawValue) renders \(rendered) mi over \(metres) m of its own chain")
            #expect(rendered == StraightLineDistance.wholeMiles(through: drive.chain),
                    "\(drive.rawValue): the entry point and the helper disagree")
        }
        // And the loop is not comparing one drive with itself: three drives, three figures.
        let figures = HandoffDrive.allCases.map { StraightLineDistance.wholeMiles(for: $0) }
        #expect(Set(figures).count == HandoffDrive.allCases.count,
                "two drives render the same miles (\(figures)), so a drive swapped here would be invisible")
    }
}
