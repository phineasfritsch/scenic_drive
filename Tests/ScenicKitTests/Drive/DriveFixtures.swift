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
        exact(meters, near: meters / DriveLine.metersPerDegree, probeDistance)
    }

    /// The smallest latitude above `latitude(measuring: meters)` whose probe distance exceeds `meters`.
    static func latitude(above meters: Double) -> Double? {
        latitude(measuring: meters).flatMap { above(meters, from: $0, probeDistance) }
    }

    /// The NORTH-SOUTH probe (rv1-t0317 R2): one segment north along longitude 0 from latitude 34, where a metre
    /// east is cos(34 deg) of a metre north in degrees. A fix at (34, longitude) projects onto the segment's start.
    static let northStart = Coordinate(latitude: 34, longitude: 0)
    static let northEnd = Coordinate(latitude: 34.01, longitude: 0)

    static func eastDistance(_ longitude: Double) -> Double {
        DriveLine([northStart, northEnd])!.distanceMeters(from: Coordinate(latitude: 34, longitude: longitude))
    }

    /// Degrees of longitude per metre east at latitude 34, computed here and NOT by DriveLine.
    static let eastDegreesPerMeter = 1 / (cos(34 * Double.pi / 180) * Geo.earthRadiusMeters * Double.pi / 180)

    /// A longitude whose east distance is EXACTLY `meters`, searched next to the independent guess.
    static func longitude(measuring meters: Double) -> Double? {
        exact(meters, near: meters * eastDegreesPerMeter, eastDistance)
    }

    static func longitude(above meters: Double) -> Double? {
        longitude(measuring: meters).flatMap { above(meters, from: $0, eastDistance) }
    }

    private static func exact(_ meters: Double, near guess: Double, _ measure: (Double) -> Double) -> Double? {
        var down = guess, up = guess
        for _ in 0..<256 {
            if measure(down) == meters { return down }
            if measure(up) == meters { return up }
            down = down.nextDown
            up = up.nextUp
        }
        return nil
    }

    private static func above(_ meters: Double, from start: Double, _ measure: (Double) -> Double) -> Double? {
        var y = start
        for _ in 0..<256 {
            y = y.nextUp
            if measure(y) > meters { return y }
        }
        return nil
    }
}
