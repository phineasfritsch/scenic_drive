import Foundation
import ScenicKit

/// The /loop body (T-0314 R1), built only through `validated`: exactly services/api/src/loopRequest.ts's BODY_KEYS -
/// `{start: {lat, lon}, minutes, vehicle}`. The start is the ONE coordinate (P-PRIV-05) and must already be at 2 dp;
/// minutes are whole and inside [MIN_LOOP_MINUTES, MAX_LOOP_MINUTES].
struct LoopRequestBody: Encodable {
    static let minuteRange = 10...180

    let start: Coordinate
    let minutes: Int
    let vehicle: VehicleProfile

    private init(start: Coordinate, minutes: Int, vehicle: VehicleProfile) {
        self.start = start
        self.minutes = minutes
        self.vehicle = vehicle
    }

    static func validated(start: Coordinate, minutes: Int, vehicle: VehicleProfile) -> Result<LoopRequestBody, LoopRefusal> {
        guard (-90.0...90.0).contains(start.latitude), (-180.0...180.0).contains(start.longitude) else {
            return .failure(.startOutOfRange)
        }
        guard atTwoDecimals(start.latitude), atTwoDecimals(start.longitude) else {
            return .failure(.startMoreThanTwoDecimals)
        }
        guard minuteRange.contains(minutes) else { return .failure(.minutesOutOfRange) }
        guard vehicle.isEnabled else { return .failure(.vehicleNotEnabled) }
        return .success(LoopRequestBody(start: start, minutes: minutes, vehicle: vehicle))
    }

    static func atTwoDecimals(_ value: Double) -> Bool {
        (value * 100).rounded() / 100 == value
    }

    enum CodingKeys: String, CodingKey {
        case start, lat, lon, minutes, vehicle
    }

    func encode(to encoder: Encoder) throws {
        var top = encoder.container(keyedBy: CodingKeys.self)
        var from = top.nestedContainer(keyedBy: CodingKeys.self, forKey: .start)
        try from.encode(start.latitude, forKey: .lat)
        try from.encode(start.longitude, forKey: .lon)
        try top.encode(minutes, forKey: .minutes)
        try top.encode(vehicle.rawValue, forKey: .vehicle)
    }
}
