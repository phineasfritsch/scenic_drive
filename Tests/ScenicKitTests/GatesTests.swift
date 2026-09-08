import Foundation
import Testing
@testable import ScenicKit

/// Two claims are tested here and neither may be allowed to prove the other:
///
///   1. every safety gate fires on its own positive evidence, and
///   2. **no gate fires on a motorway, or on an absent tag.**
///
/// The second is the one that matters. CLAUDE.md lists the motorway rule first among the invariants not to
/// optimize away, and this repository has already broken it once. So it is asserted with written-out literals
/// and never through `Gates.unpavedSurfaces`, `GateReason.allCases`, or any other property of the rule set
/// under test - an expectation derived from the rules would hold for whatever rules happened to exist.
@Suite("Gates")
struct GatesTests {

    // MARK: - THE INVARIANT

    @Test("a motorway is never gated, because freeway shoulders carry every long scenic drive")
    func motorwayIsNeverGated() {
        // The failure this pins is not hypothetical: a whole-route freeway exclusion made the flagship
        // Mountain View -> SF fixture unroutable. Every Bay Area commute over 15 km needs freeway shoulders
        // around a scenic middle - 280, then Cañada, then Skyline. A motorway is DULL, which is the scoring
        // function's business; it is not UNSAFE, which is this file's.
        #expect(Gates.decide(["highway": "motorway"]) == .allowed)
        #expect(Gates.decide(["highway": "motorway_link"]) == .allowed)
        #expect(Gates.decide(["highway": "trunk"]) == .allowed)
        #expect(Gates.decide(["highway": "trunk_link"]) == .allowed)

        // With the tags a real freeway carries, not just the bare one.
        #expect(Gates.decide(["highway": "motorway", "surface": "asphalt", "lanes": "4",
                              "maxspeed": "65 mph", "oneway": "yes"]) == .allowed)
    }

    @Test("no GateReason exists that could refuse a motorway")
    func noMotorwayReasonExists() {
        // Written out as the complete expected set, in a literal, rather than as a count or as a filter over
        // GateReason.allCases. A count would pass when one reason was swapped for another; a filter over the
        // enum would be asking the thing under test what it contains.
        #expect(Set(GateReason.allCases.map(\.rawValue)) == Set([
            "unpavedSurface", "track", "tooRough", "noAccess", "lockedBarrier", "ford", "serviceWay",
        ]))
    }

    // MARK: - absent is not negative

    @Test("a road with no surface tag is allowed, because most rural lanes have none")
    func absentSurfaceIsNotUnpaved() {
        // The plan is explicit: absent surface means x0.8 and a `surfaceUnknown` flag, NOT a refusal. A gate
        // on the absent case would refuse the roads this product exists to find.
        #expect(Gates.decide(["highway": "unclassified"]) == .allowed)
        #expect(Gates.decide(["highway": "residential"]) == .allowed)
        #expect(Gates.decide(["highway": "tertiary"]) == .allowed)
        #expect(Gates.decide([:]) == .allowed, "no tags at all is not evidence of anything")
    }

    @Test("every gate stays quiet when its own tag is absent")
    func absentTagsNeverFire() {
        // One case per rule, each with the OTHER tags present so a mistake shows up as this rule firing
        // rather than as an empty dictionary passing trivially.
        #expect(Gates.decide(["highway": "residential", "lanes": "2"]) == .allowed)
        #expect(Gates.decide(["highway": "secondary", "surface": "asphalt"]) == .allowed)
        #expect(Gates.decide(["highway": "primary", "smoothness": "good"]) == .allowed)
        #expect(Gates.decide(["highway": "residential", "access": "yes"]) == .allowed)
        #expect(Gates.decide(["highway": "residential", "motor_vehicle": "yes"]) == .allowed)
        #expect(Gates.decide(["highway": "residential", "ford": "no"]) == .allowed)
        #expect(Gates.decide(["highway": "service"]) == .allowed, "a service way with no service value")
    }

    // MARK: - each gate on its own positive evidence

    @Test("an unpaved surface is refused, and the reason says which rule")
    func unpavedSurfaceIsRefused() {
        // Every value written out. Looping over Gates.unpavedSurfaces would assert the set against itself.
        #expect(Gates.decide(["surface": "gravel"]) == .refused(.unpavedSurface))
        #expect(Gates.decide(["surface": "dirt"]) == .refused(.unpavedSurface))
        #expect(Gates.decide(["surface": "ground"]) == .refused(.unpavedSurface))
        #expect(Gates.decide(["surface": "sand"]) == .refused(.unpavedSurface))
        #expect(Gates.decide(["surface": "unpaved"]) == .refused(.unpavedSurface))
        #expect(Gates.decide(["surface": "compacted"]) == .refused(.unpavedSurface))
        #expect(Gates.decide(["surface": "fine_gravel"]) == .refused(.unpavedSurface))

        // Paved values stay allowed, or the rule is just "has a surface tag".
        #expect(Gates.decide(["surface": "asphalt"]) == .allowed)
        #expect(Gates.decide(["surface": "concrete"]) == .allowed)
        #expect(Gates.decide(["surface": "paved"]) == .allowed)
        #expect(Gates.decide(["surface": "paving_stones"]) == .allowed)
    }

    @Test("a track is refused, by highway or by tracktype")
    func trackIsRefused() {
        #expect(Gates.decide(["highway": "track"]) == .refused(.track))
        #expect(Gates.decide(["highway": "residential", "tracktype": "grade3"]) == .refused(.track))
        #expect(Gates.decide(["highway": "residential", "tracktype": "grade4"]) == .refused(.track))
        #expect(Gates.decide(["highway": "residential", "tracktype": "grade5"]) == .refused(.track))
        // grade1 and grade2 are firm surfaces and are not refused.
        #expect(Gates.decide(["highway": "residential", "tracktype": "grade1"]) == .allowed)
        #expect(Gates.decide(["highway": "residential", "tracktype": "grade2"]) == .allowed)
    }

    @Test("smoothness worse than intermediate is refused, and intermediate itself is not")
    func roughnessIsRefused() {
        #expect(Gates.decide(["smoothness": "bad"]) == .refused(.tooRough))
        #expect(Gates.decide(["smoothness": "very_bad"]) == .refused(.tooRough))
        #expect(Gates.decide(["smoothness": "horrible"]) == .refused(.tooRough))
        #expect(Gates.decide(["smoothness": "very_horrible"]) == .refused(.tooRough))
        #expect(Gates.decide(["smoothness": "impassable"]) == .refused(.tooRough))
        // The boundary, on the allowed side. "worse than intermediate" means intermediate passes.
        #expect(Gates.decide(["smoothness": "intermediate"]) == .allowed)
        #expect(Gates.decide(["smoothness": "good"]) == .allowed)
        #expect(Gates.decide(["smoothness": "excellent"]) == .allowed)
    }

    @Test("access that forbids the public is refused")
    func closedAccessIsRefused() {
        #expect(Gates.decide(["access": "private"]) == .refused(.noAccess))
        #expect(Gates.decide(["access": "no"]) == .refused(.noAccess))
        #expect(Gates.decide(["access": "permit"]) == .refused(.noAccess))
        #expect(Gates.decide(["access": "destination"]) == .refused(.noAccess))
        #expect(Gates.decide(["motor_vehicle": "no"]) == .refused(.noAccess))

        #expect(Gates.decide(["access": "yes"]) == .allowed)
        #expect(Gates.decide(["access": "permissive"]) == .allowed)
        #expect(Gates.decide(["motor_vehicle": "yes"]) == .allowed)
    }

    @Test("a gate is refused only when it is recorded as locked")
    func onlyLockedGatesAreRefused() {
        // The distinction the driver cares about. An unlocked gate may be openable and they can see it; the
        // hazard strip tells them it is there. Refusing every gate would cut off a large share of the ranch
        // and park roads this product is for.
        #expect(Gates.decide(["barrier": "gate", "locked": "yes"]) == .refused(.lockedBarrier))
        #expect(Gates.decide(["barrier": "gate"]) == .allowed, "an unlocked gate is the driver's decision")
        #expect(Gates.decide(["barrier": "gate", "locked": "no"]) == .allowed)
        #expect(Gates.decide(["locked": "yes"]) == .allowed, "locked alone, with no barrier, says nothing")
    }

    @Test("a ford is refused on positive evidence")
    func fordIsRefused() {
        #expect(Gates.decide(["ford": "yes"]) == .refused(.ford))
        #expect(Gates.decide(["ford": "no"]) == .allowed)
    }

    @Test("a driveway is refused; a service road that is not one is allowed")
    func serviceWaysAreRefused() {
        #expect(Gates.decide(["highway": "service", "service": "driveway"]) == .refused(.serviceWay))
        #expect(Gates.decide(["highway": "service", "service": "parking_aisle"]) == .refused(.serviceWay))
        // `service = alley` is a road, and it is not in the refused set.
        #expect(Gates.decide(["highway": "service", "service": "alley"]) == .allowed)
        // The service value alone, without highway=service, is not evidence.
        #expect(Gates.decide(["highway": "residential", "service": "driveway"]) == .allowed)
    }

    // MARK: - the decision carries its reason

    @Test("a refusal names its rule, so an autopsy can say why")
    func refusalCarriesItsReason() {
        #expect(Gates.decide(["surface": "gravel"]).reason == .unpavedSurface)
        #expect(Gates.decide(["ford": "yes"]).reason == .ford)
        #expect(Gates.decide(["highway": "motorway"]).reason == nil)
        #expect(Gates.decide(["highway": "motorway"]).isAllowed)
        #expect(!Gates.decide(["surface": "dirt"]).isAllowed)
    }
}
