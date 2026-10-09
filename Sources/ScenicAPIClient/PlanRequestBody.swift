import Foundation
import ScenicKit

/// The POST /plan body T-0248 R1 ruled, built only from values that pass the device-side whitelist (T-0251 R3).
///
/// ONE coordinate - `origin` - and a destination that is the corpus `place_id` integer, so no parameter exists
/// through which a second coordinate could ride. The origin must already be at 2 decimal places; this type
/// refuses rather than rounds, so a caller that forgot to round is told instead of being made to look compliant.
/// `vehicle` is the profile's raw value, always sent; a profile that is not enabled is refused here (T-0311 R6).
struct PlanRequestBody: Encodable {
    /// T-0248's MAX_BUDGET_MINUTES: the Worker refuses more, so the device does too.
    static let maxBudgetMinutes = 180
    /// T-0319 R2: the Worker's MAX_WAYPOINTS, the largest reroute.first_pin it accepts.
    static let maxFirstPin = 9

    let origin: Coordinate
    let place: Int64
    let budgetMinutes: Int
    let departsAt: Date?
    let vehicle: VehicleProfile
    /// T-0319 R2: the plan this request continues and its first pin not yet passed; both nil on a fresh plan.
    let rerouteToken: String?
    let firstPin: Int?
    /// T-0334 R2: `back_roads: true` - plan the MAX_LAMBDA route alone; sent only when true, never with a reroute.
    let backRoads: Bool

    private init(origin: Coordinate, place: Int64, budgetMinutes: Int, departsAt: Date?, vehicle: VehicleProfile,
                 rerouteToken: String? = nil, firstPin: Int? = nil, backRoads: Bool = false) {
        self.origin = origin
        self.place = place
        self.budgetMinutes = budgetMinutes
        self.departsAt = departsAt
        self.vehicle = vehicle
        self.rerouteToken = rerouteToken
        self.firstPin = firstPin
        self.backRoads = backRoads
    }

    /// The body, or why it may not be sent. Range first (a NaN or an infinity fails `contains`), then decimals.
    static func validated(origin: Coordinate, place: Int64, budgetMinutes: Int,
                          departsAt: Date?, vehicle: VehicleProfile,
                          backRoads: Bool = false) -> Result<PlanRequestBody, PlanRefusal> {
        guard (-90.0...90.0).contains(origin.latitude), (-180.0...180.0).contains(origin.longitude) else {
            return .failure(.originOutOfRange)
        }
        guard atTwoDecimals(origin.latitude), atTwoDecimals(origin.longitude) else {
            return .failure(.originMoreThanTwoDecimals)
        }
        guard (0...maxBudgetMinutes).contains(budgetMinutes) else { return .failure(.budgetOutOfRange) }
        guard vehicle.isEnabled else { return .failure(.vehicleNotEnabled) }
        return .success(PlanRequestBody(origin: origin, place: place, budgetMinutes: budgetMinutes,
                                        departsAt: departsAt, vehicle: vehicle, backRoads: backRoads))
    }

    /// A reroute body (T-0319 R9): the token in the Worker's PLAN_TOKEN spelling, the first pin in 0...maxFirstPin,
    /// then every check a fresh plan makes. No departs_at: a reroute leaves now.
    static func validatedReroute(origin: Coordinate, place: Int64, budgetMinutes: Int, vehicle: VehicleProfile,
                                 token: String, firstPin: Int) -> Result<PlanRequestBody, PlanRefusal> {
        guard isPlanToken(token) else { return .failure(.rerouteTokenMalformed) }
        guard (0...maxFirstPin).contains(firstPin) else { return .failure(.firstPinOutOfRange) }
        return validated(origin: origin, place: place, budgetMinutes: budgetMinutes, departsAt: nil, vehicle: vehicle)
            .map { PlanRequestBody(origin: $0.origin, place: $0.place, budgetMinutes: $0.budgetMinutes, departsAt: nil,
                                   vehicle: $0.vehicle, rerouteToken: token, firstPin: firstPin) }
    }

    /// planToken.ts's PLAN_TOKEN: 36 characters, hyphens at 8, 13, 18 and 23, lowercase hex everywhere else.
    static func isPlanToken(_ token: String) -> Bool {
        let scalars = Array(token.unicodeScalars)
        guard scalars.count == 36 else { return false }
        for (index, scalar) in scalars.enumerated() {
            let hyphen = index == 8 || index == 13 || index == 18 || index == 23
            let hex = ("0"..."9").contains(scalar) || ("a"..."f").contains(scalar)
            guard hyphen ? scalar == "-" : hex else { return false }
        }
        return true
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
        case origin, destination, lat, lon, place, vehicle
        case budgetMinutes = "budget_minutes"
        case departsAt = "departs_at"
        case reroute, token
        case firstPin = "first_pin"
        case backRoads = "back_roads"
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
        try top.encode(vehicle.rawValue, forKey: .vehicle)
        if backRoads {
            try top.encode(true, forKey: .backRoads)
        }
        if let rerouteToken, let firstPin {
            var reroute = top.nestedContainer(keyedBy: CodingKeys.self, forKey: .reroute)
            try reroute.encode(rerouteToken, forKey: .token)
            try reroute.encode(firstPin, forKey: .firstPin)
        }
    }
}
