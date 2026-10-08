import Foundation

/// The day a Surprise place was shown, as the device's user store keeps it (T-0312 R2, R3): the civil date the card
/// used, as whole days since 1970-01-01 of that calendar date - no zone, no time of day.
public enum SurpriseShownDay {
    /// Whole days from 1970-01-01 to `date`, both read as calendar dates.
    public static func number(_ date: CivilDate) -> Int {
        0
    }

    /// The calendar date `number` days after 1970-01-01: the inverse of `number(_:)`.
    public static func date(_ number: Int) -> CivilDate {
        CivilDate(year: 1970, month: 1, day: 1)
    }

    /// The oldest day the pick still reads on `today` (R3): an entry this old blocks its place, one a day older does
    /// not, so the store keeps this day and prunes everything before it.
    public static func oldestKept(today: CivilDate) -> Int {
        0
    }
}
