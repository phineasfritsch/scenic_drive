import ScenicKit
import SwiftUI

/// Where the drive's start and end go (T-0361 R1/R6). The shell sets it from PlanAdapter, so this module never
/// imports the telemetry client; unset, a moment goes nowhere.
struct DriveMomentsKey: EnvironmentKey {
    static let defaultValue: (any AppMomentReporting)? = nil
}

extension EnvironmentValues {
    public var driveMoments: (any AppMomentReporting)? {
        get { self[DriveMomentsKey.self] }
        set { self[DriveMomentsKey.self] = newValue }
    }
}
