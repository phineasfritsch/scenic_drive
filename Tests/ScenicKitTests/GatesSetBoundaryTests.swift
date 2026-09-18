import Foundation
import Testing
@testable import ScenicKit

/// The three rule sets pinned on the side the plan does **not** list, because that is the side a widening
/// escapes through.
///
/// A gate set shrinks the road network. The plan writes each refused set out verbatim - seven `surface`
/// values, four `access` values, `barrier = gate` **with** `locked = yes` - and every value outside those
/// lists is a road this product is allowed to route over. `GatesTests` already pins that boundary for the
/// values somebody happened to think of: `access=permissive`, `smoothness=intermediate`, `service=alley`,
/// `tracktype` grade2, cobblestone and sett. The sixth review of PR #82 stepped straight over it on three
/// values nobody had named, each with `swift test` exit 0 and nothing objecting, and a control red proving
/// the mutant really refused a road:
///
///   * `unpavedSurfaces + "wood", "metal"` - every planked or metal-grid bridge deck.
///   * `closedAccess + "customers"` - every lane signed for customers.
///   * the barrier rule widened to `barrier = lift_gate` - every locked boom barrier.
///
/// **This suite does not claim those three widenings are wrong.** Refusing a locked lift gate may well be
/// the right product change one day. It claims something narrower and checkable: the refused sets are the
/// plan's lists and nothing else, so widening one has to be a deliberate, reviewed edit that turns a named
/// test red - not a "be thorough" tidy-up that ships in silence. `ops/mutate/gates_corpus_sets.py` carries
/// one mutation per pin, so each of the three has been seen red.
///
/// Every input below is a written-out literal and every expectation is the literal `.allowed`. Nothing is
/// read back from `Gates.unpavedSurfaces`, `Gates.closedAccess` or any other property of the rule set under
/// test, which would assert a set against itself.
///
/// The three value tests above are an ENUMERATION and were shipped claiming a class: round 7 of PR #82 added
/// `surface=grass`, `access=delivery` and `barrier=swing_gate` and all three passed with nothing objecting.
/// "The plan's lists and nothing else" is only checkable as an EQUALITY against the list written out, which
/// is what `theRefusedSetsAreExactlyThePlansLists` does - the expected side is typed here, not read back.
///
/// WHAT THAT PINS, AND WHAT IT DOES NOT. The equality is on the SIX SET OBJECTS a refusal is driven by, and
/// on nothing else: `unpavedSurfaces`, `closedAccess`, `refusableBarriers`, `refusedTracktypes`,
/// `refusedSmoothness`, `refusedServiceValues`. It pinned the first three only until round 8 of PR #82,
/// while this paragraph already said "the sets": agent/rv8b-pr82 widened `refusedServiceValues` with
/// `"bus"` and the whole suite stayed green, a hard safety gate moving in silence with a control red
/// proving `highway=service` + `service=bus` really went from `.allowed` to `.refused(.serviceWay)`.
/// A widening written into the rule instead of the set - `unpavedSurfaces.contains(surface) || surface ==
/// "mud"` - is still not seen by it: round 7b of PR #82 measured three such edits shipping with 43 tests
/// green and a control red for each. So "widening one has to be a deliberate, reviewed edit that turns a
/// named test red" is true of the six sets and not of the refusal's behaviour; the behaviour is pinned only
/// where a test names a value. Said here rather than implied, because two successive versions of this
/// header claimed more than the code below measured.
@Suite("Gates set boundaries")
struct GatesSetBoundaryTests {

    @Test("a wooden or metal bridge deck is allowed, because a deck is not an unpaved road")
    func bridgeDeckSurfacesAreNotUnpaved() {
        // `surface=wood` is the decking on every covered bridge and boardwalk crossing, and `surface=metal`
        // the grid deck on a lift or truss bridge. Both are carriageways that a sedan drives over at speed;
        // neither is positive evidence of an unpaved road. They are not in the plan's seven-value list.
        #expect(Gates.decide(["surface": "wood"]) == .allowed)
        #expect(Gates.decide(["surface": "metal"]) == .allowed)
        #expect(Gates.decide(["highway": "unclassified", "surface": "wood", "bridge": "yes"]) == .allowed)
        #expect(Gates.decide(["highway": "tertiary", "surface": "metal", "bridge": "yes"]) == .allowed)
    }

    @Test("access=customers is allowed, because the closed set is the plan's four values and no more")
    func customersAccessIsNotClosedAccess() {
        // The plan's closed set is private, no, permit, destination. `customers` is a sign about who the
        // road is for, not a barrier, and a scenic lane past a winery or a lodge commonly carries it.
        // Adding it here would be a product decision; it must not arrive as a widening nobody noticed.
        #expect(Gates.decide(["access": "customers"]) == .allowed)
        #expect(Gates.decide(["highway": "service", "service": "alley", "access": "customers"]) == .allowed)
        // The neighbouring values on both sides, so this cannot pass by allowing everything.
        #expect(Gates.decide(["access": "private"]) == .refused(.noAccess))
        #expect(Gates.decide(["access": "destination"]) == .refused(.noAccess))
    }

    @Test("a locked lift gate is allowed, because the barrier rule names barrier=gate and nothing else")
    func onlyBarrierGateIsARefusableBarrier() {
        // The plan's rule is `barrier = gate` WITH `locked = yes`. A boom barrier, a bollard and a cattle
        // grid are different objects with different consequences, and the hazard strip is what tells the
        // driver they are there. Widening this rule is exactly the edit that must not be silent.
        #expect(Gates.decide(["barrier": "lift_gate", "locked": "yes"]) == .allowed)
        #expect(Gates.decide(["barrier": "bollard", "locked": "yes"]) == .allowed)
        #expect(Gates.decide(["barrier": "cattle_grid"]) == .allowed)
        // The one shape that IS refused, written out beside them.
        #expect(Gates.decide(["barrier": "gate", "locked": "yes"]) == .refused(.lockedBarrier))
    }

    @Test("the refused sets are exactly the plan's lists - an equality, not a sample of widenings")
    func theRefusedSetsAreExactlyThePlansLists() {
        // The right-hand sides are the plan's tables, typed out. All SIX sets whose MEMBERSHIP refuses a way
        // are here. `Gates` declares seven `Set<String>`s in all; the seventh, `consideredTagKeys`, narrows
        // what a rule can read rather than refusing anything, and `GatesInvariantTests` pins it the same way.
        // So any value added to any of them - grass, delivery, swing_gate, bus, or one nobody has thought
        // of - turns this red by name, which the three tests above could not promise: each of them pins only
        // the widenings its author imagined. Until round 8 of PR #82 the last three lines were missing while
        // the name and the header claimed all six, and `refusedServiceValues + "bus"` shipped in silence.
        #expect(Gates.unpavedSurfaces == ["gravel", "dirt", "ground", "sand", "unpaved", "compacted", "fine_gravel"])
        #expect(Gates.closedAccess == ["private", "no", "permit", "destination"])
        #expect(Gates.refusableBarriers == ["gate"])
        #expect(Gates.refusedTracktypes == ["grade3", "grade4", "grade5"])
        #expect(Gates.refusedSmoothness == ["bad", "very_bad", "horrible", "very_horrible", "impassable"])
        #expect(Gates.refusedServiceValues == ["driveway", "parking_aisle", "drive-through", "emergency_access"])
        // And the values round 7 used to show the enumeration was not a class, so the record has them.
        #expect(Gates.decide(["surface": "grass"]) == .allowed)
        #expect(Gates.decide(["access": "delivery"]) == .allowed)
        #expect(Gates.decide(["barrier": "swing_gate", "locked": "yes"]) == .allowed)
        // And the value round 8 used, which no shipped test objected to before these three equalities.
        #expect(Gates.decide(["highway": "service", "service": "bus"]) == .allowed)
    }
}
