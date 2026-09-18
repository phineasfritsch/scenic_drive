import Foundation
import Testing
import ScenicKit
@testable import Handoff

/// The second half of the drive: the Cañada/CA-92 junction, west and up CA-92 onto the Skyline
/// ridge, then south along CA-35 past Sky Londa to the turn-around.
///
/// ## Why this is a suite of its own
///
/// It was written inside `SkylineRouteTests` first and put that file at 320 lines, over CLAUDE.md's
/// 300-line cap. The leg is also a different question from "are these the seven verified pins": this
/// suite asks only whether the ridge goes unpinned. The seven literals stay in `SkylineRouteTests`,
/// which is the one place they are typed out against the shipped array; this file reads them from
/// there rather than typing them a third time, and reuses that suite's own great-circle helper
/// (`metresApart`, the spherical law of cosines, deliberately not `ScenicKit.Geo`) so there is one
/// formula behind both bounds and not two that could drift apart.
///
/// ## The rule this suite exists for
///
/// No scenic leg between consecutive pins goes unpinned. Before this suite the last pin before the
/// ridge stood on CA-92, 242 m from the Cañada junction pin - two pins on one junction - and the
/// CA-92 climb and the whole northern ridge behind it carried none. A drive that drops off the ridge,
/// runs down to I-280 and comes back up CA-84 reaches every remaining pin in order, which is the
/// shortcut the product exists to avoid. `theCA35PinIsWhatKeepsTheRidgeBound` is that arrangement,
/// measured and refused.
@Suite("The Skyline route's ridge leg")
struct SkylineRidgeLegTests {

    /// The leg, typed out from `SkylineRouteTests`' literals in driving order.
    ///
    /// `theRidgeLegIsWhereThisTestThinksItIs` is what ties it to the array the app hands Apple Maps,
    /// so a reordering of the route cannot leave the spacing test measuring a different leg.
    static let ridgeLeg: [Coordinate] = [
        SkylineRouteTests.canadaRoadAt92,
        SkylineRouteTests.skylineSouthOfCA92,
        SkylineRouteTests.skylineRidge,
        SkylineRouteTests.skylineSouthOfSkyLonda,
    ]

    /// NOT a pin. This is where the last pin before the ridge used to be: CA-92, 242 m from the
    /// junction pin, on the other road. It is kept as a literal because `theCA35PinIsWhatKeepsTheRidgeBound`
    /// measures the leg it produced, which is the leg the bound below refuses.
    static let retiredHalfMoonBayRoadPin = Coordinate(latitude: 37.50745, longitude: -122.34299)

    /// THE BOUND. No two consecutive pins on the ridge leg may be further apart than this.
    ///
    /// Thirteen kilometres is a ceiling, not a measurement, and it is deliberately looser than the
    /// Cañada leg's six: the ridge IS long, and CA-35 between CA-92 and Sky Londa has no decision
    /// point every six kilometres to pin. What the number says is that the CA-92 climb and the
    /// northern ridge may not be ONE unpinned gap, which is what they were while the pin before the
    /// ridge stood on CA-92 beside the Cañada junction instead of on CA-35 below it. Both gaps are
    /// printed, on every run and in both directions: the one this bound refuses by
    /// `theCA35PinIsWhatKeepsTheRidgeBound`, the one the shipped pins leave by
    /// `maxSpacingOnTheRidgeLeg`.
    ///
    /// The headroom between those two numbers is much thinner than on the Cañada leg. That is the
    /// honest state of this leg and not a reason to widen the bound: one more pin on CA-35 - the
    /// Kings Mountain Road junction is the candidate - is what would let it come down, and T-0151's
    /// log carries that under STILL OPEN.
    static let ridgeLegMaxSpacingMeters = 13_000.0

    /// The leg as it appears in the shipped array, located by its two typed-out END POINTS rather
    /// than by an index pair, for the reason `SkylineRouteTests.canadaLegAsShipped` gives: with
    /// indices written out, deleting a pin slides the window onto a leg nobody asked about.
    static func ridgeLegAsShipped() -> [Coordinate] {
        SkylineRouteTests.legAsShipped(from: SkylineRouteTests.canadaRoadAt92,
                                       to: SkylineRouteTests.skylineSouthOfSkyLonda)
    }

    @Test("the ridge leg is the slice this test thinks it is")
    func theRidgeLegIsWhereThisTestThinksItIs() {
        let slice = Self.ridgeLegAsShipped()
        #expect(slice == Self.ridgeLeg, "got \(slice)")
    }

    @Test("no gap on the CA-92 climb and the ridge is wider than the bound")
    func maxSpacingOnTheRidgeLeg() {
        // Measured over the array the app actually hands Apple Maps, not over this file's fixtures -
        // `theRidgeLegIsWhereThisTestThinksItIs` is what proves those are the same four pins.
        let leg = Self.ridgeLegAsShipped()
        let gaps = SkylineRouteTests.spacings(leg)
        let widest = gaps.max() ?? .infinity
        #expect(widest < Self.ridgeLegMaxSpacingMeters,
                "widest gap on the ridge leg is \(widest) m, bound \(Self.ridgeLegMaxSpacingMeters) m; gaps were \(gaps)")
    }

    @Test("the CA-35 pin is what keeps that bound: with the old CA-92 pin the gap is over it")
    func theCA35PinIsWhatKeepsTheRidgeBound() {
        // The RED demonstration, standing. Same arithmetic on this file's own literals, so the reason
        // the bound holds is stated rather than folklore, and a future edit that slides the CA-35 pin
        // back up towards the junction until the bound is trivially met has to fail one of the two.
        let withOldPin = [SkylineRouteTests.canadaRoadAt92,
                          Self.retiredHalfMoonBayRoadPin,
                          SkylineRouteTests.skylineRidge,
                          SkylineRouteTests.skylineSouthOfSkyLonda]
        let widest = SkylineRouteTests.spacings(withOldPin).max() ?? 0
        #expect(widest > Self.ridgeLegMaxSpacingMeters,
                "with the old CA-92 pin the widest gap is \(widest) m, not over the \(Self.ridgeLegMaxSpacingMeters) m bound")
    }
}
