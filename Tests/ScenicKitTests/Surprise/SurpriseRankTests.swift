import Foundation
import Testing
@testable import ScenicKit

/// T-0253 R4, R5, R7: the ranking, the seeded exploration and P-PROD-02 by exact equality to the independent
/// Python oracle (Tests/Fixtures/surprise/model.py), and the WHY pinned whole.
@Suite("surprise ranking and reproducibility")
struct SurpriseRankTests {
    @Test("P-PROD-02: the same user, local date and seed give the same pick, 100 runs")
    func reproducible() throws {
        for seed: UInt64 in [0, 7, 125, 9_999_999_999] {
            let first = SurpriseFixture.render(try SurpriseFixture.pick(seed: seed))
            #expect(first != "nil")
            for _ in 0..<100 {
                #expect(SurpriseFixture.render(try SurpriseFixture.pick(seed: seed)) == first)
            }
        }
    }

    @Test("P-PROD-02: >= 90 of 100 consecutive seeds give distinct picks over the 126 eligible")
    func distinct() throws {
        #expect(Set(try SurpriseFixture.ids()).count == 126)
        #expect(Set(try SurpriseFixture.ids(count: 100)).count >= 90)
        #expect(Set(try SurpriseFixture.ids(from: 5_000, count: 100)).count >= 90)
    }

    @Test("the whole pick permutation equals the oracle's: driver-a, driver-c and driver-b with history")
    func permutation() throws {
        let a = try SurpriseFixture.sequence("A")
        let c = try SurpriseFixture.sequence("C")
        let b = try SurpriseFixture.sequence("B")
        #expect(a.count == 126 && c.count == 126 && b.count == 96)
        #expect(try SurpriseFixture.ids(count: 126) == a)
        #expect(try SurpriseFixture.ids(count: 126, context: SurpriseFixture.context(user: "driver-c")) == c)
        #expect(try SurpriseFixture.ids(count: 96, budget: 150, history: SurpriseFixture.historyB,
                                        context: SurpriseFixture.contextB) == b)
        #expect(a != c)
    }

    @Test("the WHY: three picks pinned whole - hook, round trip and the golden-hour line from Solar")
    func reasons() throws {
        #expect(SurpriseFixture.render(try SurpriseFixture.pick(seed: 0))
            == "lbc-02 | Long Beach Cove 3 | Tide pools at the end of a quiet road - Long Beach | 170 min | "
            + "no golden hour")
        #expect(SurpriseFixture.render(try SurpriseFixture.pick(seed: 3))
            == "ojai-02 | Ojai Trailhead 3 | A short climb to a long view - Ojai | 154 min | no golden hour")
        let evening = SurpriseFixture.context(depart: 1170)
        let early = try SurpriseFixture.ids(context: evening).firstIndex(of: "w-dark-early")
        #expect(SurpriseFixture.render(try SurpriseFixture.pick(seed: UInt64(early ?? 0), context: evening))
            == "w-dark-early | Witness Early Dirt Overlook | Sunset from a dirt turnout | 30 min | "
            + "Sunset 20:08 - golden hour while you're there")
    }

    @Test("nothing reachable is nil: a 20 min budget, or no candidates; a 30 min budget reaches one")
    func nothing() throws {
        #expect(try SurpriseFixture.pick(seed: 0, budget: 20) == nil)
        #expect(try SurpriseFixture.ids(count: 3, budget: 30) == ["w-dark-early", "w-dark-early", "w-dark-early"])
        #expect(Surprise.pick(candidates: [], reach: SurpriseReach(budgetMinutes: 180, roundTripMinutes: [:]),
                              history: SurpriseHistory(), context: SurpriseFixture.context(), seed: 0) == nil)
    }
}
