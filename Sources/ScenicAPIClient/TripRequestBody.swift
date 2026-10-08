import Foundation
import ScenicKit

/// The /trip body (T-0313 R1), built only through `validated`: exactly services/api/src/tripRequest.ts's BODY_KEYS -
/// `{origin: {lat, lon}, destination: {place}, days, extra_budget_pct, vehicle}`. The origin is the ONE coordinate
/// (P-PRIV-05) and must already be at 2 dp; the place id travels as the string the Worker's PLACE_ID accepts.
struct TripRequestBody: Encodable {
    static let dayRange = 1...5
    static let extraPercentRange = 0...40

    let origin: Coordinate
    let place: Int64
    let days: Int
    let extraBudgetPercent: Int
    let vehicle: VehicleProfile

    private init(origin: Coordinate, place: Int64, days: Int, extraBudgetPercent: Int, vehicle: VehicleProfile) {
        self.origin = origin
        self.place = place
        self.days = days
        self.extraBudgetPercent = extraBudgetPercent
        self.vehicle = vehicle
    }

    static func validated(origin: Coordinate, place: Int64, days: Int, extraBudgetPercent: Int,
                          vehicle: VehicleProfile) -> Result<TripRequestBody, TripRefusal> {
        guard (-90.0...90.0).contains(origin.latitude), (-180.0...180.0).contains(origin.longitude) else {
            return .failure(.originOutOfRange)
        }
        guard atTwoDecimals(origin.latitude), atTwoDecimals(origin.longitude) else {
            return .failure(.originMoreThanTwoDecimals)
        }
        guard dayRange.contains(days) else { return .failure(.daysOutOfRange) }
        guard extraPercentRange.contains(extraBudgetPercent) else { return .failure(.extraPercentOutOfRange) }
        guard vehicle.isEnabled else { return .failure(.vehicleNotEnabled) }
        return .success(TripRequestBody(origin: origin, place: place, days: days,
                                        extraBudgetPercent: extraBudgetPercent, vehicle: vehicle))
    }

    static func atTwoDecimals(_ value: Double) -> Bool {
        (value * 100).rounded() / 100 == value
    }

    enum CodingKeys: String, CodingKey {
        case origin, destination, lat, lon, place, days, vehicle
        case extraBudgetPercent = "extra_budget_pct"
    }

    func encode(to encoder: Encoder) throws {
        var top = encoder.container(keyedBy: CodingKeys.self)
        var from = top.nestedContainer(keyedBy: CodingKeys.self, forKey: .origin)
        try from.encode(origin.latitude, forKey: .lat)
        try from.encode(origin.longitude, forKey: .lon)
        var to = top.nestedContainer(keyedBy: CodingKeys.self, forKey: .destination)
        try to.encode(String(place), forKey: .place)
        try top.encode(days, forKey: .days)
        try top.encode(extraBudgetPercent, forKey: .extraBudgetPercent)
        try top.encode(vehicle.rawValue, forKey: .vehicle)
    }
}
