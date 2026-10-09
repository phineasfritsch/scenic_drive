import Foundation

/// What /trip's 422 `nothing_pretty` carries (T-0335 R2, T-0337 R1): the request's own days and extra-time percent,
/// echoed by services/api/src/trip.ts when the trip the Worker would ship scores below RouteScore's 0.45.
///
/// Read fail-closed, as `NothingPrettyOffer` is: both keys present, each a JSON number that is finite, whole and
/// inside the Worker's whitelist (tripRequest.ts). Anything else is not an answer to a request this client made, and
/// TripReplyReader answers `unexpectedResponse` instead.
public struct TripNothingPretty: Equatable, Sendable, Decodable {
    /// tripRequest.ts MIN_TRIP_DAYS...MAX_TRIP_DAYS.
    public static let dayRange = 1...5
    /// tripRequest.ts 0...MAX_EXTRA_BUDGET_PCT.
    public static let percentRange = 0...40

    public let days: Int
    public let extraBudgetPercent: Int

    public init(days: Int, extraBudgetPercent: Int) {
        self.days = days
        self.extraBudgetPercent = extraBudgetPercent
    }

    enum CodingKeys: String, CodingKey {
        case days
        case extraBudgetPercent = "extra_budget_pct"
    }

    struct Refused: Error {}

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        let days = try container.decode(Double.self, forKey: .days)
        let percent = try container.decode(Double.self, forKey: .extraBudgetPercent)
        guard days.isFinite, days == days.rounded(),
              days >= Double(Self.dayRange.lowerBound), days <= Double(Self.dayRange.upperBound) else { throw Refused() }
        guard percent.isFinite, percent == percent.rounded(),
              percent >= Double(Self.percentRange.lowerBound), percent <= Double(Self.percentRange.upperBound) else {
            throw Refused()
        }
        self.init(days: Int(days), extraBudgetPercent: Int(percent))
    }
}
