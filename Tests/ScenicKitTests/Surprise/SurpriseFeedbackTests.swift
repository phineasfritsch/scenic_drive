import Foundation
import Testing
@testable import ScenicKit

/// T-0253 R6: each "not this" reason changes the next pick deterministically. P0 is scenario A's seed-0 pick,
/// lbc-02 (a beach, 170 min round trip); each test answers it and asks `Surprise.pick` again at seed 0. The
/// seed-0 literals are the Python oracle's (R8).
@Suite("surprise not-this feedback")
struct SurpriseFeedbackTests {
    static func answered(_ reason: SurpriseFeedback.Reason, on date: CivilDate = SurpriseFixture.june20)
        -> SurpriseHistory {
        SurpriseHistory(feedback: [SurpriseFeedback(candidateId: "lbc-02", category: .beach, roundTripMinutes: 170,
                                                    date: date, reason: reason)])
    }

    @Test("not this - too far: the next pick is ojai-02 and no pick that day is 170 min or longer")
    func tooFar() throws {
        #expect(try SurpriseFixture.pick(seed: 0)?.candidateId == "lbc-02")
        let history = Self.answered(.tooFar)
        #expect(try SurpriseFixture.pick(seed: 0, history: history)?.candidateId == "ojai-02")
        let trips = try SurpriseFixture.roundTrips()
        #expect(try SurpriseFixture.ids(history: history).allSatisfy { (trips[$0] ?? 999) < 170 })
        let tomorrow = SurpriseFixture.context(date: SurpriseFixture.june21)
        #expect(Set(try SurpriseFixture.ids(history: history, context: tomorrow)).contains("lbc-02"))
    }

    @Test("not this - not my thing: the next pick is ojai-02 and no beach for 30 days")
    func notMyThing() throws {
        let history = Self.answered(.notMyThing)
        #expect(try SurpriseFixture.pick(seed: 0, history: history)?.candidateId == "ojai-02")
        #expect(try SurpriseFixture.ids(history: history).allSatisfy { try SurpriseFixture.category($0) != .beach })
        let day29 = SurpriseFixture.context(date: CivilDate(year: 2026, month: 7, day: 19))
        #expect(try SurpriseFixture.ids(history: history, context: day29)
            .allSatisfy { try SurpriseFixture.category($0) != .beach })
        let monthLater = SurpriseFixture.context(date: CivilDate(year: 2026, month: 7, day: 20))
        #expect(try SurpriseFixture.ids(history: history, context: monthLater)
            .contains { try SurpriseFixture.category($0) == .beach })
    }

    @Test("not this - been there: the next pick is mulholland-09 and lbc-02 never returns, even a year on")
    func beenThere() throws {
        let history = Self.answered(.beenThere, on: CivilDate(year: 2025, month: 5, day: 16))
        #expect(try SurpriseFixture.pick(seed: 0, history: history)?.candidateId == "mulholland-09")
        #expect(!Set(try SurpriseFixture.ids(history: history)).contains("lbc-02"))
    }

    @Test("not this - wrong time: the next pick is mulholland-09 today, and lbc-02 is back tomorrow")
    func wrongTime() throws {
        let history = Self.answered(.wrongTime)
        #expect(try SurpriseFixture.pick(seed: 0, history: history)?.candidateId == "mulholland-09")
        #expect(!Set(try SurpriseFixture.ids(history: history)).contains("lbc-02"))
        let tomorrow = SurpriseFixture.context(date: SurpriseFixture.june21)
        #expect(try SurpriseFixture.pick(seed: 0, history: history, context: tomorrow)?.candidateId == "lbc-02")
    }
}
