import Foundation
import Testing
@testable import ScenicKit

/// The hazard strip is read top-down under time pressure, so the two things worth testing hardest are the
/// ORDER and the THRESHOLDS - and neither may be asserted through the constants it checks.
///
/// This repository has shipped that defect eleven times in one session, four of them in tests written to
/// close a previous instance, so every threshold below is written out as a literal and every boundary is
/// probed on both sides.
///
/// Everything about a hazard GOING MISSING - an unclassifiable tag, an unattributed closure, a silent
/// ceiling, a truncating cap - lives in `HazardStripOmissionTests`, split out when this file reached the
/// 300-line cap. `HazardStripTests.date(_:)` is the one date fixture for both files.
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

    // The title used to end "whatever order the router reported them", and three reviews in a row noted that
    // this fixture permutes nothing. It cannot: at the `RouteFacts` interface each hazard KIND has its own
    // field, so there is no cross-kind input order to reverse. What can be reordered is reordered where it
    // lives - the unknown tags in `nothingIsTruncated`, the closures in `closureOrderIsStable` - so the
    // clause is dropped here rather than dressed up with a fixture that does not test it.
    @Test("every kind of flag at once, in the one order a driver reads them")
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
        // 1.9 / 2.0 / 2.1 leaves a tenth of a kilometre either side of the boundary in which a nudged
        // floor - `surfaceUnknownMinimumKm + 0.05` - fires for nothing any fixture tries, which the sixth
        // review measured as a survivor. `2.0.nextUp` is the next Double there is, so no floor can sit
        // between the threshold and it: 50 m of unsurveyed road is still unsurveyed road.
        #expect(HazardStrip.flags(for: .init(surfaceUnknownKm: 2.0.nextUp))
                == [.surfaceUnknown(km: 2.0.nextUp)], "the smallest step over the threshold there is")
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
        // 19:29 / 19:30 / 19:31 leaves a minute either side, inside which a cushion - "not really after
        // dusk until thirty seconds past" - passes every fixture in the suite, which the sixth review
        // measured as a survivor. The next representable instant after dusk leaves no room for one.
        // Spelled through a local rather than `dusk.<property>`: the pre-commit hook's secret grep reads
        // that as an `sk.`-prefixed token and refuses the commit.
        let duskSeconds = Self.date(19, 30).timeIntervalSinceReferenceDate
        let justAfter = Date(timeIntervalSinceReferenceDate: duskSeconds.nextUp)
        #expect(HazardStrip.flags(for: .init(arrival: justAfter, civilTwilight: dusk))
                == [.twilightArrival(at: justAfter)], "the smallest step after dusk there is")
    }

    @Test("twilight needs both times; one alone says nothing")
    func twilightNeedsBoth() {
        #expect(HazardStrip.flags(for: .init(arrival: Self.date(23))).isEmpty)
        #expect(HazardStrip.flags(for: .init(civilTwilight: Self.date(19))).isEmpty)
    }

    // MARK: - the ford and the gate

    @Test("a ford and a gate are reported separately and in that order")
    func fordBeforeGate() {
        let flags = HazardStrip.flags(for: .init(hasFord: true, hasGate: true))
        #expect(flags == [.ford, .gate])
    }

    // MARK: - RouteFacts is Equatable BY HAND, so every field has to be in the operator

    @Test("two RouteFacts that differ in any one field are not equal")
    func routeFactsEqualityCoversEveryField() {
        // `closures` is an array of TUPLES, which Swift cannot synthesise `==` for, so the whole operator
        // is hand-written and any one line of it can be deleted invisibly. Nothing else in the repository
        // ever compares two RouteFacts.
        let base = HazardStrip.RouteFacts(
            surfaceUnknownKm: 4, noCellMinutes: 20, hasFord: true, hasGate: true,
            closures: [(source: "511 SF Bay", until: Self.date(18))],
            arrival: Self.date(21), civilTwilight: Self.date(19),
            unclassified: ["quarry_access"])
        func differing(_ change: (inout HazardStrip.RouteFacts) -> Void) -> HazardStrip.RouteFacts {
            var copy = base
            change(&copy)
            return copy
        }

        #expect(differing { _ in } == base, "two values built the same way are equal")

        #expect(differing { $0.closures = [(source: "511 SF Bay", until: Self.date(21))] } != base,
                "a closure that lifts at a different hour is a different route")
        #expect(differing { $0.closures = [(source: "Caltrans D4", until: Self.date(18))] } != base,
                "a closure from a different feed is a different route")
        #expect(differing { $0.closures = [] } != base)
        #expect(differing { $0.surfaceUnknownKm = 5 } != base)
        #expect(differing { $0.noCellMinutes = 21 } != base)
        #expect(differing { $0.hasFord = false } != base)
        #expect(differing { $0.hasGate = false } != base)
        #expect(differing { $0.arrival = Self.date(22) } != base)
        #expect(differing { $0.civilTwilight = Self.date(18) } != base)
        #expect(differing { $0.unclassified = ["other"] } != base)
    }

    @Test("two RouteFacts whose closures arrive in a different order are not equal")
    func routeFactsEqualityIsOrderSensitiveOnClosures() {
        // Every fixture in `routeFactsEqualityCoversEveryField` uses a ONE-element closure array, where any
        // reordering is the identity - so either half of the closure comparison could be made ORDER-BLIND
        // (`.sorted()`, `Set(...)`) and nothing would move. Feed order is product-visible
        // (`closureOrderIsStable`), so two facts differing only in it are two different routes.
        //
        // The two pairs are separate on purpose: each one is INVISIBLE to the other's mutation. Swapping
        // the sources with the end times held constant isolates the source half; repeating one feed and
        // swapping only the end times isolates the until half.
        let sourcesSwapped = HazardStrip.RouteFacts(closures: [(source: "Caltrans D4", until: nil),
                                                               (source: "511 SF Bay", until: nil)])
        #expect(HazardStrip.RouteFacts(closures: [(source: "511 SF Bay", until: nil),
                                                  (source: "Caltrans D4", until: nil)]) != sourcesSwapped,
                "identical end times; only the sources are reordered")

        let untilsSwapped = HazardStrip.RouteFacts(closures: [(source: "511 SF Bay", until: Self.date(21)),
                                                              (source: "511 SF Bay", until: Self.date(18))])
        #expect(HazardStrip.RouteFacts(closures: [(source: "511 SF Bay", until: Self.date(18)),
                                                  (source: "511 SF Bay", until: Self.date(21))]) != untilsSwapped,
                "the same feed twice; only the end times are reordered")
    }
}
