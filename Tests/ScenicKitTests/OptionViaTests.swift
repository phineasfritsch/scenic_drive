import ScenicKit
import Testing

/// T-0408 R4: the home sheet's option rows and meta line say "via" the roads an option ADDS over the fastest one,
/// first two, then "+N more". Every case compares the whole string, so a changed separator, count or order fails.
@Suite("OptionViaTests") struct OptionViaTests {
    @Test("an option names the roads the fastest option does not drive, in order, then the count left")
    func namesTheAddedRoads() {
        let line = OptionVia.line(roads: ["Topanga", "Fernwood", "Tuna Canyon", "Saddle Peak", "PCH"],
                                  fastest: ["Topanga", "PCH"])
        #expect(line == "via Fernwood · Tuna Canyon · +1 more")
    }

    @Test("the fastest option, which adds nothing, names its own first roads")
    func fastestNamesItsOwnRoads() {
        let roads = ["Topanga", "PCH", "Malibu Canyon"]
        #expect(OptionVia.line(roads: roads, fastest: roads) == "via Topanga · PCH · +1 more")
    }

    @Test("exactly two added roads carry no count; one added road stands alone")
    func noCountWhenNothingIsLeft() {
        #expect(OptionVia.line(roads: ["A", "B", "C"], fastest: ["A"]) == "via B · C")
        #expect(OptionVia.line(roads: ["A", "B"], fastest: ["A"]) == "via B")
    }

    @Test("a road listed twice is named once and counted once")
    func repeatsCollapse() {
        #expect(OptionVia.line(roads: ["A", "B", "B", "C", "D", "C"], fastest: ["A"]) == "via B · C · +1 more")
    }

    @Test("no roads at all is an empty line, never a bare 'via'")
    func noRoadsNoLine() {
        #expect(OptionVia.line(roads: [], fastest: ["A"]) == "")
        #expect(OptionVia.line(roads: [], fastest: []) == "")
    }
}
