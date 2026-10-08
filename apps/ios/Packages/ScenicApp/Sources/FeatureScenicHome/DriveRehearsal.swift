import Foundation
import ScenicKit

/// The drive the app opens on in a DEBUG build launched with `-screen drive` - ios-screenshot's drive shot (T-0324
/// R6) - and in every release build, none. The `-screen` pair lands in UserDefaults' argument domain, read here and
/// written nowhere (LaunchScreen's pattern); `LaunchScreen(rawValue: "drive")` is nil, so Settings stays closed.
/// It lives here because the shell may carry no `#` directive (ops/lib/check-safety-disclaimer-frozen).
///
/// T-0328 R8: the rehearsal REROUTES. Its planned line runs 0.003 deg north of the road the simulated location drives,
/// so the fixes are off-route after DriveSession's 5 s dwell; the rehearsal is then its own reroute sender and answers
/// at once with the road itself, which the drive map draws in place of the planned line.
public struct DriveRehearsal: RerouteSending {
    /// A short stretch of Mulholland Highway in the Santa Monica Mountains. The workflow's simulated location
    /// (`simctl location start`) moves along these same four points, so the fixes are on THIS line.
    static let line = [
        Coordinate(latitude: 34.0905, longitude: -118.6370),
        Coordinate(latitude: 34.0880, longitude: -118.6250),
        Coordinate(latitude: 34.0855, longitude: -118.6150),
        Coordinate(latitude: 34.0830, longitude: -118.6050),
    ]

    /// The rehearsal's planned line: the road shifted 0.003 deg north (~333 m, beyond the 50 m threshold).
    static let planned = line.map { Coordinate(latitude: $0.latitude + 0.003, longitude: $0.longitude) }

    /// The preview to drive at launch, or nil: always nil outside DEBUG.
    public static var atLaunch: PlanPreview? {
        #if DEBUG
        guard UserDefaults.standard.string(forKey: "screen") == "drive" else { return nil }
        return PlanPreview(route: planned, etaSeconds: 1_500, fastestEtaSeconds: 1_200, etaIsEstimate: true,
                           hazards: [], waypoints: [], lambda: 0.5)
        #else
        return nil
        #endif
    }

    /// The rehearsal's own reroute sender while it is driven, or nil: always nil outside DEBUG.
    public static var rerouter: (any RerouteSending)? {
        #if DEBUG
        guard UserDefaults.standard.string(forKey: "screen") == "drive" else { return nil }
        return DriveRehearsal()
        #else
        return nil
        #endif
    }

    /// The road the simulated location drives, with no pins: the line DriveSession takes and the map draws.
    public func reroute(_ request: RerouteRequest) async throws -> RerouteReply {
        RerouteReply(line: Self.line, waypoints: [])
    }
}
