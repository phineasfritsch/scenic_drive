import Foundation

/// Who is asking, on which local day, leaving when, and whether today is a red-flag day (T-0253 R1, R2).
public struct SurpriseContext: Sendable, Equatable {
    public let userId: String
    public let date: CivilDate
    /// Local minutes after midnight.
    public let departureMinute: Int
    /// Local clock minus UTC, in minutes (-420 for Los Angeles in summer).
    public let utcOffsetMinutes: Int
    public let redFlag: Bool

    public init(userId: String, date: CivilDate, departureMinute: Int, utcOffsetMinutes: Int, redFlag: Bool) {
        self.userId = userId
        self.date = date
        self.departureMinute = departureMinute
        self.utcOffsetMinutes = utcOffsetMinutes
        self.redFlag = redFlag
    }
}
