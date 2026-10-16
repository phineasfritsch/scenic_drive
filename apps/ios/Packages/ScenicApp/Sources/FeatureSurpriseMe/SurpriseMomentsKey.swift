import ScenicKit
import SwiftUI

/// Where the Surprise card's "not this" goes (T-0361 R1/R5). The shell sets it from PlanAdapter, so this feature
/// never imports the telemetry client; unset, a moment goes nowhere.
struct SurpriseMomentsKey: EnvironmentKey {
    static let defaultValue: (any AppMomentReporting)? = nil
}

extension EnvironmentValues {
    public var surpriseMoments: (any AppMomentReporting)? {
        get { self[SurpriseMomentsKey.self] }
        set { self[SurpriseMomentsKey.self] = newValue }
    }
}
