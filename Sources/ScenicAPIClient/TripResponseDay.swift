import Foundation
import ScenicKit

/// One day of a /trip answer (services/api/src/tripPlanner.ts TripDayResult): its two ends, the split's drive time,
/// distance and ceiling, its stops, whether an overnight stop closes it, and its leg's path - null in a preview.
public struct TripResponseDay: Equatable, Sendable {
    public let day: Int
    public let start: Coordinate
    public let end: Coordinate
    public let driveSeconds: Double
    public let distanceMeters: Double
    public let ceilingSeconds: Double
    public let stops: [String]
    public let overnight: Bool
    public let leg: [Coordinate]?

    public init(day: Int, start: Coordinate, end: Coordinate, driveSeconds: Double, distanceMeters: Double,
                ceilingSeconds: Double, stops: [String], overnight: Bool, leg: [Coordinate]?) {
        self.day = day
        self.start = start
        self.end = end
        self.driveSeconds = driveSeconds
        self.distanceMeters = distanceMeters
        self.ceilingSeconds = ceilingSeconds
        self.stops = stops
        self.overnight = overnight
        self.leg = leg
    }
}

extension TripResponseDay: Decodable {
    enum CodingKeys: String, CodingKey {
        case day, start, end, lat, lon, stops, overnight, leg, coordinates, kind
        case driveSeconds = "drive_s"
        case distanceMeters = "distance_m"
        case ceilingSeconds = "ceiling_s"
    }

    public init(from decoder: Decoder) throws {
        let top = try decoder.container(keyedBy: CodingKeys.self)
        func point(_ key: CodingKeys) throws -> Coordinate {
            let at = try top.nestedContainer(keyedBy: CodingKeys.self, forKey: key)
            return Coordinate(latitude: try at.decode(Double.self, forKey: .lat),
                              longitude: try at.decode(Double.self, forKey: .lon))
        }
        var overnight = false
        if try !top.decodeNil(forKey: .overnight) {
            let night = try top.nestedContainer(keyedBy: CodingKeys.self, forKey: .overnight)
            _ = try night.decode(String.self, forKey: .kind)
            overnight = true
        }
        var leg: [Coordinate]?
        if try !top.decodeNil(forKey: .leg) {
            let path = try top.nestedContainer(keyedBy: CodingKeys.self, forKey: .leg)
            var pairs = try path.nestedUnkeyedContainer(forKey: .coordinates)
            leg = try TripResponse.coordinates(&pairs)
        }
        self.init(day: try top.decode(Int.self, forKey: .day), start: try point(.start), end: try point(.end),
                  driveSeconds: try top.decode(Double.self, forKey: .driveSeconds),
                  distanceMeters: try top.decode(Double.self, forKey: .distanceMeters),
                  ceilingSeconds: try top.decode(Double.self, forKey: .ceilingSeconds),
                  stops: try top.decode([String].self, forKey: .stops), overnight: overnight, leg: leg)
    }
}
