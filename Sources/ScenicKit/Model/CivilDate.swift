import Foundation

/// A calendar date with no time zone. Used where "the drive is on the 21st" matters and Foundation's
/// `Calendar`/`TimeZone` machinery would only add ways to be wrong on Linux.
public struct CivilDate: Hashable, Sendable, Codable {
    public let year: Int
    public let month: Int
    public let day: Int

    public init(year: Int, month: Int, day: Int) {
        self.year = year
        self.month = month
        self.day = day
    }

    /// Julian Day Number of this Gregorian date (proleptic), at 0h UTC. Fliegel & Van Flandern.
    public var julianDayAtMidnightUTC: Double {
        let a = (14 - month) / 12
        let y = year + 4800 - a
        let m = month + 12 * a - 3
        let jdn = day + (153 * m + 2) / 5 + 365 * y + y / 4 - y / 100 + y / 400 - 32045
        return Double(jdn) - 0.5
    }

    /// 0h UTC on this date as a `Date`.
    public var midnightUTC: Date {
        Date(timeIntervalSince1970: (julianDayAtMidnightUTC - 2_440_587.5) * 86_400)
    }

    /// Parses "YYYY-MM-DD". Anything else returns nil.
    public init?(iso: String) {
        let parts = iso.split(separator: "-")
        guard parts.count == 3, let y = Int(parts[0]), let m = Int(parts[1]), let d = Int(parts[2]),
              (1...12).contains(m), (1...31).contains(d) else { return nil }
        self.init(year: y, month: m, day: d)
    }
}
