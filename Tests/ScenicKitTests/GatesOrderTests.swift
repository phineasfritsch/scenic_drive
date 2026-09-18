import Foundation
import Testing
@testable import ScenicKit

/// Rule ORDER is behaviour, not formatting: `ops/route-autopsy` is specified to read whichever reason fired,
/// so hoisting one rule above another changes what a driver is told about a road that trips both.
///
/// `theFirstRuleToFireIsTheReasonReported` in `GatesTests` pins five hand-picked two-rule ways. The second
/// review of PR #82 walked past it twice - hoisting the locked-barrier rule above the access rule, and the
/// smoothness rule above the `highway=track` rule - because neither of those pairs was among the five. This
/// file pins the property instead of the samples: **every earlier rule beats every later rule**, for all 35
/// combinable ordered pairs of the nine rules.
@Suite("Gates rule order")
struct GatesOrderTests {

    /// The rules of `Gates.decide` in the order that function documents, each with a tag set that trips that
    /// rule and no other, and the reason it must report.
    ///
    /// Every field is a written-out literal. Nothing here is read back from `Gates`: an order table derived
    /// from the implementation would agree with whatever order the implementation happened to have.
    static let rulesInOrder: [(name: String, tags: [String: String], reason: GateReason)] = [
        ("unpaved surface", ["surface": "gravel"], .unpavedSurface),
        ("highway=track", ["highway": "track"], .track),
        ("tracktype grade3 or worse", ["tracktype": "grade4"], .track),
        ("smoothness worse than intermediate", ["smoothness": "bad"], .tooRough),
        ("access closed to the public", ["access": "private"], .noAccess),
        ("motor_vehicle=no", ["motor_vehicle": "no"], .noAccess),
        ("a locked barrier", ["barrier": "gate", "locked": "yes"], .lockedBarrier),
        ("a ford", ["ford": "yes"], .ford),
        ("a refused service way", ["highway": "service", "service": "driveway"], .serviceWay),
    ]

    @Test("every earlier rule beats every later rule, over all 35 combinable pairs")
    func everyEarlierRuleBeatsEveryLaterRule() {
        let rules = Self.rulesInOrder
        var asserted = 0
        var skippedForKeyCollision = 0

        for i in rules.indices {
            for j in rules.indices where j > i {
                // Two rules written on the SAME tag key cannot both be tripped by one way: `highway=track`
                // and `highway=service` are the only such pair, and merging them would silently test the
                // later rule alone. Skipped deliberately AND counted, because a collision test that started
                // matching everything would otherwise turn this whole suite into a pass over zero ways.
                if rules[i].tags.keys.contains(where: { rules[j].tags[$0] != nil }) {
                    skippedForKeyCollision += 1
                    continue
                }
                var tags = rules[i].tags
                for (key, value) in rules[j].tags { tags[key] = value }
                #expect(Gates.decide(tags) == .refused(rules[i].reason),
                        "a way tripping '\(rules[i].name)' and '\(rules[j].name)' reports the earlier one")
                asserted += 1
            }
        }

        // Literals, not `rules.count * (rules.count - 1) / 2`: the point is that the number of pairs actually
        // asserted is pinned, so a merge or a collision check that quietly dropped pairs cannot read green.
        #expect(asserted == 35, "35 of the 36 ordered pairs are combinable")
        #expect(skippedForKeyCollision == 1, "only highway=track vs highway=service collides on a key")
    }
}
