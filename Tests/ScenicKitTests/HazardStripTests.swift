import Foundation
import Testing
@testable import ScenicKit

/// The hazard strip is read top-down under time pressure, so the two things worth testing hardest are the
/// ORDER and the THRESHOLDS - and neither may be asserted through the constants it checks.
///
/// This repository has shipped that defect eleven times in one session, four of them in tests written to
/// close a previous instance, so every threshold below is written out as a literal and every boundary is
/// probed on both sides.
@Suite("Hazard strip")
struct HazardStripTests {

    static func date(_ hour: Int, _ minute: Int = 0) -> Date {
        var c = DateComponents()
        c.year = 2026; c.month = 9; c.day = 8; c.hour = hour; c.minute = minute
        c.timeZone = TimeZone(identifier: "UTC")
        var cal = Calendar(identifier: .gregorian)
        cal.timeZone = TimeZone(identifier: "UTC")!
        return cal.date(from: c)!
    }

    // MARK: - nothing wrong says nothing

    @Test("a route with nothing wrong produces an empty strip, not a reassuring flag")
    func cleanRouteIsEmpty() {
        #expect(HazardStrip.flags(for: .init()).isEmpty)
        // Just under every threshold, still nothing.
        let quiet = HazardStrip.RouteFacts(surfaceUnknownKm: 2.0, noCellMinutes: 4)
        #expect(HazardStrip.flags(for: quiet).isEmpty)
    }

    // MARK: - the order, which is the product

    @Test("flags sort by consequence, whatever order the router reported them")
    func orderedByConsequence() {
        let everything = HazardStrip.RouteFacts(
            surfaceUnknownKm: 9,
            noCellMinutes: 30,
            hasFord: true,
            hasGate: true,
            closures: [(source: "511 SF Bay", until: Self.date(18))],
            arrival: Self.date(20),
            civilTwilight: Self.date(19),
            unclassified: ["quarry_access"])
        let flags = HazardStrip.flags(for: everything)

        // Written out as the expected sequence, not derived from severityRank - asserting the order against
        // the property that produces it would hold for any ordering the code happened to have.
        #expect(flags.count == 7)
        guard flags.count == 7 else { return }
        #expect(flags[0] == .closure(source: "511 SF Bay", until: Self.date(18)))
        #expect(flags[1] == .ford)
        #expect(flags[2] == .gate)
        #expect(flags[3] == .unrecognised("quarry_access"))
        #expect(flags[4] == .noCell(minutes: 30))
        #expect(flags[5] == .twilightArrival(at: Self.date(20)))
        #expect(flags[6] == .surfaceUnknown(km: 9))
    }

    @Test("a closure outranks an advisory, which is the whole reason the strip is ordered")
    func closureBeatsAdvisory() {
        let facts = HazardStrip.RouteFacts(surfaceUnknownKm: 40,
                                           closures: [(source: "Caltrans D4", until: nil)])
        let flags = HazardStrip.flags(for: facts)
        #expect(flags.first == .closure(source: "Caltrans D4", until: nil))
        #expect(flags.last == .surfaceUnknown(km: 40))
    }

    @Test("two closures keep the order the feed gave them")
    func closureOrderIsStable() {
        let facts = HazardStrip.RouteFacts(closures: [(source: "511 SF Bay", until: nil),
                                                      (source: "Caltrans D4", until: nil)])
        let flags = HazardStrip.flags(for: facts)
        #expect(flags == [.closure(source: "511 SF Bay", until: nil),
                          .closure(source: "Caltrans D4", until: nil)])
    }

    // MARK: - thresholds, pinned as literals and probed on both sides

    @Test("the surface threshold is 2 km and it is strict")
    func surfaceThreshold() {
        #expect(HazardStrip.surfaceUnknownMinimumKm == 2.0)
        #expect(HazardStrip.flags(for: .init(surfaceUnknownKm: 1.9)).isEmpty)
        #expect(HazardStrip.flags(for: .init(surfaceUnknownKm: 2.0)).isEmpty,
                "exactly the threshold is not over it")
        #expect(HazardStrip.flags(for: .init(surfaceUnknownKm: 2.1)) == [.surfaceUnknown(km: 2.1)])
    }

    @Test("the no-cell threshold is 5 minutes and it is inclusive")
    func noCellThreshold() {
        #expect(HazardStrip.noCellMinimumMinutes == 5)
        #expect(HazardStrip.flags(for: .init(noCellMinutes: 4)).isEmpty)
        #expect(HazardStrip.flags(for: .init(noCellMinutes: 5)) == [.noCell(minutes: 5)],
                "exactly the threshold counts")
        #expect(HazardStrip.flags(for: .init(noCellMinutes: 6)) == [.noCell(minutes: 6)])
    }

    @Test("twilight fires only when arrival is after it")
    func twilightBoundary() {
        let dusk = Self.date(19, 30)
        #expect(HazardStrip.flags(for: .init(arrival: Self.date(19, 29), civilTwilight: dusk)).isEmpty)
        #expect(HazardStrip.flags(for: .init(arrival: dusk, civilTwilight: dusk)).isEmpty,
                "arriving exactly at twilight is not after it")
        #expect(HazardStrip.flags(for: .init(arrival: Self.date(19, 31), civilTwilight: dusk))
                == [.twilightArrival(at: Self.date(19, 31))])
    }

    @Test("twilight needs both times; one alone says nothing")
    func twilightNeedsBoth() {
        #expect(HazardStrip.flags(for: .init(arrival: Self.date(23))).isEmpty)
        #expect(HazardStrip.flags(for: .init(civilTwilight: Self.date(19))).isEmpty)
    }

    // MARK: - nothing is dropped

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

    @Test("empty strings are not hazards")
    func emptyStringsIgnored() {
        #expect(HazardStrip.flags(for: .init(unclassified: ["", "  "])).count == 1,
                "a blank tag is not a hazard, but a whitespace one is still unknown text")
        #expect(HazardStrip.flags(for: .init(closures: [(source: "", until: nil)])).isEmpty)
    }

    // MARK: - the ford and the gate

    @Test("a ford and a gate are reported separately and in that order")
    func fordBeforeGate() {
        let flags = HazardStrip.flags(for: .init(hasFord: true, hasGate: true))
        #expect(flags == [.ford, .gate])
    }
}
