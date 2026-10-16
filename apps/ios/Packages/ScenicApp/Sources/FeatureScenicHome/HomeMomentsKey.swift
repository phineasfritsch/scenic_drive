import ScenicKit
import SwiftUI

/// Where the home's moments go - its drive and the Surprise's place handed to Apple Maps (T-0361 R1/R3/R4). The
/// shell sets it from PlanAdapter, so this feature never imports the telemetry client; unset, a moment goes nowhere.
struct HomeMomentsKey: EnvironmentKey {
    static let defaultValue: (any AppMomentReporting)? = nil
}

extension EnvironmentValues {
    public var homeMoments: (any AppMomentReporting)? {
        get { self[HomeMomentsKey.self] }
        set { self[HomeMomentsKey.self] = newValue }
    }
}
