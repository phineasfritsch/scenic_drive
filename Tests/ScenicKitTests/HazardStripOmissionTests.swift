import Foundation
import Testing
@testable import ScenicKit

/// Everything about a hazard GOING MISSING, split out of `HazardStripTests` when that file reached the
/// 300-line cap.
///
/// Five review rounds have now found the same shape of defect here and only here, which is why it is worth
/// its own file: a hazard can be lost at the BOTTOM of a range (below a threshold), at the TOP of one (a
/// silent ceiling), at the END of the strip (a truncating cap), for missing a piece of METADATA that is not
/// the hazard itself (an unattributed closure), for what that metadata SAYS rather than for its absence (a
/// closure that lifts at either end of `Date`), for there being MORE of it than any fixture happened to
/// carry (a third unknown tag, a second closure from one feed), or for its text being LONGER - or SHORTER,
/// once something trims it - than any fixture happened to use. Every one of those was found by a mutation
/// that the suite let through.
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

    // MARK: - nothing is dropped for its METADATA - for missing it, or for what it says
    //
    // The two empty strings in this file do not mean the same thing. For an unclassified tag the string IS
    // the hazard, so an empty one is nothing at all. For a closure the string is only the provenance, and
    // the hazard is the closure the router reported - at severity rank 0, "the route does not go through".
    //
    // `.closure` carries exactly TWO pieces of metadata, `source` and `until`, and a guard on either drops
    // the same rank-0 flag. Both are pinned here, at both ends: `source` empty, whitespace and four
    // thousand characters long; `until` nil and at each end of `Date`.

    @Test("an empty unknown TAG is not a hazard, because there the string IS the hazard")
    func emptyStringsIgnored() {
        // The whitespace tag's TEXT is asserted and not merely its existence. This ended at `.count == 1`,
        // which let `tag.trimmingCharacters(in: .whitespaces)` corrupt "  " into "" with nothing
        // objecting - the sibling of the caught twenty-character truncation, one step less visible
        // because the count does not move.
        #expect(HazardStrip.flags(for: .init(unclassified: ["", "  "])) == [.unrecognised("  ")],
                "a blank tag is not a hazard, but a whitespace one is still unknown text, unaltered")
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

        // BOTH halves of the metadata at their worst at once. This assertion lives here, in the test that
        // owns the empty source, rather than in `closureUntilIsNotAGuard` which owns `until`: putting it
        // there would have made that test a second guard on the empty source, and deleting this one -
        // which is acceptance line 4 - would then have cost nothing and quietly stopped being a red run.
        #expect(HazardStrip.flags(for: .init(closures: [(source: "", until: .distantPast)]))
                == [.closure(source: "", until: .distantPast)])
    }

    @Test("a closure whose source is only whitespace still reaches the strip")
    func whitespaceSourcedClosureReachesTheStrip() {
        // Pins WHERE a source guard would cut if one were reintroduced: `unattributedClosureReachesTheStrip`
        // pins that "" survives, and this pins that "   " survives, so neither an `isEmpty` guard nor a
        // `trimmingCharacters` one can come back without a named test objecting.
        let facts = HazardStrip.RouteFacts(closures: [(source: "   ", until: HazardStripTests.date(18))])
        #expect(HazardStrip.flags(for: facts) == [.closure(source: "   ", until: HazardStripTests.date(18))])
    }

    @Test("a closure reaches the strip whatever its until is, at both ends of the type")
    func closureUntilIsNotAGuard() {
        // The sixth review found this one. `source` was pinned in three directions - empty, whitespace,
        // four thousand characters - and `until`, the OTHER half of the same rank-0 flag's metadata, took
        // three values in the entire suite: nil, 18:00 and 21:00 on one 2026 evening. So a guard reading
        // `where c.until.map({ $0 > <some date> }) ?? true`, or its mirror at the top, passed every
        // fixture there was while a real closure vanished. nil is pinned by the fixtures above; these are
        // the two ends of `Date`, outside which no such guard can hide.
        //
        // Written out rather than swept in a loop, on purpose: the review found this hole with the one-line
        // check `grep -rho "until: [^),]*" Tests/ --include=*.swift`, which returned only `nil` and two
        // hours of one 2026 evening. A loop variable would have answered that grep with `until: until`, and
        // the next person doing the same audit would have had to read the fixture to learn anything.
        #expect(HazardStrip.flags(for: .init(closures: [(source: "511 SF Bay", until: .distantPast)]))
                == [.closure(source: "511 SF Bay", until: .distantPast)], "the bottom of the type")
        #expect(HazardStrip.flags(for: .init(closures: [(source: "511 SF Bay", until: .distantFuture)]))
                == [.closure(source: "511 SF Bay", until: .distantFuture)], "the top of the type")
        // Both halves at their worst at once is pinned by `unattributedClosureReachesTheStrip`, which owns
        // the empty source. Asserting it here as well would make this test a second guard on that, and
        // acceptance line 4 - delete that test, lose exactly two mutations - would stop being red.
    }

    @Test("a closure's until keeps its seconds - the ends of the type do not pin the middle")
    func closureUntilKeepsItsSeconds() {
        // Round 7's reviewer: every `until` fixture was ON THE HOUR, so rounding it to the hour survived.
        let lifts = HazardStripTests.date(18).addingTimeInterval(1830)          // 18:30:30
        #expect(HazardStrip.flags(for: .init(closures: [(source: "511 SF Bay", until: lifts)]))
                == [.closure(source: "511 SF Bay", until: lifts)])
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
        // The TAGS are fed in the opposite order to the one expected out: avalanche_gate is reported second
        // and shown first. The CLOSURES are not, and cannot be - `closureOrderIsStable` makes feed order
        // product-visible, so their expected order IS their input order.
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

    @Test("twilight has a floor but no ceiling: arriving long after dusk is still arriving after dusk")
    func twilightHasNoCeiling() {
        // The fourth review found this one: the other two advisories are probed at the top of their type
        // above, and twilight had no ceiling probe at all. The largest arrival-after-dusk gap anywhere else
        // in the suite is two hours, so `arrival.timeIntervalSince(twilight) <= 7200` passed every fixture.
        let dusk = HazardStripTests.date(19)
        #expect(HazardStrip.flags(for: .init(arrival: HazardStripTests.date(23), civilTwilight: dusk))
                == [.twilightArrival(at: HazardStripTests.date(23))], "four hours after dusk")
        // The end of the type: no finite gap can be a ceiling hiding above `.distantFuture`.
        #expect(HazardStrip.flags(for: .init(arrival: .distantFuture, civilTwilight: dusk))
                == [.twilightArrival(at: .distantFuture)])
    }

    @Test("twilight fires wherever dusk itself falls, at both ends of the type")
    func civilTwilightIsNotAGuard() {
        // Found by the same audit as `closureUntilIsNotAGuard`, and it is the same hole: this flag needs
        // TWO Dates and only `arrival` was ever moved. `twilightHasNoCeiling` takes arrival to the top of
        // the type and leaves dusk at 19:00, and every other twilight fixture puts both times on one 2026
        // evening - so a floor or a ceiling on `civilTwilight` passed the whole suite in both directions
        // while the flag stopped firing.
        #expect(HazardStrip.flags(for: .init(arrival: HazardStripTests.date(21),
                                             civilTwilight: .distantPast))
                == [.twilightArrival(at: HazardStripTests.date(21))], "dusk at the bottom of the type")
        // And as high as dusk can go and still have an arrival after it: `.distantFuture` is the largest
        // Date there is, so dusk one hour below it leaves no room for a ceiling in between.
        #expect(HazardStrip.flags(for: .init(arrival: .distantFuture,
                                             civilTwilight: Date.distantFuture.addingTimeInterval(-3600)))
                == [.twilightArrival(at: .distantFuture)], "dusk one hour below the top of the type")
    }

    // MARK: - nothing is dropped for there being MANY of it, or for being long
    //
    // `stripLengthFollowsTheInput` sweeps the closure count, and the fourth review found the two things a
    // route can have many of that nothing swept: DISTINCT unknown tags (every fixture in the suite used at
    // most two) and CHARACTERS in a string (every closure source in the suite is eleven characters or fewer,
    // and no unknown tag is longer than sixteen). A cap on either is the same failure one step less obvious.

    @Test("every distinct unknown tag reaches the strip; that list is not capped either")
    func everyDistinctUnknownTagReachesTheStrip() {
        // Three written out by hand - one more than any other fixture in the suite uses - and then SWEPT,
        // so the cap cannot be closed by moving it to three the way `.prefix(7)` was moved to `.prefix(9)`.
        #expect(HazardStrip.flags(for: .init(unclassified: ["quarry_access", "seasonal_closure",
                                                            "avalanche_gate"]))
                == [.unrecognised("avalanche_gate"), .unrecognised("quarry_access"),
                    .unrecognised("seasonal_closure")])
        for tagCount in [1, 2, 3, 4, 9, 33, 128] {
            let facts = HazardStrip.RouteFacts(unclassified: (0..<tagCount).map { "unknown_tag_\($0)" })
            #expect(HazardStrip.flags(for: facts).count == tagCount, "\(tagCount) distinct unknown tags in")
        }
    }

    @Test("an unknown tag reaches the strip with its text intact, however long it is")
    func unknownTagTextIsNotTruncated() {
        // A tag is the only flag whose payload IS free text the router chose, so it is the only one that can
        // be quietly SHORTENED rather than quietly dropped. "seasonal_closure_november..." truncated to
        // twenty characters reads as a different hazard, and nothing in the suite noticed.
        let longTag = "seasonal_closure_november_through_april_by_county_ordinance"
        #expect(HazardStrip.flags(for: .init(unclassified: [longTag])) == [.unrecognised(longTag)])
        let absurd = String(repeating: "x", count: 4096)
        #expect(HazardStrip.flags(for: .init(unclassified: [absurd])) == [.unrecognised(absurd)])
    }

    @Test("a closure reaches the strip whatever length its source is")
    func closureSourceLengthIsNotAGuard() {
        // "" and "   " are pinned above; this pins the other end. Every closure source anywhere else in the
        // suite is eleven characters or fewer ("Caltrans D4"), so `where c.source.count <= 11` would pass
        // the whole suite while a real "Caltrans Lane Closure System District 4" polygon vanished.
        for source in ["a", "Caltrans D4", "Caltrans Lane Closure System District 4",
                       String(repeating: "feed ", count: 800)] {
            #expect(HazardStrip.flags(for: .init(closures: [(source: source, until: nil)]))
                    == [.closure(source: source, until: nil)], "a source of \(source.count) characters")
        }
    }

    @Test("two closures from the same feed are two closures, not one")
    func twoClosuresFromOneFeedBothReachTheStrip() {
        // Every other fixture that reaches `flags(for:)` gives each closure a DIFFERENT source, so deduping
        // closures by source - the treatment the unknown TAGS get eight lines below in the derivation -
        // would have looked right everywhere. Two lanes shut by one agency are two closures.
        let facts = HazardStrip.RouteFacts(closures: [(source: "511 SF Bay", until: HazardStripTests.date(18)),
                                                      (source: "511 SF Bay", until: HazardStripTests.date(21))])
        #expect(HazardStrip.flags(for: facts)
                == [.closure(source: "511 SF Bay", until: HazardStripTests.date(18)),
                    .closure(source: "511 SF Bay", until: HazardStripTests.date(21))])
    }
}
