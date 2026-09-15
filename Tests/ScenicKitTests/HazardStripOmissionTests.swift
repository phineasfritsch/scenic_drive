import Foundation
import Testing
@testable import ScenicKit

/// Everything about a hazard GOING MISSING, split out of `HazardStripTests` when that file reached the
/// 300-line cap.
///
/// Three review rounds have now found the same shape of defect here and only here, which is why it is worth
/// its own file: a hazard can be lost at the BOTTOM of a range (below a threshold), at the TOP of one (a
/// silent ceiling), at the END of the strip (a truncating cap), or for missing a piece of METADATA that is
/// not the hazard itself (an unattributed closure). The last of those shipped in PR #80 and is fixed here.
///
/// The fixture helper deliberately stays in `HazardStripTests` rather than being copied: one date fixture,
/// not two that can drift. `ops/mutate/hazards.py` empties BOTH files for `--prove-vacuity`, and refuses if
/// a grep finds any third test file that mentions the subject.
@Suite("Hazard strip - nothing goes missing")
struct HazardStripOmissionTests {

    // MARK: - nothing is dropped for being unclassifiable

    @Test("a tag this version cannot classify surfaces instead of vanishing")
    func unclassifiedSurfaces() {
        // The alternative is silent omission, and a strip that quietly drops a hazard is worse than no
        // strip because the driver has learned to trust it.
        let flags = HazardStrip.flags(for: .init(unclassified: ["avalanche_gate", "seasonal_closure"]))
        #expect(flags == [.unrecognised("avalanche_gate"), .unrecognised("seasonal_closure")])
    }

    @Test("the same unknown tag on forty edges is one line, not forty")
    func unclassifiedIsDeduplicated() {
        let facts = HazardStrip.RouteFacts(unclassified: Array(repeating: "quarry_access", count: 40))
        #expect(HazardStrip.flags(for: facts) == [.unrecognised("quarry_access")])
    }

    @Test("an unrecognised tag outranks the advisories, because nobody has judged it")
    func unrecognisedOutranksAdvisories() {
        let facts = HazardStrip.RouteFacts(surfaceUnknownKm: 30, noCellMinutes: 60,
                                           unclassified: ["mystery"])
        #expect(HazardStrip.flags(for: facts).first == .unrecognised("mystery"))
    }

    // MARK: - nothing is dropped for missing its ATTRIBUTION
    //
    // The two empty strings in this file do not mean the same thing. For an unclassified tag the string IS
    // the hazard, so an empty one is nothing at all. For a closure the string is only the provenance, and
    // the hazard is the closure the router reported - at severity rank 0, "the route does not go through".

    @Test("an empty unknown TAG is not a hazard, because there the string IS the hazard")
    func emptyStringsIgnored() {
        #expect(HazardStrip.flags(for: .init(unclassified: ["", "  "])).count == 1,
                "a blank tag is not a hazard, but a whitespace one is still unknown text")
        // This test used to end by asserting that a closure with an empty SOURCE produced nothing, which
        // pinned a rank-0 hazard silently vanishing. `unattributedClosureReachesTheStrip` now pins the
        // opposite, and `ops/mutate/hazards.py` carries the mutation that reinstates the dropping.
    }

    @Test("a closure with no source at all still reaches the strip, and still sorts first")
    func unattributedClosureReachesTheStrip() {
        // The feed forgetting to name itself is not evidence that the road is open. Expectations written
        // out by hand; nothing here reads `severityRank` or any constant of the type under test.
        let alone = HazardStrip.RouteFacts(closures: [(source: "", until: HazardStripTests.date(18))])
        #expect(HazardStrip.flags(for: alone) == [.closure(source: "", until: HazardStripTests.date(18))])

        // Not demoted to `.unrecognised` either: that would move the most consequential flag there is below
        // a ford and a gate, which is the same loss in slower motion.
        let amongOthers = HazardStrip.RouteFacts(surfaceUnknownKm: 9, hasFord: true, hasGate: true,
                                                 closures: [(source: "", until: nil)],
                                                 unclassified: ["quarry_access"])
        let flags = HazardStrip.flags(for: amongOthers)
        #expect(flags.count == 5)
        #expect(flags.first == .closure(source: "", until: nil), "unattributed, and still the first line")

        // An unnamed feed and a named one report the same number of hazards for the same route.
        #expect(HazardStrip.flags(for: .init(closures: [(source: "", until: nil)])).count
                == HazardStrip.flags(for: .init(closures: [(source: "511 SF Bay", until: nil)])).count)
    }

    @Test("a closure whose source is only whitespace still reaches the strip")
    func whitespaceSourcedClosureReachesTheStrip() {
        // Pins WHERE a source guard would cut if one were reintroduced: `unattributedClosureReachesTheStrip`
        // pins that "" survives, and this pins that "   " survives, so neither an `isEmpty` guard nor a
        // `trimmingCharacters` one can come back without a named test objecting.
        let facts = HazardStrip.RouteFacts(closures: [(source: "   ", until: HazardStripTests.date(18))])
        #expect(HazardStrip.flags(for: facts) == [.closure(source: "   ", until: HazardStripTests.date(18))])
    }

    // MARK: - nothing is dropped at the TOP of a range, or off the END of the strip
    //
    // Every fixture outside this file probes a threshold just above its FLOOR and tops out at seven flags,
    // which is also the number of flag KINDS - so a ceiling could be added to any advisory, or the strip
    // truncated, and no assertion would move. A hazard dropped for being too big is the same failure as one
    // dropped for having no source.

    @Test("nine hazards on one route all reach the strip; nothing is truncated")
    func nothingIsTruncated() {
        // Nine is counted from the inputs below BY HAND - 2 closures + ford + gate + 2 distinct unknown
        // tags + noCell + twilight + surface - and is deliberately more than the seven flag kinds.
        // The closures and the tags are also fed in the OPPOSITE order to the one expected out.
        let facts = HazardStrip.RouteFacts(
            surfaceUnknownKm: 12,
            noCellMinutes: 45,
            hasFord: true,
            hasGate: true,
            closures: [(source: "511 SF Bay", until: HazardStripTests.date(18)),
                       (source: "Caltrans D4", until: nil)],
            arrival: HazardStripTests.date(21),
            civilTwilight: HazardStripTests.date(19),
            unclassified: ["quarry_access", "avalanche_gate"])
        let flags = HazardStrip.flags(for: facts)

        #expect(flags.count == 9)
        guard flags.count == 9 else { return }
        #expect(flags[0] == .closure(source: "511 SF Bay", until: HazardStripTests.date(18)))
        #expect(flags[1] == .closure(source: "Caltrans D4", until: nil))
        #expect(flags[2] == .ford)
        #expect(flags[3] == .gate)
        #expect(flags[4] == .unrecognised("avalanche_gate"), "reported second, shown first: tags sort")
        #expect(flags[5] == .unrecognised("quarry_access"))
        #expect(flags[6] == .noCell(minutes: 45))
        #expect(flags[7] == .twilightArrival(at: HazardStripTests.date(21)))
        #expect(flags[8] == .surfaceUnknown(km: 12))
    }

    @Test("the strip's length follows its input; the cap is not merely moved to the next fixture's size")
    func stripLengthFollowsTheInput() {
        // Two rounds have now pinned the length at ONE number a single fixture happened to produce - seven,
        // then nine - and each time the fix moved the cap instead of removing it (`.prefix(7)` died,
        // `.prefix(9)` survived the whole suite). So the count is SWEPT, and the expected length is
        // arithmetic on the inputs rather than anything read back out of the strip.
        for closureCount in [1, 2, 9, 10, 33, 128, 257] {
            let facts = HazardStrip.RouteFacts(
                surfaceUnknownKm: 12, noCellMinutes: 45, hasFord: true, hasGate: true,
                closures: (0..<closureCount).map { (source: "feed \($0)", until: nil) },
                arrival: HazardStripTests.date(21), civilTwilight: HazardStripTests.date(19),
                unclassified: ["quarry_access"])
            let flags = HazardStrip.flags(for: facts)
            // closures + ford + gate + one unknown tag + noCell + twilight + surface, counted by hand.
            #expect(flags.count == closureCount + 6, "\(closureCount) closures plus six other hazards")
            // A cap truncates the TAIL, and the tail is the advisory nobody would miss in a fixture.
            #expect(flags.last == .surfaceUnknown(km: 12), "with \(closureCount) closures ahead of it")
        }
    }

    @Test("no signal has a floor but no ceiling, all the way to the top of the type")
    func noCellHasNoCeiling() {
        #expect(HazardStrip.flags(for: .init(noCellMinutes: 700)) == [.noCell(minutes: 700)])
        #expect(HazardStrip.flags(for: .init(noCellMinutes: 100_000)) == [.noCell(minutes: 100_000)])
        // The previous round closed a ceiling at 600 by probing 100_000, which only MOVED the magic number:
        // `&& noCellMinutes <= 100_000` still survived the whole suite. `Int.max` is the end of the type, so
        // no ceiling can hide above it - a guard that admits Int.max admits every Int there is.
        #expect(HazardStrip.flags(for: .init(noCellMinutes: Int.max)) == [.noCell(minutes: Int.max)])
    }

    @Test("unsurveyed surface has a floor but no ceiling, all the way to the top of the type")
    func surfaceHasNoCeiling() {
        #expect(HazardStrip.flags(for: .init(surfaceUnknownKm: 150)) == [.surfaceUnknown(km: 150)])
        #expect(HazardStrip.flags(for: .init(surfaceUnknownKm: 100_000)) == [.surfaceUnknown(km: 100_000)])
        // Same reasoning: the largest finite Double, so no finite ceiling can sit above it.
        #expect(HazardStrip.flags(for: .init(surfaceUnknownKm: .greatestFiniteMagnitude))
                == [.surfaceUnknown(km: .greatestFiniteMagnitude)])
    }
}
