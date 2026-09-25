import Foundation

/// Where and when a corridor speed was observed: a coarse cell, and an hour of the week.
///
/// Hour of the week rather than hour of the day, because the thing being learned is congestion and Tuesday
/// at 08:00 has nothing in common with Sunday at 08:00. 168 buckets per cell.
///
/// The cell id is supplied by the caller rather than computed here. The plan specifies H3 resolution 8
/// (~0.7 km edge), and an H3 implementation is a large, exacting piece of geometry that belongs in its own
/// task with the reference library as an oracle. Everything in this file is about the *learning*, which is
/// independent of how the cell was derived - so it takes the id as an opaque value and can be tested exactly.
public struct CorridorKey: Hashable, Sendable {
    /// An opaque coarse-cell identifier. H3-8 in production.
    public let cell: UInt64

    /// 0...167, Monday 00:00 = 0.
    public let hourOfWeek: Int

    public init?(cell: UInt64, hourOfWeek: Int) {
        guard (0..<168).contains(hourOfWeek) else { return nil }
        self.cell = cell
        self.hourOfWeek = hourOfWeek
    }

    /// The bucket a date falls in, in the given calendar.
    ///
    /// The calendar is a parameter because `Calendar.current` reads the device's locale, and the first
    /// weekday differs by region - Sunday in the US, Monday in most of Europe. Learning would bucket the
    /// same drive differently for two users, and a user who travelled would silently re-bucket their own
    /// history. Monday is fixed as bucket 0 here regardless of what the calendar calls the first weekday.
    public init?(cell: UInt64, date: Date, calendar: Calendar) {
        let c = calendar.dateComponents([.weekday, .hour], from: date)
        guard let weekday = c.weekday, let hour = c.hour else { return nil }
        // Calendar.weekday is 1 = Sunday ... 7 = Saturday, always, independent of `firstWeekday`.
        let mondayBased = (weekday + 5) % 7          // Monday -> 0, Sunday -> 6
        self.init(cell: cell, hourOfWeek: mondayBased * 24 + hour)
    }
}
