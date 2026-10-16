import ScenicKit
import SwiftUI

/// Where the drive screen's post-drive answer goes (T-0358 R7). The shell sets it from PlanAdapter, so this feature
/// never imports the telemetry client; unset, an answer goes nowhere.
struct PostDriveAnswersKey: EnvironmentKey {
    static let defaultValue: (any PostDriveAnswering)? = nil
}

extension EnvironmentValues {
    public var postDriveAnswers: (any PostDriveAnswering)? {
        get { self[PostDriveAnswersKey.self] }
        set { self[PostDriveAnswersKey.self] = newValue }
    }
}
