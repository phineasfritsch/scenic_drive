import Foundation
import ScenicKit

/// A 200 from /loop (services/api/src/loopPlanner.ts LoopResult), decoded strictly (T-0314 R2): route points arrive
/// as [lon, lat] pairs of exactly two numbers, waypoints as {lat, lon} and at most PlanWaypoints.maximum (the
/// Worker's MAX_WAYPOINTS) - more is not a loop, never truncated. The Worker's apple_maps_url is not read (R8).
public struct LoopResponse: Equatable, Sendable {
    public let route: [Coordinate]
    public let distanceMeters: Double
    public let durationSeconds: Double
    public let retraceFraction: Double
    public let minutes: Double
    public let etaIsEstimate: Bool
    public let waypoints: [Coordinate]

    public init(route: [Coordinate], distanceMeters: Double, durationSeconds: Double, retraceFraction: Double,
                minutes: Double, etaIsEstimate: Bool, waypoints: [Coordinate]) {
        self.route = route
        self.distanceMeters = distanceMeters
        self.durationSeconds = durationSeconds
        self.retraceFraction = retraceFraction
        self.minutes = minutes
        self.etaIsEstimate = etaIsEstimate
        self.waypoints = waypoints
    }
}

extension LoopResponse: Decodable {
    enum CodingKeys: String, CodingKey {
        case route, coordinates, minutes, waypoints, lat, lon
        case distanceMeters = "distance_m"
        case durationSeconds = "duration_s"
        case retraceFraction = "retrace_fraction"
        case etaIsEstimate = "eta_is_estimate"
    }

    public init(from decoder: Decoder) throws {
        let top = try decoder.container(keyedBy: CodingKeys.self)
        let route = try top.nestedContainer(keyedBy: CodingKeys.self, forKey: .route)
        var pairs = try route.nestedUnkeyedContainer(forKey: .coordinates)
        var points: [Coordinate] = []
        while !pairs.isAtEnd {
            let pair = try pairs.decode([Double].self)
            guard pair.count == 2 else {
                throw DecodingError.dataCorruptedError(in: pairs, debugDescription: "a route point is [lon, lat]")
            }
            points.append(Coordinate(latitude: pair[1], longitude: pair[0]))
        }
        var pins = try top.nestedUnkeyedContainer(forKey: .waypoints)
        var waypoints: [Coordinate] = []
        while !pins.isAtEnd {
            let pin = try pins.nestedContainer(keyedBy: CodingKeys.self)
            waypoints.append(Coordinate(latitude: try pin.decode(Double.self, forKey: .lat),
                                        longitude: try pin.decode(Double.self, forKey: .lon)))
        }
        guard waypoints.count <= PlanWaypoints.maximum else {
            throw DecodingError.dataCorruptedError(forKey: .waypoints, in: top, debugDescription: "more than nine")
        }
        self.init(route: points, distanceMeters: try route.decode(Double.self, forKey: .distanceMeters),
                  durationSeconds: try top.decode(Double.self, forKey: .durationSeconds),
                  retraceFraction: try top.decode(Double.self, forKey: .retraceFraction),
                  minutes: try top.decode(Double.self, forKey: .minutes),
                  etaIsEstimate: try top.decode(Bool.self, forKey: .etaIsEstimate),
                  waypoints: waypoints)
    }
}
