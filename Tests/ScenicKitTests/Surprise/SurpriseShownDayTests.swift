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
}
