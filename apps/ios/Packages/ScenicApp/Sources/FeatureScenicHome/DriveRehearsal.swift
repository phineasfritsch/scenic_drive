import Foundation
import ScenicKit

/// The drive the app opens on in a DEBUG build launched with `-screen drive` - ios-screenshot's drive shot (T-0324
/// R6) - and in every release build, none. The `-screen` pair lands in UserDefaults' argument domain, read here and
/// written nowhere (LaunchScreen's pattern); `LaunchScreen(rawValue: "drive")` is nil, so Settings stays closed.
/// It lives here because the shell may carry no `#` directive (ops/lib/check-safety-disclaimer-frozen).
public enum DriveRehearsal {
    /// A short planned line along Mulholland Highway in the Santa Monica Mountains. The workflow's simulated
    /// location (`simctl location start`) moves along these same four points, so the fixes are on the line.
    static let line = [
        Coordinate(latitude: 34.0905, longitude: -118.6370),
        Coordinate(latitude: 34.0880, longitude: -118.6250),
        Coordinate(latitude: 34.0855, longitude: -118.6150),
        Coordinate(latitude: 34.0830, longitude: -118.6050),
    ]

    /// The preview to drive at launch, or nil: always nil outside DEBUG.
    public static var atLaunch: PlanPreview? {
        #if DEBUG
        guard UserDefaults.standard.string(forKey: "screen") == "drive" else { return nil }
        return PlanPreview(route: line, etaSeconds: 1_500, fastestEtaSeconds: 1_200, etaIsEstimate: true,
                           hazards: [], waypoints: [], lambda: 0.5)
        #else
        return nil
        #endif
    }
}
