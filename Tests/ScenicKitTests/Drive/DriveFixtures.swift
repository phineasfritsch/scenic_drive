@testable import ScenicKit
import Foundation

/// T-0317: the fixes and lines the drive-session suites feed DriveSession.
enum DriveFixtures {
    /// A straight line along `latitude`, a vertex every 0.01 degree of longitude from `firstLongitude` (~920 m in LA).
    static func line(latitude: Double, firstLongitude: Double, count: Int) -> [Coordinate] {
        (0..<count).map { Coordinate(latitude: latitude, longitude: firstLongitude + Double($0) * 0.01) }
    }

    /// The midpoint of segment `segment` of a line built by `line(...)`: on the line, distance 0.
    static func on(_ line: [Coordinate], segment: Int) -> Coordinate {
        let a = line[segment], b = line[segment + 1]
        return Coordinate(latitude: (a.latitude + b.latitude) / 2, longitude: (a.longitude + b.longitude) / 2)
    }

    /// 0.002 degree north of `point`: ~222 m, far beyond the 50 m threshold from every segment of a line(...).
    static func away(from point: Coordinate) -> Coordinate {
        Coordinate(latitude: point.latitude + 0.002, longitude: point.longitude)
    }

    static func fix(_ point: Coordinate, at timestamp: Double, speed: Double = 12) -> DriveFix {
        DriveFix(coordinate: point, speedMetersPerSecond: speed, timestamp: timestamp)
    }

    /// The probe line for the exact threshold: one segment east along the equator from (0, 0).
    static let probeStart = Coordinate(latitude: 0, longitude: 0)
    static let probeEnd = Coordinate(latitude: 0, longitude: 0.01)

    /// The distance DriveLine measures from (latitude, 0) to the probe line. At longitude 0 the fix projects onto
    /// the segment's start, so this is |latitude * metersPerDegree| rounded once - which some latitude makes exact.
    static func probeDistance(_ latitude: Double) -> Double {
        DriveLine([probeStart, probeEnd])!.distanceMeters(from: Coordinate(latitude: latitude, longitude: 0))
    }

    /// A latitude whose probe distance is EXACTLY `meters`, searched among the floats next to meters/k.
    static func latitude(measuring meters: Double) -> Double? {
        var down = meters / DriveLine.metersPerDegree, up = down
        for _ in 0..<256 {
            if probeDistance(down) == meters { return down }
            if probeDistance(up) == meters { return up }
            down = down.nextDown
            up = up.nextUp
        }
        return nil
    }

    /// The smallest latitude above `latitude(measuring: meters)` whose probe distance exceeds `meters`.
    static func latitude(above meters: Double) -> Double? {
        guard var y = latitude(measuring: meters) else { return nil }
        for _ in 0..<256 {
            y = y.nextUp
            if probeDistance(y) > meters { return y }
        }
        return nil
    }
}
