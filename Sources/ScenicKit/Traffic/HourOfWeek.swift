import Foundation

/// One hour of the week, Monday 00:00 = 0 through Sunday 23:00 = 167, in local time (T-0320 R5): rush hour is a
/// local fact, so the learner reads the hour in its own TimeZone and Sunday 23:xx wraps to Monday 00:xx = 0.
public struct HourOfWeek: Hashable, Sendable {
    /// Hours in a week; a value is in 0..<count.
    public static let count = 168

    public let value: Int

    /// nil outside 0...167 - an hour that is not one of the week's cannot be built (R4).
    public init?(_ value: Int) {
        guard value >= 0, value < Self.count else { return nil }
        self.value = value
    }

    /// The hour of the week `date` falls in, read on the gregorian calendar in `timeZone`.
    public static func of(_ date: Date, in timeZone: TimeZone) -> HourOfWeek {
        var calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = timeZone
        let parts = calendar.dateComponents([.weekday, .hour], from: date)
        // Calendar's weekday is 1 = Sunday ... 7 = Saturday; Monday-based is 0 = Monday ... 6 = Sunday.
        let day = ((parts.weekday ?? 2) + 5) % 7
        return HourOfWeek(day * 24 + (parts.hour ?? 0)) ?? HourOfWeek(0)!
    }
}
