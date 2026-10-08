import Foundation
import ScenicKit
import Testing

/// T-0312 R2/R3: the stored day is the card's civil date as whole days since 1970-01-01, and the store keeps
/// exactly the days the pick still reads.
@Suite("SurpriseShownDayTests") struct SurpriseShownDayTests {
    struct Known: Sendable, CustomTestStringConvertible {
        let date: CivilDate
        let number: Int
        var testDescription: String { "\(date.year)-\(date.month)-\(date.day)" }
    }

    /// Hand-counted: 2000-01-01 is 10957 (30 years, 7 leap days), 2026-01-01 is 20454 (+26 years, 7 leap days),
    /// and 2026-10-07 is 279 days later.
    static let known: [Known] = [
        Known(date: CivilDate(year: 1970, month: 1, day: 1), number: 0),
        Known(date: CivilDate(year: 1970, month: 1, day: 2), number: 1),
        Known(date: CivilDate(year: 1969, month: 12, day: 31), number: -1),
        Known(date: CivilDate(year: 1970, month: 3, day: 1), number: 59),
        Known(date: CivilDate(year: 2000, month: 1, day: 1), number: 10_957),
        Known(date: CivilDate(year: 2000, month: 2, day: 29), number: 11_016),
        Known(date: CivilDate(year: 2000, month: 3, day: 1), number: 11_017),
        Known(date: CivilDate(year: 2026, month: 1, day: 1), number: 20_454),
        Known(date: CivilDate(year: 2026, month: 10, day: 7), number: 20_733),
        Known(date: CivilDate(year: 2026, month: 12, day: 31), number: 20_818),
    ]

    @Test("A known calendar date is its hand-counted day number, and that number is the date", arguments: known)
    func knownDays(_ row: Known) {
        #expect(SurpriseShownDay.number(row.date) == row.number)
        #expect(SurpriseShownDay.date(row.number) == row.date)
    }

    @Test("The oldest kept day on 2026-10-07 is 89 days back: 2026-07-10")
    func oldestKeptValue() {
        let today = CivilDate(year: 2026, month: 10, day: 7)
        #expect(SurpriseShownDay.oldestKept(today: today) == 20_733 - 89)
        #expect(SurpriseShownDay.date(SurpriseShownDay.oldestKept(today: today)) == CivilDate(year: 2026, month: 7,
                                                                                                  day: 10))
    }

    static func daysIn(_ year: Int, _ month: Int) -> Int {
        let leap = year % 4 == 0 && (year % 100 != 0 || year % 400 == 0)
        return [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]
    }

    @Test("Every day from 1600 to 2400 is a valid calendar date that numbers back to itself")
    func sweep() {
        let first = SurpriseShownDay.number(CivilDate(year: 1600, month: 1, day: 1))
        let last = SurpriseShownDay.number(CivilDate(year: 2400, month: 12, day: 31))
        var offenders: [String] = []
        for n in first...last {
            let d = SurpriseShownDay.date(n)
            let valid = (1...12).contains(d.month) && (1...Self.daysIn(d.year, d.month)).contains(d.day)
            if !valid || SurpriseShownDay.number(d) != n, offenders.count < 3 {
                offenders.append("\(n) -> \(d.year)-\(d.month)-\(d.day)")
            }
        }
        let span: Int = 801 * 365 + 195 - 1
        #expect(last - first == span, "801 years of days, 195 of them leap years")
        #expect(offenders == [])
    }

    @Test("The pick blocks a place shown on the oldest kept day and not one shown the day before")
    func retentionIsThePicksWindow() {
        let today = CivilDate(year: 2026, month: 10, day: 7)
        let a = SurpriseShownFixture.a
        let oldest = SurpriseShownDay.oldestKept(today: today)
        func pick(shownOn day: Int?) -> String? {
            let shown = day.map { [SurpriseShownFixture.shown(a, SurpriseShownDay.date($0))] } ?? []
            return Surprise.pick(candidates: [a], reach: SurpriseReach(budgetMinutes: 120, roundTripMinutes: [a.id: 60]),
                                 history: SurpriseHistory(shown: shown),
                                 context: SurpriseContext(userId: "u", date: today, departureMinute: 600,
                                                          utcOffsetMinutes: -420, redFlag: false),
                                 seed: 0)?.candidateId
        }
        #expect(pick(shownOn: nil) == a.id, "control: never shown, the place is picked")
        #expect(pick(shownOn: oldest) == nil, "shown on the oldest kept day: still blocked")
        #expect(pick(shownOn: oldest - 1) == a.id, "shown the day before: free again, so the store may prune it")
    }
}
