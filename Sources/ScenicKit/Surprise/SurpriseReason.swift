import Foundation

/// The pick's WHY (T-0253 R7): the hook line, the round trip, and the golden-hour line when sunset falls inside
/// the visit.
public struct SurpriseReason: Sendable, Equatable {
    public let hook: String
    public let roundTripMinutes: Int
    public let goldenHourLine: String?

    public init(hook: String, roundTripMinutes: Int, goldenHourLine: String?) {
        self.hook = hook
        self.roundTripMinutes = roundTripMinutes
        self.goldenHourLine = goldenHourLine
    }
}
