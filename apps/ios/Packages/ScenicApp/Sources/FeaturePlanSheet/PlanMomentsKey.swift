import ScenicKit
import SwiftUI

/// Where the plan sheet's moments go (T-0361 R1/R2). The shell sets it from PlanAdapter, so this feature never
/// imports the telemetry client; unset, a moment goes nowhere.
struct PlanMomentsKey: EnvironmentKey {
    static let defaultValue: (any AppMomentReporting)? = nil
}

extension EnvironmentValues {
    public var planMoments: (any AppMomentReporting)? {
        get { self[PlanMomentsKey.self] }
        set { self[PlanMomentsKey.self] = newValue }
    }
}
