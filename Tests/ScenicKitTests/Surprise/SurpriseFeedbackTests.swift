import Foundation
import Testing
@testable import ScenicKit

/// T-0253 R6: each "not this" reason changes the next pick deterministically. P0 is scenario A's seed-0 pick,
/// sgc-05 (a park, 132 min round trip, T-0283); each test answers it and asks `Surprise.pick` again at seed 0. The
/// seed-0 literals are the Python oracle's (R8).
@Suite("surprise not-this feedback")
struct SurpriseFeedbackTests {
    static func answered(_ reason: SurpriseFeedback.Reason, on date: CivilDate = SurpriseFixture.june20)
        -> SurpriseHistory {
        SurpriseHistory(feedback: [SurpriseFeedback(candidateId: "sgc-05", category: .park, roundTripMinutes: 132,
                                                    date: date, reason: reason)])
    }

    @Test("not this - too far: the next pick is griffith-02 and no pick that day is 132 min or longer")
    func tooFar() throws {
        #expect(try SurpriseFixture.pick(seed: 0)?.candidateId == "sgc-05")
        let history = Self.answered(.tooFar)
        #expect(try SurpriseFixture.pick(seed: 0, history: history)?.candidateId == "griffith-02")
        let trips = try SurpriseFixture.roundTrips()
        #expect(try SurpriseFixture.ids(history: history).allSatisfy { (trips[$0] ?? 999) < 132 })
        let tomorrow = SurpriseFixture.context(date: SurpriseFixture.june21)
        #expect(Set(try SurpriseFixture.ids(history: history, context: tomorrow)).contains("sgc-05"))
    }

    @Test("not this - not my thing: the next pick is griffith-02 and no park for 30 days")
    func notMyThing() throws {
        let history = Self.answered(.notMyThing)
        #expect(try SurpriseFixture.pick(seed: 0, history: history)?.candidateId == "griffith-02")
        #expect(try SurpriseFixture.ids(history: history).allSatisfy { try SurpriseFixture.category($0) != .park })
        let day29 = SurpriseFixture.context(date: CivilDate(year: 2026, month: 7, day: 19))
        #expect(try SurpriseFixture.ids(history: history, context: day29)
            .allSatisfy { try SurpriseFixture.category($0) != .park })
        let monthLater = SurpriseFixture.context(date: CivilDate(year: 2026, month: 7, day: 20))
        #expect(try SurpriseFixture.ids(history: history, context: monthLater)
            .contains { try SurpriseFixture.category($0) == .park })
    }

    @Test("not this - been there: the next pick is griffith-02 and sgc-05 never returns, even a year on")
    func beenThere() throws {
        let history = Self.answered(.beenThere, on: CivilDate(year: 2025, month: 5, day: 16))
        #expect(try SurpriseFixture.pick(seed: 0, history: history)?.candidateId == "griffith-02")
        #expect(!Set(try SurpriseFixture.ids(history: history)).contains("sgc-05"))
    }

    @Test("not this - wrong time: the next pick is griffith-02 today, and sgc-05 is back tomorrow")
    func wrongTime() throws {
        let history = Self.answered(.wrongTime)
        #expect(try SurpriseFixture.pick(seed: 0, history: history)?.candidateId == "griffith-02")
        #expect(!Set(try SurpriseFixture.ids(history: history)).contains("sgc-05"))
        let tomorrow = SurpriseFixture.context(date: SurpriseFixture.june21)
        #expect(try SurpriseFixture.pick(seed: 0, history: history, context: tomorrow)?.candidateId == "sgc-05")
    }
}
