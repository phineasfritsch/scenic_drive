import Foundation

/// One stretch of the planned line between pins, as NavAdapter hands it to Ferrostar as a step (T-0321 R4).
///
/// /plan returns no GraphHopper instructions today, so the steps are the legs: each ends at a pin
/// (GuidanceMapping's `.reachedVia`) and the last at the destination (`.finish`).
public struct DriveLeg: Sendable, Equatable {
    public let coordinates: [Coordinate]
    public let maneuver: GuidanceManeuver

    public init(coordinates: [Coordinate], maneuver: GuidanceManeuver) {
        self.coordinates = coordinates
        self.maneuver = maneuver
    }

    /// The leg's length along its vertices, in metres (Geo's haversine, summed).
    public var lengthMeters: Double {
        zip(coordinates, coordinates.dropFirst()).reduce(0) { $0 + Geo.distanceMeters($1.0, $1.1) }
    }

    /// The line cut at each pin vertex strictly inside it. A pin on the first or last vertex cuts nothing, so no
    /// leg is a single point; consecutive legs share their boundary vertex.
    public static func split(_ line: DriveLine, at vertices: [Int]) -> [DriveLeg] {
        let last = line.coordinates.count - 1
        var legs: [DriveLeg] = []
        var start = 0
        for cut in vertices where cut > 0 && cut < last {
            legs.append(DriveLeg(coordinates: Array(line.coordinates[start...cut]),
                                 maneuver: GuidanceMapping.maneuver(for: .reachedVia)))
            start = cut
        }
        legs.append(DriveLeg(coordinates: Array(line.coordinates[start...last]),
                             maneuver: GuidanceMapping.maneuver(for: .finish)))
        return legs
    }
}
