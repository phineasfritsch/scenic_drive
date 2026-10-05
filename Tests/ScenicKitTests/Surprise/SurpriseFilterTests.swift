import Foundation
import Testing
@testable import ScenicKit

/// T-0253 R3: each hard filter, over every seed's pick from `Surprise.pick`. The picks over 300 consecutive
/// seeds are the whole eligible list (R5), so a witness that one filter alone excludes appears the moment that
/// filter is gone.
@Suite("surprise hard filters")
struct SurpriseFilterTests {
    @Test("filter 1: a place whose round trip exceeds the budget, or lies outside the reach, is never picked")
    func reach() throws {
        let picked = Set(try SurpriseFixture.ids())
        let trips = try SurpriseFixture.roundTrips()
        #expect(!picked.contains("w-reach-over"))
        #expect(!picked.contains("w-reach-none"))
        #expect(picked.contains("w-reach-edge"))
        #expect(picked.allSatisfy { (trips[$0] ?? 999) <= 180 })
    }

    @Test("filter 2: a place shown within 90 days is never picked; 90 days ago it may return")
    func shown90() throws {
        let picked = Set(try SurpriseFixture.ids(budget: 150, history: SurpriseFixture.historyB,
                                                 context: SurpriseFixture.contextB))
        #expect(!picked.contains("topanga-03"))
        #expect(picked.contains("malibu-02"))
        #expect(Set(try SurpriseFixture.ids(budget: 150, context: SurpriseFixture.contextB)).contains("topanga-03"))
    }

    @Test("filter 3: the same category on the same corridor within 30 days is never picked")
    func categoryCorridor30() throws {
        let picked = Set(try SurpriseFixture.ids(budget: 150, history: SurpriseFixture.historyB,
                                                 context: SurpriseFixture.contextB))
        #expect(!picked.contains("griffith-02"))
        #expect(picked.contains("arroyo-06"))
        #expect(Set(try SurpriseFixture.ids(budget: 150, context: SurpriseFixture.contextB)).contains("griffith-02"))
    }

    @Test("filter 4: a blocklisted brand or chain is never picked; an unlisted local brand is")
    func brands() throws {
        let picked = Set(try SurpriseFixture.ids())
        #expect(!picked.contains("w-brand-sbux"))
        #expect(!picked.contains("w-brand-innout"))
        let local = try SurpriseFixture.candidates().filter { $0.brand == "Canyon Coffee Co." }.map(\.id)
        #expect(local.count >= 5)
        #expect(local.allSatisfy { picked.contains($0) })
    }

    @Test("filter 5: a place not open from arrival to arrival + dwell + 45 min is never picked unless exempt")
    func openAtArrival() throws {
        let picked = Set(try SurpriseFixture.ids())
        #expect(!picked.contains("w-hours-late"))
        #expect(!picked.contains("w-hours-opens"))
        #expect(!picked.contains("w-hours-none"))
        #expect(picked.contains("w-hours-edge"))
        #expect(picked.contains("w-hours-open-edge"))
    }

    @Test("filter 6: an unlit unpaved viewpoint arriving after civil twilight is never picked")
    func darkViewpoint() throws {
        let picked = Set(try SurpriseFixture.ids(context: SurpriseFixture.context(depart: 1170)))
        #expect(!picked.contains("w-dark-late"))
        #expect(picked.contains("w-dark-lit"))
        #expect(picked.contains("w-dark-paved"))
        #expect(picked.contains("w-dark-early"))
        #expect(picked.contains("malibu-02"))
        #expect(Set(try SurpriseFixture.ids()).contains("w-dark-late"))
    }

    /// Two full equalities, not properties: the whole red-flag permutation equals the Python oracle's scenario R
    /// (its own fire table), and the red-flag set equals the calm set minus EXACTLY the three fire categories -
    /// so a red flag that also closes a beach, garden, cafe, museum or town is red here.
    @Test("filter 7: a red-flag day drops exactly park, trailhead and viewpoint - the oracle's red-flag permutation")
    func redFlag() throws {
        let fire: Set<SurpriseCategory> = [.park, .trailhead, .viewpoint]
        let red = SurpriseFixture.context(redFlag: true)
        let oracle = try SurpriseFixture.sequence("R")
        #expect(oracle.count == 75)
        #expect(try SurpriseFixture.ids(count: 75, context: red) == oracle)
        let calm = try SurpriseFixture.ids()
        let spared = Set(try calm.filter { !fire.contains(try SurpriseFixture.category($0) ?? .town) })
        #expect(Set(try SurpriseFixture.ids(context: red)) == spared)
        #expect(spared.count == 75 && Set(calm).count == 127)
    }

    @Test("filter 8: an approach crossing private access is never picked")
    func privateApproach() throws {
        let picked = Set(try SurpriseFixture.ids())
        #expect(!picked.contains("w-private-1"))
        #expect(!picked.contains("w-private-2"))
        #expect(picked.count == 127)
    }
}
