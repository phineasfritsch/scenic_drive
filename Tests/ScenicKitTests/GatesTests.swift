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
///
/// ## What the motorway pin covers, and what it does not
///
/// The review of PR #82 refuted the first version of this file. It pinned five specific tag dictionaries, and
/// only `motorway` got a realistic-tag form, so a refusal keyed on a SECOND tag was invisible: inserting
/// `if tags["highway"] == "motorway_link", tags["oneway"] == "yes" { return .refused(.noAccess) }` - which
/// refuses every freeway ramp there is - left the suite green. `motorroad = yes` did the same for trunk.
///
/// `freewayTagsNeverGate` below crosses the four freeway `highway` values with the companion tags a freeway
/// really carries in OSM. Every one of those inputs is a written-out literal and the expected side is the
/// literal `.allowed`; nothing is read back from `Gates`. That kills both refuted branches and the class they
/// belong to. It does **not** make a motorway refusal structurally impossible: a branch keyed on a tag no
/// case below supplies would still be invisible, and `noMotorwayReasonExists` does not close that gap either,
/// because a refusal can reuse an existing `GateReason` instead of adding one. `ops/mutate/gates.py` carries a
/// mutation for each shape that has actually been proposed.
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

    @Test("no freeway tag combination is gated, not just the bare highway value")
    func freewayTagsNeverGate() {
        // The four freeway values crossed with the companion tags they really carry. Both arrays are written
        // out here; neither is read from Gates, and the expected side is the literal `.allowed`, so this
        // assertion does not hold for an arbitrary rule set - it holds only for one that refuses none of
        // these 52 ways.
        let freewayHighways = ["motorway", "motorway_link", "trunk", "trunk_link"]
        let companions: [[String: String]] = [
            [:],
            ["oneway": "yes"],
            ["motorroad": "yes"],
            ["lanes": "4"],
            ["maxspeed": "65 mph"],
            ["toll": "yes"],
            ["bridge": "yes"],
            ["tunnel": "yes"],
            ["junction": "roundabout"],
            ["ref": "I 280"],
            ["surface": "asphalt"],
            ["smoothness": "excellent"],
            ["oneway": "yes", "motorroad": "yes", "surface": "asphalt",
             "lanes": "4", "maxspeed": "65 mph", "ref": "I 280"],
        ]
        for highway in freewayHighways {
            for companion in companions {
                var tags = companion
                tags["highway"] = highway
                #expect(Gates.decide(tags) == .allowed,
                        "highway=\(highway) with \(companion.keys.sorted()) must not be gated")
            }
        }
    }

    @Test("a one-way freeway ramp is never gated, or no shoulder is reachable at all")
    func onewayRampIsNeverGated() {
        // `motorway_link` ways are one-way ramps and carry `oneway = yes` as a matter of course. Refusing
        // them refuses every on-ramp and off-ramp, so the freeway shoulder in the middle of a long scenic
        // drive becomes unreachable even though the shoulder itself was never refused.
        #expect(Gates.decide(["highway": "motorway_link", "oneway": "yes", "surface": "asphalt"]) == .allowed)
        #expect(Gates.decide(["highway": "trunk_link", "oneway": "yes"]) == .allowed)
    }

    @Test("motorroad=yes is never gated, because that is how a trunk expressway is tagged")
    func motorroadIsNeverGated() {
        // `motorroad = yes` is the ordinary tagging for trunk-grade expressways - exactly the "penalise,
        // never exclude" class, and not a safety fact about the road surface.
        #expect(Gates.decide(["highway": "trunk", "motorroad": "yes"]) == .allowed)
        #expect(Gates.decide(["highway": "motorway", "motorroad": "yes"]) == .allowed)
    }

    @Test("no GateReason exists that could refuse a motorway")
    func noMotorwayReasonExists() {
        // Written out as the complete expected set, in a literal, rather than as a count or as a filter over
        // GateReason.allCases. A count would pass when one reason was swapped for another; a filter over the
        // enum would be asking the thing under test what it contains.
        //
        // This asserts exactly what its name says and no more: that no case is NAMED for a motorway. It is
        // not a guarantee that a motorway cannot be refused, because a new branch can reuse `.noAccess` - see
        // the suite comment. `ops/mutate/gates.py` carries the mutation that adds a case, so this test has
        // been seen red.
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

    @Test("highway=track is refused whatever else it carries, because track is an unconditional gate")
    func trackIsRefusedRegardlessOfItsOtherTags() {
        // Every case in `trackIsRefused` supplies either `highway = track` with no tracktype, or a tracktype
        // on `highway = residential`, and nothing combined them - so narrowing the track rule to
        // `tracktype != "grade1"` made a graded track routable with no test objecting. The plan makes
        // `highway = track` a hard safety gate independent of how well graded the track is.
        #expect(Gates.decide(["highway": "track", "tracktype": "grade1"]) == .refused(.track))
        #expect(Gates.decide(["highway": "track", "tracktype": "grade2"]) == .refused(.track))
        #expect(Gates.decide(["highway": "track", "surface": "asphalt"]) == .refused(.track))
        #expect(Gates.decide(["highway": "track", "smoothness": "excellent"]) == .refused(.track))
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

    @Test("every refused service value is refused, and a service road that is not one is allowed")
    func serviceWaysAreRefused() {
        // All four members of `refusedServiceValues`, written out. The first version of this test named two
        // of them, so shrinking the set to those two changed behaviour with nothing objecting.
        #expect(Gates.decide(["highway": "service", "service": "driveway"]) == .refused(.serviceWay))
        #expect(Gates.decide(["highway": "service", "service": "parking_aisle"]) == .refused(.serviceWay))
        #expect(Gates.decide(["highway": "service", "service": "drive-through"]) == .refused(.serviceWay))
        #expect(Gates.decide(["highway": "service", "service": "emergency_access"]) == .refused(.serviceWay))
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

    @Test("a way that trips two rules reports the first one in the documented order")
    func theFirstRuleToFireIsTheReasonReported() {
        // `Gates.decide` documents its rule order as "the order of the reasons a person would want to hear
        // first", and `ops/route-autopsy` is specified to read exactly that reason - so which rule wins is
        // behaviour, not formatting. No test used to supply a way that tripped more than one rule, so
        // hoisting the ford rule above the surface rule changed every gravel ford's reported reason from
        // `.unpavedSurface` to `.ford` with nothing objecting.
        #expect(Gates.decide(["surface": "gravel", "ford": "yes"]) == .refused(.unpavedSurface))
        #expect(Gates.decide(["highway": "track", "access": "private"]) == .refused(.track))
        #expect(Gates.decide(["surface": "dirt", "highway": "track"]) == .refused(.unpavedSurface))
        #expect(Gates.decide(["smoothness": "bad", "motor_vehicle": "no"]) == .refused(.tooRough))
        #expect(Gates.decide(["highway": "service", "service": "driveway",
                              "barrier": "gate", "locked": "yes"]) == .refused(.lockedBarrier))
    }
}
