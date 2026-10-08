import Foundation

/// The day a Surprise place was shown, as the device's user store keeps it (T-0312 R2, R3): the civil date the card
/// used, as whole days since 1970-01-01 of that calendar date - no zone, no time of day.
public enum SurpriseShownDay {
    /// Julian Day Number of 1970-01-01.
    static let epochJulianDay = 2_440_588

    /// Whole days from 1970-01-01 to `date`, both read as calendar dates.
    public static func number(_ date: CivilDate) -> Int {
        Int((date.julianDayAtMidnightUTC + 0.5).rounded()) - epochJulianDay
    }

    /// The calendar date `number` days after 1970-01-01: the inverse of `number(_:)` (proleptic Gregorian, counted
    /// in 400-year eras from 0000-03-01 so the leap day is the last day of each counted year).
    public static func date(_ number: Int) -> CivilDate {
        let z = number + 719_468
        let era = (z >= 0 ? z : z - 146_096) / 146_097
        let dayOfEra = z - era * 146_097
        let yearOfEra = (dayOfEra - dayOfEra / 1460 + dayOfEra / 36_524 - dayOfEra / 146_096) / 365
        let dayOfYear = dayOfEra - (365 * yearOfEra + yearOfEra / 4 - yearOfEra / 100)
        let shiftedMonth = (5 * dayOfYear + 2) / 153
        let day = dayOfYear - (153 * shiftedMonth + 2) / 5 + 1
        let month = shiftedMonth < 10 ? shiftedMonth + 3 : shiftedMonth - 9
        let year = yearOfEra + era * 400
        return CivilDate(year: month <= 2 ? year + 1 : year, month: month, day: day)
    }

    /// The oldest day the pick still reads on `today` (R3): an entry this old blocks its place, one a day older does
    /// not, so the store keeps this day and prunes everything before it.
    public static func oldestKept(today: CivilDate) -> Int {
        number(today) - (Surprise.shownDays - 1)
    }
}
