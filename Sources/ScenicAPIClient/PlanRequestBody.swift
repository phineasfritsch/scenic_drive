import Foundation
import ScenicKit

/// The POST /plan body T-0248 R1 ruled, built only from values that pass the device-side whitelist (T-0251 R3).
///
/// ONE coordinate - `origin` - and a destination that is the corpus `place_id` integer, so no parameter exists
/// through which a second coordinate could ride. The origin must already be at 2 decimal places; this type
/// refuses rather than rounds, so a caller that forgot to round is told instead of being made to look compliant.
struct PlanRequestBody: Encodable {
    /// T-0248's MAX_BUDGET_MINUTES: the Worker refuses more, so the device does too.
    static let maxBudgetMinutes = 180

    let origin: Coordinate
    let place: Int64
    let budgetMinutes: Int
    let departsAt: Date?

    private init(origin: Coordinate, place: Int64, budgetMinutes: Int, departsAt: Date?) {
        self.origin = origin
        self.place = place
        self.budgetMinutes = budgetMinutes
        self.departsAt = departsAt
    }

    /// The body, or why it may not be sent. Range first (a NaN or an infinity fails `contains`), then decimals.
    static func validated(origin: Coordinate, place: Int64, budgetMinutes: Int,
                          departsAt: Date?) -> Result<PlanRequestBody, PlanRefusal> {
        guard (-90.0...90.0).contains(origin.latitude), (-180.0...180.0).contains(origin.longitude) else {
            return .failure(.originOutOfRange)
        }
        guard atTwoDecimals(origin.latitude), atTwoDecimals(origin.longitude) else {
            return .failure(.originMoreThanTwoDecimals)
        }
        guard (0...maxBudgetMinutes).contains(budgetMinutes) else { return .failure(.budgetOutOfRange) }
        return .success(PlanRequestBody(origin: origin, place: place, budgetMinutes: budgetMinutes,
                                        departsAt: departsAt))
    }

    /// The double nearest some k/100 - the Swift twin of planRequest.ts's `Number(v.toFixed(2)) === v`.
    static func atTwoDecimals(_ value: Double) -> Bool {
        (value * 100).rounded() / 100 == value
    }

    /// `2026-10-05T16:30:00Z`: UTC, whole seconds - the spelling planRequest.ts's INSTANT grammar accepts.
    static func instant(_ date: Date) -> String {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime]
        formatter.timeZone = TimeZone(identifier: "UTC")
        return formatter.string(from: date)
    }

    enum CodingKeys: String, CodingKey {
        case origin, destination, lat, lon, place
        case budgetMinutes = "budget_minutes"
        case departsAt = "departs_at"
    }

    func encode(to encoder: Encoder) throws {
        var top = encoder.container(keyedBy: CodingKeys.self)
        var from = top.nestedContainer(keyedBy: CodingKeys.self, forKey: .origin)
        try from.encode(origin.latitude, forKey: .lat)
        try from.encode(origin.longitude, forKey: .lon)
        var to = top.nestedContainer(keyedBy: CodingKeys.self, forKey: .destination)
        try to.encode(String(place), forKey: .place)
        try top.encode(budgetMinutes, forKey: .budgetMinutes)
        if let departsAt {
            try top.encode(Self.instant(departsAt), forKey: .departsAt)
        }
    }
}
